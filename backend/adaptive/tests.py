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

    def test_calculate_access_ready_via_support_and_preferences(self):
        self.task.access_requirements = ['screen_reader', 'quiet_room']
        self.task.project.workspace.access_support = ['quiet_room']
        profile = WorkProfile(access_preferences=['screen_reader'])
        res = AdaptiveEngine.calculate_access(self.task, profile)
        self.assertEqual(res['readiness'], 'READY')
        self.assertEqual(res['score'], 2.0)
        self.assertEqual(res['matched_preferences'], ['screen_reader'])
        self.assertEqual(res['workplace_support'], ['quiet_room'])
        self.assertEqual(res['unmet_preferences'], [])

    def test_calculate_access_needs_support(self):
        self.task.access_requirements = ['screen_reader', 'quiet_room']
        self.task.project.workspace.access_support = ['quiet_room']
        profile = WorkProfile(access_preferences=[])
        res = AdaptiveEngine.calculate_access(self.task, profile)
        self.assertEqual(res['readiness'], 'NEEDS_SUPPORT')
        self.assertEqual(res['score'], 1.0)
        self.assertEqual(res['unmet_preferences'], ['screen_reader'])

    def test_calculate_access_unresolved(self):
        self.task.access_requirements = ['braille_display']
        self.task.project.workspace.access_support = []
        profile = WorkProfile(access_preferences=[])
        res = AdaptiveEngine.calculate_access(self.task, profile)
        self.assertEqual(res['readiness'], 'UNRESOLVED')
        self.assertEqual(res['score'], 0.0)
        self.assertEqual(res['unmet_preferences'], ['braille_display'])

    def test_task_load_formula_matrix(self):
        # 1. Completed task is always 0.0
        completed = Task(status=TaskStatus.COMPLETED, estimated_effort=20, complexity='HIGH', progress=0)
        self.assertEqual(task_load(completed), 0.0)

        # 2. No deadline -> deadline_factor = 1.0
        t_no_deadline = Task(status=TaskStatus.PENDING, estimated_effort=10, complexity='MEDIUM', progress=0)
        self.assertEqual(task_load(t_no_deadline), 10.0)

        # 3. Complexity factors: LOW=0.8, MEDIUM=1.0, HIGH=1.3 with normal deadline (>7 days -> 1.0)
        t_low = Task(status=TaskStatus.PENDING, estimated_effort=10, complexity='LOW', progress=0,
                     deadline=date.today() + timedelta(days=14))
        t_med = Task(status=TaskStatus.PENDING, estimated_effort=10, complexity='MEDIUM', progress=0,
                     deadline=date.today() + timedelta(days=14))
        t_high = Task(status=TaskStatus.PENDING, estimated_effort=10, complexity='HIGH', progress=0,
                      deadline=date.today() + timedelta(days=14))
        self.assertEqual(task_load(t_low), 8.0)
        self.assertEqual(task_load(t_med), 10.0)
        self.assertEqual(task_load(t_high), 13.0)

        # 4. Deadline factors: <3 days -> 1.5, <=7 days -> 1.2, >7 days -> 1.0
        t_urgent = Task(status=TaskStatus.PENDING, estimated_effort=10, complexity='MEDIUM', progress=0,
                        deadline=date.today() + timedelta(days=2))
        t_week = Task(status=TaskStatus.PENDING, estimated_effort=10, complexity='MEDIUM', progress=0,
                      deadline=date.today() + timedelta(days=7))
        self.assertEqual(task_load(t_urgent), 15.0)
        self.assertEqual(task_load(t_week), 12.0)

        # 5. Progress factor: (1 - progress / 100)
        t_half = Task(status=TaskStatus.IN_PROGRESS, estimated_effort=10, complexity='HIGH', progress=50,
                      deadline=date.today() + timedelta(days=2))
        # 10 * 0.5 * 1.3 * 1.5 = 9.75
        self.assertEqual(task_load(t_half), 9.75)

        t_almost_done = Task(status=TaskStatus.IN_PROGRESS, estimated_effort=10, complexity='MEDIUM', progress=90,
                             deadline=date.today() + timedelta(days=2))
        # 10 * 0.1 * 1.0 * 1.5 = 1.5
        self.assertEqual(task_load(t_almost_done), 1.5)

    def test_calculate_capacity_signals_and_thresholds(self):
        # Fresh member with AVAILABLE signal
        member = Member.objects.create(team=self.team, name='CapacityTester', email='captester@example.com')
        CapacitySignal.objects.create(member=member, level='AVAILABLE')

        # 1. AVAILABLE fit: projected < 15 hours
        eval_task = Task.objects.create(project=self.project, title='Eval 1', estimated_effort=10,
                                        complexity='MEDIUM', progress=0,
                                        deadline=date.today() + timedelta(days=14))
        cap = AdaptiveEngine.calculate_capacity(member, eval_task)
        self.assertEqual(cap['fit'], 'AVAILABLE')
        self.assertEqual(cap['score'], 2.0)
        self.assertEqual(cap['current_hours'], 0.0)
        self.assertEqual(cap['projected_hours'], 10.0)

        # 2. BALANCED fit: 15 <= projected < 30 hours
        t_active1 = Task.objects.create(project=self.project, title='Active 1', estimated_effort=10,
                                        complexity='MEDIUM', progress=0,
                                        deadline=date.today() + timedelta(days=14))
        Assignment.objects.create(task=t_active1, member=member, reason='work')
        cap = AdaptiveEngine.calculate_capacity(member, eval_task)
        self.assertEqual(cap['fit'], 'BALANCED')
        self.assertEqual(cap['score'], 1.5)
        self.assertEqual(cap['current_hours'], 10.0)
        self.assertEqual(cap['projected_hours'], 20.0)

        # 3. NEAR_CAPACITY fit: 30 <= projected < 40 hours
        t_active2 = Task.objects.create(project=self.project, title='Active 2', estimated_effort=12,
                                        complexity='MEDIUM', progress=0,
                                        deadline=date.today() + timedelta(days=14))
        Assignment.objects.create(task=t_active2, member=member, reason='work')
        cap = AdaptiveEngine.calculate_capacity(member, eval_task)
        self.assertEqual(cap['fit'], 'NEAR_CAPACITY')
        self.assertEqual(cap['score'], 0.8)
        self.assertEqual(cap['current_hours'], 22.0)
        self.assertEqual(cap['projected_hours'], 32.0)

        # 4. OVER_CAPACITY fit: projected >= 40 hours
        t_active3 = Task.objects.create(project=self.project, title='Active 3', estimated_effort=10,
                                        complexity='MEDIUM', progress=0,
                                        deadline=date.today() + timedelta(days=14))
        Assignment.objects.create(task=t_active3, member=member, reason='work')
        cap = AdaptiveEngine.calculate_capacity(member, eval_task)
        self.assertEqual(cap['fit'], 'OVER_CAPACITY')
        self.assertEqual(cap['score'], 0.0)
        self.assertEqual(cap['current_hours'], 32.0)
        self.assertEqual(cap['projected_hours'], 42.0)

        # 5. Signal Floor: Self-reported OVER_CAPACITY is capped at NEAR_CAPACITY floor
        # Clear assignments so system_fit is AVAILABLE (projected=10.0)
        member.assignments.all().delete()
        CapacitySignal.objects.create(member=member, level='OVER_CAPACITY')
        cap = AdaptiveEngine.calculate_capacity(member, eval_task)
        self.assertEqual(cap['fit'], 'NEAR_CAPACITY')
        self.assertEqual(cap['score'], 0.8)
        self.assertEqual(cap['signal_level'], 'OVER_CAPACITY')

        # 6. Signal Floor: Self-reported NEAR_CAPACITY elevates AVAILABLE system_fit
        CapacitySignal.objects.create(member=member, level='NEAR_CAPACITY')
        cap = AdaptiveEngine.calculate_capacity(member, eval_task)
        self.assertEqual(cap['fit'], 'NEAR_CAPACITY')
        self.assertEqual(cap['score'], 0.8)

        # 7. Signal Floor: Self-reported BALANCED elevates AVAILABLE system_fit
        CapacitySignal.objects.create(member=member, level='BALANCED')
        cap = AdaptiveEngine.calculate_capacity(member, eval_task)
        self.assertEqual(cap['fit'], 'BALANCED')
        self.assertEqual(cap['score'], 1.5)
