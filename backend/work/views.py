from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction
from work.models import Project, Task, Assignment, Blocker, CompletionEvidence
from work.serializers import (
    ProjectSerializer, TaskSerializer, AssignmentSerializer,
    BlockerSerializer, CompletionEvidenceSerializer
)
from adaptive.services import AdaptiveEngine
from adaptive.evidence import propose_task_evidence, sync_task_requirements
from adaptive.serializers import AdaptiveAnalysisSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def perform_create(self, serializer):
        task = serializer.save()
        sync_task_requirements(task)
        AdaptiveEngine.refresh_team(task.project.team, 'task_created')

    def perform_update(self, serializer):
        task = serializer.save()
        if 'required_skills' in serializer.validated_data:
            sync_task_requirements(task)
        if task.status == 'COMPLETED' and hasattr(task, 'completion_evidence'):
            propose_task_evidence(task)
        AdaptiveEngine.refresh_team(task.project.team, 'task_updated')

    def perform_destroy(self, instance):
        team = instance.project.team
        instance.delete()
        AdaptiveEngine.refresh_team(team, 'task_deleted')

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Analyze task and generate assignment recommendations."""
        task = self.get_object()

        analysis = AdaptiveEngine.save_analysis(task)

        serializer = AdaptiveAnalysisSerializer(analysis)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign task to a member (human decision)."""
        task = self.get_object()
        serializer = AssignmentSerializer(data=request.data)

        if serializer.is_valid():
            if serializer.validated_data['task'] != task:
                raise ValidationError({'task': 'Must match URL task.'})
            if serializer.validated_data['member'].team_id != task.project.team_id:
                raise ValidationError({'member': 'Must belong to the task team.'})
            with transaction.atomic():
                assignment = serializer.save()
                task.status = 'IN_PROGRESS'
                task.save()
            AdaptiveEngine.refresh_team(task.project.team, 'assignment_changed')
            return Response(AssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed with evidence."""
        task = self.get_object()
        serializer = CompletionEvidenceSerializer(data=request.data)

        if serializer.is_valid():
            if serializer.validated_data['task'] != task:
                raise ValidationError({'task': 'Must match URL task.'})
            with transaction.atomic():
                evidence = serializer.save()
                task.status = 'COMPLETED'
                task.progress = 100
                task.save()
                propose_task_evidence(task)
            AdaptiveEngine.refresh_team(task.project.team, 'task_completed')
            return Response(CompletionEvidenceSerializer(evidence).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer

    def perform_create(self, serializer):
        assignment = serializer.save()
        AdaptiveEngine.refresh_team(assignment.task.project.team, 'assignment_changed')

    def perform_update(self, serializer):
        assignment = serializer.save()
        AdaptiveEngine.refresh_team(assignment.task.project.team, 'assignment_changed')

    def perform_destroy(self, instance):
        team = instance.task.project.team
        instance.delete()
        AdaptiveEngine.refresh_team(team, 'assignment_changed')


class BlockerViewSet(viewsets.ModelViewSet):
    queryset = Blocker.objects.all()
    serializer_class = BlockerSerializer

    def perform_update(self, serializer):
        blocker = serializer.save()
        AdaptiveEngine.refresh_team(blocker.task.project.team, 'blocker_changed')

    def create(self, request, *args, **kwargs):
        """Create blocker and update task status."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        blocker = serializer.save()

        # Update task status to BLOCKED
        task = blocker.task
        task.status = 'BLOCKED'
        task.save()
        AdaptiveEngine.refresh_team(task.project.team, 'blocker_reported')

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CompletionEvidenceViewSet(viewsets.ModelViewSet):
    queryset = CompletionEvidence.objects.all()
    serializer_class = CompletionEvidenceSerializer

    def perform_create(self, serializer):
        evidence = serializer.save()
        if evidence.task.status == 'COMPLETED':
            propose_task_evidence(evidence.task)
        AdaptiveEngine.refresh_team(evidence.task.project.team, 'completion_evidence')

    def perform_update(self, serializer):
        evidence = serializer.save()
        AdaptiveEngine.refresh_team(evidence.task.project.team, 'completion_evidence')
