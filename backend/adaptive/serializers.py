from rest_framework import serializers
from adaptive.models import AdaptiveAnalysis, EmployeeSkill, Skill, SkillEvidence, TaskSkillRequirement


class AdaptiveAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptiveAnalysis
        fields = ['id', 'task', 'candidates', 'recommendation', 'evidence', 'workload_impact', 'created_at']
        read_only_fields = ['id', 'created_at']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'canonical_name', 'category', 'aliases']

    def validate(self, attrs):
        raw_name = attrs.get('canonical_name', getattr(self.instance, 'canonical_name', ''))
        raw_aliases = attrs.get('aliases', getattr(self.instance, 'aliases', []))
        if not isinstance(raw_name, str) or not isinstance(raw_aliases, list) or not all(isinstance(a, str) for a in raw_aliases):
            raise serializers.ValidationError('Expected a name and a list of aliases.')
        name = raw_name.casefold().strip()
        aliases = [a.casefold().strip() for a in raw_aliases]
        if not name or len({name, *aliases}) != len(aliases) + 1:
            raise serializers.ValidationError('Canonical name and aliases must be distinct.')
        for other in Skill.objects.exclude(pk=getattr(self.instance, 'pk', None)):
            if {name, *aliases} & {other.canonical_name.casefold(), *(a.casefold() for a in other.aliases)}:
                raise serializers.ValidationError('Skill name or alias already exists.')
        attrs['canonical_name'] = name
        attrs['aliases'] = aliases
        return attrs


class EmployeeSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSkill
        fields = ['id', 'member', 'skill', 'declared_proficiency', 'observed_proficiency',
                  'evidence_confidence', 'declared_at', 'last_evidence_at']
        read_only_fields = ['observed_proficiency', 'evidence_confidence', 'declared_at', 'last_evidence_at']

    def validate_declared_proficiency(self, value):
        if value not in {'BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT'}:
            raise serializers.ValidationError('Invalid proficiency.')
        return value

    def validate(self, attrs):
        if self.instance and 'member' in attrs and attrs['member'] != self.instance.member:
            raise serializers.ValidationError('Member cannot be changed.')
        if self.instance and 'skill' in attrs and attrs['skill'] != self.instance.skill:
            raise serializers.ValidationError('Skill cannot be changed.')
        if not self.instance and EmployeeSkill.objects.filter(member=attrs['member'], skill=attrs['skill']).exists():
            raise serializers.ValidationError('Employee skill already exists.')
        return attrs


class TaskSkillRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSkillRequirement
        fields = ['id', 'task', 'skill', 'requirement_type', 'minimum_proficiency']

    def validate_requirement_type(self, value):
        if value not in {'MANDATORY', 'REQUIRED', 'PREFERRED'}:
            raise serializers.ValidationError('Invalid requirement type.')
        return value

    def validate_minimum_proficiency(self, value):
        if value not in {'BEGINNER', 'INTERMEDIATE', 'ADVANCED', 'EXPERT'}:
            raise serializers.ValidationError('Invalid proficiency.')
        return value

    def validate(self, attrs):
        if self.instance and any(attrs.get(field, getattr(self.instance, field)) != getattr(self.instance, field)
                                 for field in ('task', 'skill')):
            raise serializers.ValidationError('Task and skill cannot be changed.')
        if not self.instance and TaskSkillRequirement.objects.filter(task=attrs['task'], skill=attrs['skill']).exists():
            raise serializers.ValidationError('Task requirement already exists.')
        return attrs


class SkillEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillEvidence
        fields = ['id', 'member', 'skill', 'task', 'usage_level', 'task_complexity',
                  'context_tags', 'source', 'confirmed_by_employee', 'created_at']
        read_only_fields = fields
