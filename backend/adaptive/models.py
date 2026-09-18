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
