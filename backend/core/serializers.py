from rest_framework import serializers
from core.models import Workspace, Team, Member, WorkProfile, CapacitySignal
from adaptive.evidence import resolve_skill


class WorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'access_support', 'created_at']
        read_only_fields = ['id', 'created_at']


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'workspace', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


class WorkProfileSerializer(serializers.ModelSerializer):
    def validate_skills(self, values):
        if not isinstance(values, list):
            raise serializers.ValidationError('Expected a list of skills.')
        for value in values:
            name = value if isinstance(value, str) else value.get('skill') if isinstance(value, dict) else None
            if not isinstance(name, str) or resolve_skill(name) is None:
                raise serializers.ValidationError(f'UNRESOLVED_SKILL: {name}')
            if isinstance(value, dict) and str(value.get('level', 'INTERMEDIATE')).upper() not in {
                'BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT'
            }:
                raise serializers.ValidationError('Invalid proficiency level.')
        return values

    class Meta:
        model = WorkProfile
        fields = ['id', 'member', 'skills', 'experience', 'access_preferences', 'access_needs', 'updated_at']
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
