import uuid
from django.db import models
from core.models import Workspace, Team, Member


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='projects')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TaskStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    BLOCKED = 'BLOCKED', 'Blocked'
    COMPLETED = 'COMPLETED', 'Completed'


class TaskComplexity(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    required_skills = models.JSONField(default=list)  # list of str
    complexity = models.CharField(max_length=10, choices=TaskComplexity.choices, default=TaskComplexity.MEDIUM)
    estimated_effort = models.IntegerField(help_text='Hours')
    deadline = models.DateField(null=True, blank=True)
    access_requirements = models.JSONField(default=list)  # list of str e.g. ["Flexible Hours", "Remote"]
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='assignments')
    decided_by = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, related_name='decisions_made')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task.title} → {self.member.name}"


class BlockerType(models.TextChoices):
    TECHNICAL = 'TECHNICAL', 'Technical'
    ACCESS = 'ACCESS', 'Access'
    DEPENDENCY = 'DEPENDENCY', 'Dependency'
    RESOURCE = 'RESOURCE', 'Resource'
    OTHER = 'OTHER', 'Other'


class BlockerStatus(models.TextChoices):
    OPEN = 'OPEN', 'Open'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    RESOLVED = 'RESOLVED', 'Resolved'


class Blocker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='blockers')
    type = models.CharField(max_length=20, choices=BlockerType.choices)
    note = models.TextField()
    status = models.CharField(max_length=20, choices=BlockerStatus.choices, default=BlockerStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task.title} - {self.type}"


class CompletionEvidence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='completion_evidence')
    estimated_effort = models.IntegerField(help_text='Hours')
    actual_effort = models.IntegerField(help_text='Hours')
    factors = models.JSONField(default=list)  # list of context factors
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence for {self.task.title}"
