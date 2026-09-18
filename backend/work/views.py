from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from work.models import Project, Task, Assignment, Blocker, CompletionEvidence
from work.serializers import (
    ProjectSerializer, TaskSerializer, AssignmentSerializer,
    BlockerSerializer, CompletionEvidenceSerializer
)
from adaptive.services import AdaptiveEngine
from adaptive.models import AdaptiveAnalysis
from adaptive.serializers import AdaptiveAnalysisSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Analyze task and generate assignment recommendations."""
        task = self.get_object()

        # Run adaptive engine
        analysis_result = AdaptiveEngine.analyze_task(task)

        # Save analysis
        analysis = AdaptiveAnalysis.objects.create(
            task=task,
            candidates=analysis_result['candidates'],
            recommendation=analysis_result['recommendation'],
            evidence=analysis_result['evidence'],
            workload_impact=analysis_result['workload_impact']
        )

        serializer = AdaptiveAnalysisSerializer(analysis)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign task to a member (human decision)."""
        task = self.get_object()
        serializer = AssignmentSerializer(data=request.data)

        if serializer.is_valid():
            assignment = serializer.save()
            task.status = 'IN_PROGRESS'
            task.save()
            return Response(AssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed with evidence."""
        task = self.get_object()
        serializer = CompletionEvidenceSerializer(data=request.data)

        if serializer.is_valid():
            evidence = serializer.save()
            task.status = 'COMPLETED'
            task.save()
            return Response(CompletionEvidenceSerializer(evidence).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer


class BlockerViewSet(viewsets.ModelViewSet):
    queryset = Blocker.objects.all()
    serializer_class = BlockerSerializer

    def create(self, request, *args, **kwargs):
        """Create blocker and update task status."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        blocker = serializer.save()

        # Update task status to BLOCKED
        task = blocker.task
        task.status = 'BLOCKED'
        task.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CompletionEvidenceViewSet(viewsets.ModelViewSet):
    queryset = CompletionEvidence.objects.all()
    serializer_class = CompletionEvidenceSerializer
