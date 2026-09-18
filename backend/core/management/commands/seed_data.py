from django.core.management.base import BaseCommand
from core.models import Workspace, Team, Member, MemberRole, WorkProfile, CapacitySignal, CapacityLevel
from work.models import Project, Task, TaskComplexity, TaskStatus, Assignment
from adaptive.services import AdaptiveEngine
from adaptive.models import AdaptiveAnalysis
from adaptive.evidence import sync_profile_skills, sync_task_requirements


class Command(BaseCommand):
    help = 'Seeds database with initial data for Pantara-MindCraft demo'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Clearing old data...'))
        Workspace.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Creating Workspace & Team...'))
        workspace = Workspace.objects.create(name="Pantara Workspace")
        team = Team.objects.create(workspace=workspace, name="Engineering Team")

        # Create Members
        lead = Member.objects.create(
            team=team,
            name="Hadi Akram (Lead)",
            email="hadi@pantara.io",
            role=MemberRole.TEAM_LEAD
        )
        WorkProfile.objects.create(
            member=lead,
            skills=["Python", "Django", "System Design", "Architecture"],
            experience=[{"skill": "System Design", "years": 5}],
            access_preferences=["Flexible Hours", "Remote"]
        )
        CapacitySignal.objects.create(member=lead, level=CapacityLevel.BALANCED, context=["Managing team"])

        dev1 = Member.objects.create(
            team=team,
            name="Budi Pratama (Backend Engine)",
            email="budi@pantara.io",
            role=MemberRole.EMPLOYEE
        )
        WorkProfile.objects.create(
            member=dev1,
            skills=["Python", "Django", "REST API", "Algorithm", "PostgreSQL"],
            experience=[{"skill": "Python", "years": 4}, {"skill": "Algorithm", "years": 3}],
            access_preferences=["Remote", "Flexible Hours"]
        )
        CapacitySignal.objects.create(member=dev1, level=CapacityLevel.AVAILABLE, context=["Ready for core engine work"])

        dev2 = Member.objects.create(
            team=team,
            name="Siti Rahma (Frontend Lead)",
            email="siti@pantara.io",
            role=MemberRole.EMPLOYEE
        )
        WorkProfile.objects.create(
            member=dev2,
            skills=["React", "TypeScript", "Tailwind", "UI/UX"],
            experience=[{"skill": "React", "years": 3}, {"skill": "UI/UX", "years": 2}],
            access_preferences=["Remote", "Screen Reader"]
        )
        CapacitySignal.objects.create(member=dev2, level=CapacityLevel.BALANCED, context=["Working on design system"])

        dev3 = Member.objects.create(
            team=team,
            name="Dewi Sartika (Fullstack)",
            email="dewi@pantara.io",
            role=MemberRole.EMPLOYEE
        )
        WorkProfile.objects.create(
            member=dev3,
            skills=["Python", "React", "Django", "PostgreSQL"],
            experience=[{"skill": "Python", "years": 2}],
            access_preferences=["Flexible Hours"]
        )
        CapacitySignal.objects.create(member=dev3, level=CapacityLevel.OVER_CAPACITY, context=["Handling legacy bugfixes"])

        # Project
        project = Project.objects.create(
            workspace=workspace,
            team=team,
            name="Pantara-MindCraft Platform MVP"
        )

        # Active tasks for Dewi to simulate OVER_CAPACITY workload
        task_active1 = Task.objects.create(
            project=project,
            title="Legacy Maintenance & Patching",
            description="Fix legacy authentication bug",
            required_skills=["Python"],
            complexity=TaskComplexity.HIGH,
            estimated_effort=35,
            status=TaskStatus.IN_PROGRESS
        )
        Assignment.objects.create(
            task=task_active1,
            member=dev3,
            decided_by=lead,
            reason="Assigned for urgency"
        )

        # Main Demo Tasks
        task1 = Task.objects.create(
            project=project,
            title="Implement Adaptive Workload Engine",
            description="Build deterministic algorithm for capability, capacity, and access matching",
            required_skills=["Python", "Django", "Algorithm"],
            complexity=TaskComplexity.HIGH,
            estimated_effort=12,
            access_requirements=["Remote", "Flexible Hours"],
            status=TaskStatus.PENDING
        )

        task2 = Task.objects.create(
            project=project,
            title="Design Accessible Team Workload View",
            description="Build responsive & WCAG compliant dashboard UI",
            required_skills=["React", "UI/UX", "Tailwind"],
            complexity=TaskComplexity.MEDIUM,
            estimated_effort=8,
            access_requirements=["Remote", "Screen Reader"],
            status=TaskStatus.PENDING
        )

        # Run adaptive analysis on task1
        for profile in WorkProfile.objects.filter(member__team=team):
            sync_profile_skills(profile)
        for task in Task.objects.filter(project=project):
            sync_task_requirements(task)
        analysis_result = AdaptiveEngine.analyze_task(task1)
        AdaptiveAnalysis.objects.create(
            task=task1,
            candidates=analysis_result['candidates'],
            recommendation=analysis_result['recommendation'],
            evidence=analysis_result['evidence'],
            workload_impact=analysis_result['workload_impact']
        )

        self.stdout.write(self.style.SUCCESS('Data seeding successfully completed!'))
