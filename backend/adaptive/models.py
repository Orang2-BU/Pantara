import uuid
from django.db import models
from work.models import Task
from core.models import Member


class CapabilityFit(models.TextChoices):
    STRONG = 'STRONG', 'Strong'
    PARTIAL = 'PARTIAL', 'Partial'
    LIMITED = 'LIMITED', 'Limited'


class CapacityFit(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    BALANCED = 'BALANCED', 'Balanced'
    NEAR_CAPACITY = 'NEAR_CAPACITY', 'Near Capacity'
    OVER_CAPACITY = 'OVER_CAPACITY', 'Over Capacity'


class AccessReadiness(models.TextChoices):
    READY = 'READY', 'Ready'
    NEEDS_SUPPORT = 'NEEDS_SUPPORT', 'Needs Support'
    UNRESOLVED = 'UNRESOLVED', 'Unresolved'


class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    canonical_name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)
    aliases = models.JSONField(default=list)

    def __str__(self):
        return self.canonical_name


class EmployeeSkill(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='employee_skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    declared_proficiency = models.CharField(max_length=20, default='INTERMEDIATE')
    observed_proficiency = models.CharField(max_length=20, default='UNKNOWN')
    evidence_confidence = models.CharField(max_length=10, default='LOW')
    declared_at = models.DateTimeField(auto_now_add=True)
    last_evidence_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['member', 'skill'], name='unique_employee_skill')]


class TaskSkillRequirement(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='skill_requirements')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    requirement_type = models.CharField(max_length=12, default='REQUIRED')
    minimum_proficiency = models.CharField(max_length=20, default='INTERMEDIATE')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['task', 'skill'], name='unique_task_skill')]


class SkillEvidence(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='skill_evidence')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    usage_level = models.CharField(max_length=12, default='PRIMARY')
    task_complexity = models.CharField(max_length=10)
    context_tags = models.JSONField(default=list)
    source = models.CharField(max_length=30, default='TASK_COMPLETION')
    confirmed_by_employee = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['member', 'skill', 'task'], name='unique_skill_evidence')]


class AdaptiveAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='analyses')
    candidates = models.JSONField(default=list)  # list of candidate dicts with scores
    recommendation = models.JSONField(default=dict)  # recommended candidate with reason
    evidence = models.JSONField(default=dict)  # evidence per dimension
    workload_impact = models.JSONField(default=dict)  # before/after workload
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.task.title}"

    class Meta:
        ordering = ['-created_at']
