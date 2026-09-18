from rest_framework import serializers
from work.models import Project, Task, Assignment, Blocker, CompletionEvidence
from adaptive.evidence import resolve_skill


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'workspace', 'team', 'name', 'deadline', 'created_at']
        read_only_fields = ['id', 'created_at']


class TaskSerializer(serializers.ModelSerializer):
    def validate_required_skills(self, values):
        if not isinstance(values, list):
            raise serializers.ValidationError('Expected a list of requirements.')
        for value in values:
            name = value if isinstance(value, str) else value.get('skill') if isinstance(value, dict) else None
            if not isinstance(name, str) or resolve_skill(name) is None:
                raise serializers.ValidationError(f'UNRESOLVED_SKILL: {name}')
            if isinstance(value, dict) and (
                str(value.get('priority', 'REQUIRED')).upper() not in {'MANDATORY', 'REQUIRED', 'PREFERRED'}
                or str(value.get('min_level', 'INTERMEDIATE')).upper() not in {
                    'BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT'
                }
            ):
                raise serializers.ValidationError('Invalid priority or minimum proficiency.')
        return values

    class Meta:
        model = Task
        fields = [
            'id', 'project', 'title', 'description', 'category', 'tags', 'required_skills',
            'complexity', 'estimated_effort', 'progress', 'deadline', 'access_requirements',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_progress(self, value):
        if value > 100:
            raise serializers.ValidationError('Progress must be between 0 and 100.')
        return value


class AssignmentSerializer(serializers.ModelSerializer):
    member_name = serializers.CharField(source='member.name', read_only=True)
    decided_by_name = serializers.CharField(source='decided_by.name', read_only=True)

    class Meta:
        model = Assignment
        fields = ['id', 'task', 'member', 'member_name', 'decided_by', 'decided_by_name', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']


class BlockerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blocker
        fields = ['id', 'task', 'type', 'note', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CompletionEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompletionEvidence
        fields = ['id', 'task', 'estimated_effort', 'actual_effort', 'factors', 'created_at']
        read_only_fields = ['id', 'created_at']
