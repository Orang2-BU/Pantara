from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from adaptive.evidence import confirm_evidence, reflect_profile_skills, reflect_task_requirements
from adaptive.models import AdaptiveAnalysis, EmployeeSkill, Skill, SkillEvidence, TaskSkillRequirement
from adaptive.serializers import (AdaptiveAnalysisSerializer, EmployeeSkillSerializer,
                                  SkillSerializer, SkillEvidenceSerializer, TaskSkillRequirementSerializer)
from adaptive.services import AdaptiveEngine


class AdaptiveAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AdaptiveAnalysis.objects.all()
    serializer_class = AdaptiveAnalysisSerializer


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAdminUser]


class EmployeeSkillViewSet(viewsets.ModelViewSet):
    queryset = EmployeeSkill.objects.all()
    serializer_class = EmployeeSkillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset if self.request.user.is_staff else queryset.filter(member__user=self.request.user)

    def _check_owner(self, member):
        if not self.request.user.is_staff and member.user_id != self.request.user.pk:
            raise PermissionDenied('Only this member can declare their skill.')

    def perform_create(self, serializer):
        member = serializer.validated_data['member']
        self._check_owner(member)
        serializer.save()
        reflect_profile_skills(member)
        AdaptiveEngine.refresh_team(member.team, 'capability_changed')

    def perform_update(self, serializer):
        self._check_owner(serializer.instance.member)
        skill = serializer.save()
        reflect_profile_skills(skill.member)
        AdaptiveEngine.refresh_team(skill.member.team, 'capability_changed')

    def perform_destroy(self, instance):
        self._check_owner(instance.member)
        team = instance.member.team
        instance.delete()
        reflect_profile_skills(instance.member)
        AdaptiveEngine.refresh_team(team, 'capability_changed')


class TaskSkillRequirementViewSet(viewsets.ModelViewSet):
    queryset = TaskSkillRequirement.objects.all()
    serializer_class = TaskSkillRequirementSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        requirement = serializer.save()
        reflect_task_requirements(requirement.task)
        AdaptiveEngine.refresh_team(requirement.task.project.team, 'requirements_changed')

    def perform_update(self, serializer):
        requirement = serializer.save()
        reflect_task_requirements(requirement.task)
        AdaptiveEngine.refresh_team(requirement.task.project.team, 'requirements_changed')

    def perform_destroy(self, instance):
        task = instance.task
        instance.delete()
        reflect_task_requirements(task)
        AdaptiveEngine.refresh_team(task.project.team, 'requirements_changed')


class SkillEvidenceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SkillEvidence.objects.all()
    serializer_class = SkillEvidenceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset if self.request.user.is_staff else queryset.filter(member__user=self.request.user)

    @action(detail=True, methods=['patch'])
    def review(self, request, pk=None):
        evidence = self.get_object()
        if evidence.member.user_id != request.user.pk:
            raise PermissionDenied('Only the assigned employee can review this evidence.')
        if evidence.confirmed_by_employee:
            raise PermissionDenied('Confirmed evidence cannot be edited.')
        usage = request.data.get('usage_level', evidence.usage_level)
        if usage not in {'PRIMARY', 'SUPPORTING', 'MINOR'}:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'usage_level': 'Invalid usage level.'})
        tags = request.data.get('context_tags', evidence.context_tags)
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'context_tags': 'Expected a list of strings.'})
        evidence.usage_level = usage
        evidence.context_tags = tags
        evidence.save(update_fields=['usage_level', 'context_tags'])
        return Response(self.get_serializer(evidence).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        evidence = self.get_object()
        if evidence.member.user_id != request.user.pk:
            raise PermissionDenied('Only the assigned employee can confirm this evidence.')
        confirm_evidence(evidence)
        AdaptiveEngine.refresh_team(evidence.member.team, 'skill_evidence_confirmed')
        return Response(self.get_serializer(evidence).data)
