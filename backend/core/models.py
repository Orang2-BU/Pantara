import uuid
from django.db import models


class Workspace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    access_support = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class MemberRole(models.TextChoices):
    TEAM_LEAD = 'TEAM_LEAD', 'Team Lead'
    EMPLOYEE = 'EMPLOYEE', 'Employee'
    ADMIN = 'ADMIN', 'Admin'


class Member(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=MemberRole.choices, default=MemberRole.EMPLOYEE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.role})"

    @property
    def latest_capacity_signal(self):
        signal = self.capacity_signals.order_by('-created_at', '-id').first()
        return signal.level if signal else CapacityLevel.BALANCED


class WorkProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='work_profile')
    skills = models.JSONField(default=list)  # list of str e.g. ["Python", "Django"]
    experience = models.JSONField(default=list)  # list of dicts e.g. [{"skill": "Python", "level": "Strong"}]
    access_preferences = models.JSONField(default=list)  # list of str e.g. ["Flexible Hours", "Screen Reader"]
    access_needs = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.member.name}"


class CapacityLevel(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Available'
    BALANCED = 'BALANCED', 'Balanced'
    NEAR_CAPACITY = 'NEAR_CAPACITY', 'Near Capacity'
    OVER_CAPACITY = 'OVER_CAPACITY', 'Over Capacity'


class CapacitySignal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='capacity_signals')
    level = models.CharField(max_length=20, choices=CapacityLevel.choices, default=CapacityLevel.BALANCED)
    context = models.JSONField(default=list)  # list of context tags/notes
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.name} - {self.level}"
