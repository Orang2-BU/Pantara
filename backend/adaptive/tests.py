from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from adaptive.services import AdaptiveEngine, task_load
from core.models import CapacitySignal, Member, Team, WorkProfile, Workspace
from work.models import Assignment, CompletionEvidence, Project, Task, TaskStatus


class AdaptiveEngineTests(TestCase):
    def setUp(self):
        self.workspace = Workspace.objects.create(name='Demo', access_support=['caption'])
        self.team = Team.objects.create(name='Team', workspace=self.workspace)
        self.project = Project.objects.create(name='Project', workspace=self.workspace, team=self.team)
        self.task = Task.objects.create(project=self.project, title='React task',
                                        required_skills=['React', 'TypeScript'],
                                        access_requirements=['caption'], estimated_effort=8)
        self.strong = Member.objects.create(team=self.team, name='Strong', email='strong@example.com')
        self.available = Member.objects.create(team=self.team, name='Available', email='available@example.com')
        self.unskilled = Member.objects.create(team=self.team, name='Unskilled', email='unskilled@example.com')
        WorkProfile.objects.create(member=self.strong, skills=['React', 'TypeScript'])
        WorkProfile.objects.create(member=self.available, skills=['React'])
        WorkProfile.objects.create(member=self.unskilled, skills=['Python'])
        CapacitySignal.objects.create(member=self.strong, level='NEAR_CAPACITY')
        CapacitySignal.objects.create(member=self.available, level='AVAILABLE')
        CapacitySignal.objects.create(member=self.unskilled, level='AVAILABLE')

    def test_policy_ranks_sustainable_viable_candidate(self):
        result = AdaptiveEngine.analyze_task(self.task)
        self.assertEqual(result['recommendation']['recommended_member_id'], str(self.available.id))
        self.assertFalse(next(c for c in result['candidates'] if c['member_id'] == str(self.unskilled.id))['is_eligible'])
        self.assertEqual(result['candidates'][0]['access']['readiness'], 'READY')

    def test_capacity_uses_progress_complexity_deadline_and_history(self):
        old = Task.objects.create(project=self.project, title='Old React', required_skills=['React'],
                                  estimated_effort=20, complexity='HIGH', progress=75,
                                  deadline=date.today() + timedelta(days=2), status=TaskStatus.IN_PROGRESS)
        Assignment.objects.create(task=old, member=self.available, reason='demo')
        self.assertEqual(task_load(old), 9.75)
        old.status = TaskStatus.COMPLETED
        old.save()
        CompletionEvidence.objects.create(task=old, estimated_effort=20, actual_effort=22)
        result = AdaptiveEngine.analyze_task(self.task)
        candidate = next(c for c in result['candidates'] if c['member_id'] == str(self.available.id))
        self.assertEqual(candidate['capability']['similar_completed_tasks'], 1)
        self.assertEqual(candidate['capacity']['current_hours'], 0)

    def test_signal_reanalysis_changes_recommendation(self):
        first = AdaptiveEngine.save_analysis(self.task)
        self.assertEqual(first.recommendation['recommended_member_id'], str(self.available.id))
        response = APIClient().post(f'/api/members/{self.available.id}/capacity/',
                                    {'level': 'OVER_CAPACITY', 'context': []}, format='json')
        self.assertEqual(response.status_code, 200)
        latest = self.task.analyses.first()
        self.assertEqual(latest.recommendation['recommended_member_id'], str(self.strong.id))
        self.assertTrue(latest.recommendation['changed_from_previous'])
        self.assertEqual(latest.recommendation['trigger'], 'capacity_signal_changed')
        self.assertEqual(latest.recommendation['intervention'], 'REVIEW_REDISTRIBUTION')
        self.assertEqual(Assignment.objects.count(), 0)
        candidate = next(c for c in latest.candidates if c['member_id'] == str(self.available.id))
        self.assertGreater(candidate['capacity']['score'], 0)

    def test_unresolved_access_is_review_not_incapability(self):
        self.task.access_requirements = ['accessible office']
        self.task.save()
        result = AdaptiveEngine.analyze_task(self.task)
        self.assertNotIn('recommended_member_id', result['recommendation'])
        self.assertEqual(result['candidates'][0]['access']['readiness'], 'UNRESOLVED')
        strong = next(c for c in result['candidates'] if c['member_id'] == str(self.strong.id))
        self.assertEqual(strong['capability']['fit'], 'STRONG')

    def test_blocker_creates_review_snapshot(self):
        AdaptiveEngine.save_analysis(self.task)
        response = APIClient().post('/api/blockers/', {
            'task': str(self.task.id), 'type': 'DEPENDENCY', 'note': 'Waiting for API'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        latest = self.task.analyses.first()
        self.assertEqual(latest.evidence['open_blockers'], ['DEPENDENCY'])
        self.assertEqual(latest.recommendation['intervention'], 'REVIEW_REDISTRIBUTION')
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.BLOCKED)
