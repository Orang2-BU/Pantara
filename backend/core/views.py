from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Workspace, Team, Member, WorkProfile, CapacitySignal
from core.serializers import (
    WorkspaceSerializer, TeamSerializer, MemberSerializer,
    WorkProfileSerializer, CapacitySignalSerializer
)


class WorkspaceViewSet(viewsets.ModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

    @action(detail=True, methods=['post'])
    def capacity(self, request, pk=None):
        """Update member capacity signal."""
        member = self.get_object()
        serializer = CapacitySignalSerializer(data={**request.data, 'member': member.id})

        if serializer.is_valid():
            signal = serializer.save()
            return Response(CapacitySignalSerializer(signal).data)

        return Response(serializer.errors, status=400)


class WorkProfileViewSet(viewsets.ModelViewSet):
    queryset = WorkProfile.objects.all()
    serializer_class = WorkProfileSerializer


class CapacitySignalViewSet(viewsets.ModelViewSet):
    queryset = CapacitySignal.objects.all()
    serializer_class = CapacitySignalSerializer
