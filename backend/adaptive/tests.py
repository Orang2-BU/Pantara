from datetime import date, timedelta

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from adaptive.services import AdaptiveEngine, task_load
from adaptive.evidence import evaluate_evidence, resolve_skill, sync_profile_skills, sync_task_requirements
from adaptive.models import EmployeeSkill, SkillEvidence
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

        member.assignments.all().delete()
        member.capacity_signals.all().delete()
        CapacitySignal.objects.create(member=member, level='OVER_CAPACITY')
        cap = AdaptiveEngine.calculate_capacity(member, eval_task)
        self.assertEqual(cap['fit'], 'NEAR_CAPACITY')
        self.assertEqual(cap['system_fit'], 'AVAILABLE')
        self.assertEqual(cap['signal_level'], 'OVER_CAPACITY')

        member.capacity_signals.all().delete()
        CapacitySignal.objects.create(member=member, level='NEAR_CAPACITY')
        cap = AdaptiveEngine.calculate_capacity(member, eval_task)
        self.assertEqual(cap['fit'], 'NEAR_CAPACITY')

        member.capacity_signals.all().delete()
        CapacitySignal.objects.create(member=member, level='BALANCED')
        cap = AdaptiveEngine.calculate_capacity(member, eval_task)
        self.assertEqual(cap['fit'], 'BALANCED')

    def test_structured_requirements_aliases_levels_and_mandatory_gate(self):
        self.task.required_skills = [
            {'skill': 'React.js', 'priority': 'MANDATORY', 'min_level': 'ADVANCED'},
            {'skill': 'TypeScript', 'priority': 'REQUIRED', 'min_level': 'INTERMEDIATE'},
            {'skill': 'Accessibility', 'priority': 'PREFERRED', 'min_level': 'BEGINNER'},
        ]
        self.task.save()
        profile = self.strong.work_profile
        profile.skills = [
            {'skill': 'React', 'level': 'ADVANCED'},
            {'skill': 'typescript', 'level': 'INTERMEDIATE'},
        ]
        profile.save()
        result = AdaptiveEngine.calculate_capability(self.task, profile, [])
        self.assertEqual(result['fit'], 'STRONG')
        self.assertEqual(result['matched_skills'], ['react', 'typescript'])
        self.assertEqual(result['preferred_matches'], [])
        profile.skills = [{'skill': 'React', 'level': 'BEGINNER'}]
        profile.save()
        result = AdaptiveEngine.calculate_capability(self.task, profile, [])
        self.assertEqual(result['mandatory_missing'], ['react'])

    def test_access_needs_require_workspace_support(self):
        self.task.access_requirements = ['captions']
        self.task.project.workspace.access_support = []
        self.task.project.workspace.save()
        profile = self.strong.work_profile
        profile.access_needs = ['captions']
        profile.access_preferences = []
        profile.save()
        result = AdaptiveEngine.calculate_access(self.task, profile, [])
        self.assertEqual(result['readiness'], 'UNRESOLVED')
        self.task.project.workspace.access_support = ['captions']
        self.task.project.workspace.save()
        result = AdaptiveEngine.calculate_access(self.task, profile, ['captions'])
        self.assertEqual(result['readiness'], 'READY')

    def test_catalog_alias_and_unknown_skill_review(self):
        self.assertEqual(resolve_skill('React').id, resolve_skill('React.js').id)
        self.assertEqual(resolve_skill('ReactJS').id, resolve_skill('react').id)
        response = APIClient().patch(f'/api/tasks/{self.task.id}/',
                                     {'required_skills': ['UnknownFutureSkill']}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('UNRESOLVED_SKILL', str(response.data))

    def test_cold_start_and_conflicting_proficiency(self):
        self.task.required_skills = [{'skill': 'React', 'priority': 'MANDATORY', 'min_level': 'ADVANCED'}]
        self.task.save()
        sync_task_requirements(self.task)
        profile = self.strong.work_profile
        profile.skills = [{'skill': 'React', 'level': 'ADVANCED'}]
        profile.save()
        sync_profile_skills(profile)
        result = AdaptiveEngine.calculate_capability(self.task, profile, [])
        self.assertEqual(result['status'], 'ELIGIBLE')
        self.assertEqual(result['confidence'], 'LOW')
        self.assertIn('SELF_DECLARED_ONLY', result['reason_codes'])
        skill = EmployeeSkill.objects.get(member=self.strong, skill=resolve_skill('React'))
        skill.observed_proficiency = 'INTERMEDIATE'
        skill.evidence_confidence = 'HIGH'
        skill.last_evidence_at = timezone.now()
        skill.save()
        result = AdaptiveEngine.calculate_capability(self.task, profile, [])
        self.assertEqual(result['status'], 'REVIEW_REQUIRED')
        self.assertIn('MIXED_PROFICIENCY_EVIDENCE', result['reason_codes'])
        self.assertEqual(skill.declared_proficiency, 'ADVANCED')

    def test_completion_proposes_then_confirmation_updates_observation(self):
        sync_task_requirements(self.task)
        profile = self.strong.work_profile
        profile.skills = [{'skill': 'React', 'level': 'ADVANCED'}, 'TypeScript']
        profile.save()
        sync_profile_skills(profile)
        Assignment.objects.create(task=self.task, member=self.strong, reason='assigned')
        response = APIClient().post(f'/api/tasks/{self.task.id}/complete/', {
            'task': str(self.task.id), 'estimated_effort': 8, 'actual_effort': 10,
            'factors': ['dependency_delay'],
        }, format='json')
        self.assertEqual(response.status_code, 201)
        proposed = SkillEvidence.objects.get(member=self.strong, task=self.task, skill=resolve_skill('React'))
        self.assertFalse(proposed.confirmed_by_employee)
        user = get_user_model().objects.create_user(username='strong', email=self.strong.email, password='x')
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(f'/api/skill-evidence/{proposed.id}/confirm/')
        self.assertEqual(response.status_code, 200)
        proposed.refresh_from_db()
        self.assertTrue(proposed.confirmed_by_employee)
        employee_skill = EmployeeSkill.objects.get(member=self.strong, skill=proposed.skill)
        self.assertEqual(employee_skill.observed_proficiency, 'INTERMEDIATE')
        self.assertEqual(employee_skill.evidence_confidence, 'LOW')
        self.assertEqual(employee_skill.declared_proficiency, 'ADVANCED')
        self.assertEqual(employee_skill.last_evidence_at, proposed.created_at)

    def test_familiarity_uses_task_context_and_provenance(self):
        old = Task.objects.create(project=self.project, title='Checkout UI',
                                  required_skills=['React'], category='frontend', tags=['checkout', 'payment'],
                                  estimated_effort=5, status=TaskStatus.COMPLETED)
        Assignment.objects.create(task=old, member=self.strong, reason='worked')
        CompletionEvidence.objects.create(task=old, estimated_effort=5, actual_effort=7)
        self.task.category = 'frontend'
        self.task.tags = ['checkout']
        self.task.save()
        result = AdaptiveEngine.calculate_capability(self.task, self.strong.work_profile)
        self.assertEqual(result['task_familiarity']['level'], 'MODERATE')
        self.assertEqual(result['relevant_experience_result']['evidence_task_ids'], [str(old.id)])

    def test_evidence_pattern_and_employee_review_permission(self):
        skill = resolve_skill('React')
        records = []
        for index, tag in enumerate(['checkout', 'payment', 'dashboard']):
            task = Task.objects.create(project=self.project, title=f'High task {index}',
                                       estimated_effort=4, complexity='HIGH')
            records.append(SkillEvidence.objects.create(
                member=self.strong, skill=skill, task=task, task_complexity='HIGH',
                context_tags=[tag], confirmed_by_employee=index < 2,
            ))
        result = evaluate_evidence(records)
        self.assertEqual(result['observed_proficiency'], 'ADVANCED')
        self.assertEqual(result['evidence_confidence'], 'MEDIUM')
        self.assertEqual(result['evidence_count'], 2)
        self.assertEqual(result['strong_evidence_count'], 2)
        stranger = get_user_model().objects.create_user(username='stranger', email='other@example.com', password='x')
        client = APIClient()
        client.force_authenticate(user=stranger)
        self.assertEqual(client.post(f'/api/skill-evidence/{records[2].id}/confirm/').status_code, 404)
        owner = get_user_model().objects.create_user(username='owner', email=self.strong.email, password='x')
        client.force_authenticate(user=owner)
        self.assertEqual(client.patch(f'/api/skill-evidence/{records[2].id}/review/',
                                      {'usage_level': 'MINOR', 'context_tags': ['dependency_delay']},
                                      format='json').status_code, 200)
        self.assertEqual(client.post(f'/api/skill-evidence/{records[2].id}/confirm/').status_code, 200)
        self.assertEqual(EmployeeSkill.objects.get(member=self.strong, skill=skill).declared_proficiency, 'BEGINNER')

    def test_seed_data_populates_relational_capability(self):
        call_command('seed_data', verbosity=0)
        task = Task.objects.get(title='Implement Adaptive Workload Engine')
        self.assertEqual(task.skill_requirements.count(), 3)
        self.assertTrue(EmployeeSkill.objects.filter(member__name__contains='Budi').exists())
        self.assertIn('recommended_member_id', AdaptiveEngine.analyze_task(task)['recommendation'])
