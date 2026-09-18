from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Workspace, Team, Member, WorkProfile, CapacitySignal
from core.serializers import (
    WorkspaceSerializer, TeamSerializer, MemberSerializer,
    WorkProfileSerializer, CapacitySignalSerializer
)
from adaptive.services import AdaptiveEngine
from adaptive.evidence import sync_profile_skills


class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    def perform_update(self, serializer):
        workspace = serializer.save()
        for team in workspace.teams.all():
            AdaptiveEngine.refresh_team(team, 'access_support_changed')


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    def perform_create(self, serializer):
        member = serializer.save()
        AdaptiveEngine.refresh_team(member.team, 'team_changed')

    @action(detail=True, methods=['post'])
    def capacity(self, request, pk=None):
        """Update member capacity signal."""
        member = self.get_object()
        serializer = CapacitySignalSerializer(data={**request.data, 'member': member.id})

        if serializer.is_valid():
            signal = serializer.save()
            AdaptiveEngine.refresh_team(member.team, 'capacity_signal_changed')
            return Response(CapacitySignalSerializer(signal).data)

        return Response(serializer.errors, status=400)


class WorkProfileViewSet(viewsets.ModelViewSet):
    queryset = WorkProfile.objects.all()
    serializer_class = WorkProfileSerializer

    def perform_create(self, serializer):
        profile = serializer.save()
        sync_profile_skills(profile)
        AdaptiveEngine.refresh_team(profile.member.team, 'profile_changed')

    def perform_update(self, serializer):
        profile = serializer.save()
        if 'skills' in serializer.validated_data:
            sync_profile_skills(profile)
        AdaptiveEngine.refresh_team(profile.member.team, 'profile_changed')


class CapacitySignalViewSet(viewsets.ModelViewSet):
    queryset = CapacitySignal.objects.all()
    serializer_class = CapacitySignalSerializer

    def perform_create(self, serializer):
        signal = serializer.save()
        AdaptiveEngine.refresh_team(signal.member.team, 'capacity_signal_changed')

    def perform_update(self, serializer):
        signal = serializer.save()
        AdaptiveEngine.refresh_team(signal.member.team, 'capacity_signal_changed')

    def perform_destroy(self, instance):
        team = instance.member.team
        instance.delete()
        AdaptiveEngine.refresh_team(team, 'capacity_signal_changed')
