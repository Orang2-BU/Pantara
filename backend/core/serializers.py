from rest_framework import serializers
from core.models import Workspace, Team, Member, WorkProfile, CapacitySignal


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'workspace', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


class WorkProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkProfile
        fields = ['id', 'member', 'skills', 'experience', 'access_preferences', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class CapacitySignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapacitySignal
        fields = ['id', 'member', 'level', 'context', 'created_at']
        read_only_fields = ['id', 'created_at']


class MemberSerializer(serializers.ModelSerializer):
    latest_capacity_signal = serializers.CharField(read_only=True)
    work_profile = WorkProfileSerializer(read_only=True)

    class Meta:
        model = Member
        fields = ['id', 'team', 'name', 'email', 'role', 'latest_capacity_signal', 'work_profile', 'created_at']
        read_only_fields = ['id', 'created_at']
