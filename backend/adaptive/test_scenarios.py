"""Adaptive Engine comprehensive scenario testing.

Usage as standalone script:
    cd backend && python -m adaptive.test_scenarios

Usage via Django shell:
    cd backend && python manage.py shell < adaptive/test_scenarios.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# Ensure the backend directory is on sys.path when run as __main__
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
django.setup()

import json
from datetime import date, timedelta
from django.db import transaction
from django.utils import timezone

from adaptive.services import AdaptiveEngine, task_load
from adaptive.models import (
    AdaptiveAnalysis, Skill, EmployeeSkill, TaskSkillRequirement, SkillEvidence,
    CapabilityFit, CapacityFit, AccessReadiness,
)
from adaptive.policy import evaluate_candidate, select_candidate
from adaptive.evidence import (
    sync_profile_skills, sync_task_requirements, resolve_skill,
    evaluate_evidence, confirm_evidence, propose_task_evidence,
)
from core.models import (
    Workspace, Team, Member, MemberRole, WorkProfile, CapacitySignal, CapacityLevel,
)
from work.models import (
    Project, Task, TaskStatus, TaskComplexity, Assignment, CompletionEvidence, Blocker, BlockerStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_skill(canonical_name, aliases=None):
    """Return an existing skill or create a new one."""
    skill, _ = Skill.objects.get_or_create(
        canonical_name=canonical_name,
        defaults={'aliases': aliases or []},
    )
    return skill


def cleanup_team(team_name):
    try:
        team = Team.objects.get(name=team_name)
        team.delete()
    except Team.DoesNotExist:
        pass


def setup_team(name, access_support=None):
    cleanup_team(name)
    workspace = Workspace.objects.create(
        name=f"{name} Workspace",
        access_support=access_support or ['Remote', 'Screen Reader', 'Flexible Hours', 'Standing Desk'],
    )
    team = Team.objects.create(name=name, workspace=workspace)
    return workspace, team


def _ensure_skills(skills):
    for entry in skills or []:
        name = entry if isinstance(entry, str) else entry.get('skill')
        if name:
            ensure_skill(name)


def create_member(team, name, email, skills, experience=None, access_prefs=None,
                  access_needs=None, capacity_level='BALANCED', role=MemberRole.EMPLOYEE):
    _ensure_skills(skills)
    member = Member.objects.create(team=team, name=name, email=email, role=role)
    profile = WorkProfile.objects.create(
        member=member, skills=skills, experience=experience or [],
        access_preferences=access_prefs or [], access_needs=access_needs or [],
    )
    CapacitySignal.objects.create(member=member, level=capacity_level)
    sync_profile_skills(profile)
    return member


def create_project(team, workspace, name):
    return Project.objects.create(name=name, workspace=workspace, team=team)


def create_task(project, title, required_skills, complexity='MEDIUM', effort=8,
                access=None, deadline=None, status=TaskStatus.PENDING):
    task = Task.objects.create(
        project=project, title=title, required_skills=required_skills,
        complexity=complexity, estimated_effort=effort,
        access_requirements=access or [], deadline=deadline, status=status,
    )
    sync_task_requirements(task)
    return task


def fmt(value):
    """Format a value for the markdown report."""
    if isinstance(value, (CapabilityFit, CapacityFit, AccessReadiness)):
        return value.name
    if isinstance(value, (list, dict, bool)) or value is None:
        return json.dumps(value)
    return str(value)


# ---------------------------------------------------------------------------
# Scenario runners
# ---------------------------------------------------------------------------

def run_capability_scenarios():
    """Capability matching: full match, partial match, no match, case insensitivity."""
    results = []
    workspace, team = setup_team('Capability Team')
    project = create_project(team, workspace, 'Capability Project')

    ensure_skill('python', aliases=['py'])
    ensure_skill('django', aliases=[])
    ensure_skill('react', aliases=['reactjs'])

    strong = create_member(team, 'Strong Dev', 'strong@test.com',
                            ['python', 'django', 'react'], capacity_level='AVAILABLE')
    partial = create_member(team, 'Partial Dev', 'partial@test.com',
                            ['python', 'react'], capacity_level='AVAILABLE')
    unskilled = create_member(team, 'Unskilled Dev', 'unskilled@test.com',
                              ['java'], capacity_level='AVAILABLE')

    task = create_task(project, 'Full Stack Feature',
                       ['python', 'django'], effort=10)
    analysis = AdaptiveEngine.analyze_task(task)
    candidates = {c['member_id']: c for c in analysis['candidates']}

    results.append({
        'name': 'Capability Full Match',
        'description': 'Strong Dev has all required skills (python, django).',
        'expected': 'Eligible / Recommended',
        'actual': 'ELIGIBLE' if candidates[str(strong.id)]['is_eligible'] else 'NOT ELIGIBLE',
        'pass': candidates[str(strong.id)]['is_eligible'],
    })
    results.append({
        'name': 'Capability Partial Match',
        'description': 'Partial Dev has only python; django is missing but ratio >= 0.5.',
        'expected': 'Alternative (partial fit)',
        'actual': candidates[str(partial.id)]['recommendation_result']['recommendation'],
        'pass': candidates[str(partial.id)]['recommendation_result']['recommendation'] == 'ALTERNATIVE',
    })
    results.append({
        'name': 'Capability No Match',
        'description': 'Unskilled Dev only knows java; none of the required skills match.',
        'expected': 'NOT_VIABLE',
        'actual': candidates[str(unskilled.id)]['recommendation_result']['recommendation'],
        'pass': candidates[str(unskilled.id)]['recommendation_result']['recommendation'] == 'NOT_VIABLE',
    })

    # Case insensitivity: task uses lowercase, profile uses mixed/alias case
    workspace2, team2 = setup_team('Case Team')
    project2 = create_project(team2, workspace2, 'Case Project')
    ensure_skill('typescript', aliases=['ts'])
    dev = create_member(team2, 'Case Dev', 'case@test.com',
                        [{'skill': 'ReactJS', 'level': 'ADVANCED'},
                         {'skill': 'TypeScript', 'level': 'INTERMEDIATE'}],
                        capacity_level='AVAILABLE')
    task_case = create_task(project2, 'Case Task',
                            [{'skill': 'react', 'priority': 'REQUIRED', 'min_level': 'INTERMEDIATE'},
                             {'skill': 'typescript', 'priority': 'REQUIRED', 'min_level': 'INTERMEDIATE'}],
                            effort=8)
    analysis_case = AdaptiveEngine.analyze_task(task_case)
    candidate_case = analysis_case['candidates'][0]
    results.append({
        'name': 'Capability Case Insensitivity',
        'description': 'Skill matching normalizes reactjs->react and ignores case.',
        'expected': 'Eligible',
        'actual': 'ELIGIBLE' if candidate_case['is_eligible'] else 'NOT ELIGIBLE',
        'pass': candidate_case['is_eligible'],
    })

    return {
        'title': 'Capability Matching',
        'results': results,
        'sample_analysis': analysis,
    }


def run_capacity_scenarios():
    """Capacity calculations: workload levels and signal overrides."""
    results = []
    workspace, team = setup_team('Capacity Team')
    project = create_project(team, workspace, 'Capacity Project')

    ensure_skill('python')

    available = create_member(team, 'Available Dev', 'available@test.com', ['python'], capacity_level='AVAILABLE')
    balanced = create_member(team, 'Balanced Dev', 'balanced@test.com', ['python'], capacity_level='BALANCED')
    near = create_member(team, 'Near Cap Dev', 'near@test.com', ['python'], capacity_level='NEAR_CAPACITY')
    over = create_member(team, 'Over Cap Dev', 'over@test.com', ['python'], capacity_level='OVER_CAPACITY')

    task = create_task(project, 'Capacity Test Task', ['python'], effort=8)

    analysis = AdaptiveEngine.analyze_task(task)
    candidates = {c['member_id']: c for c in analysis['candidates']}

    results.append({
        'name': 'Available Capacity',
        'description': 'AVAILABLE signal keeps candidate viable.',
        'expected': 'ALTERNATIVE / Eligible',
        'actual': candidates[str(available.id)]['recommendation_result']['recommendation'],
        'pass': candidates[str(available.id)]['is_eligible'],
    })
    results.append({
        'name': 'Balanced Capacity',
        'description': 'BALANCED signal keeps candidate viable.',
        'expected': 'ALTERNATIVE / Eligible',
        'actual': candidates[str(balanced.id)]['recommendation_result']['recommendation'],
        'pass': candidates[str(balanced.id)]['is_eligible'],
    })
    results.append({
        'name': 'Near Capacity',
        'description': 'NEAR_CAPACITY signal still yields ALTERNATIVE.',
        'expected': 'ALTERNATIVE',
        'actual': candidates[str(near.id)]['recommendation_result']['recommendation'],
        'pass': candidates[str(near.id)]['recommendation_result']['recommendation'] == 'ALTERNATIVE',
    })
    results.append({
        'name': 'Over Capacity Signal Override',
        'description': 'OVER_CAPACITY signal triggers review.',
        'expected': 'REVIEW_REQUIRED',
        'actual': candidates[str(over.id)]['recommendation_result']['recommendation'],
        'pass': candidates[str(over.id)]['recommendation_result']['recommendation'] == 'REVIEW_REQUIRED',
    })

    # Workload threshold demonstration via direct calculate_capacity
    fresh = Member.objects.create(team=team, name='Workload Fresh', email='fresh@test.com')
    WorkProfile.objects.create(member=fresh, skills=['python'])
    CapacitySignal.objects.create(member=fresh, level='AVAILABLE')
    cap_light = AdaptiveEngine.calculate_capacity(fresh, task)
    results.append({
        'name': 'Light Workload => AVAILABLE',
        'description': 'Member with no active assignments gets projected load < 15h.',
        'expected': 'AVAILABLE',
        'actual': cap_light['fit'].name if isinstance(cap_light['fit'], CapacityFit) else cap_light['fit'],
        'pass': cap_light['fit'] == CapacityFit.AVAILABLE,
    })

    return {
        'title': 'Capacity Calculations',
        'results': results,
        'sample_analysis': analysis,
    }


def run_access_scenarios():
    """Access readiness: READY, NEEDS_SUPPORT, UNRESOLVED."""
    results = []
    workspace, team = setup_team('Access Team', access_support=['Remote'])
    project = create_project(team, workspace, 'Access Project')

    ensure_skill('python')

    ready = create_member(team, 'Ready Dev', 'ready@test.com', ['python'],
                          access_prefs=['Remote'], capacity_level='AVAILABLE')
    needs_support = create_member(team, 'Needs Support Dev', 'support@test.com', ['python'],
                                  access_prefs=[], capacity_level='AVAILABLE')
    unresolved = create_member(team, 'Unresolved Dev', 'unresolved@test.com', ['python'],
                                access_prefs=['Flexible Hours'], capacity_level='AVAILABLE')

    task_ready = create_task(project, 'Ready Task', ['python'], access=['Remote'])
    task_support = create_task(project, 'Support Task', ['python'], access=['Remote', 'Flexible Hours'])
    task_unresolved = create_task(project, 'Unresolved Task', ['python'], access=['Screen Reader'])

    analysis_ready = AdaptiveEngine.analyze_task(task_ready)
    candidates_ready = {c['member_id']: c for c in analysis_ready['candidates']}

    results.append({
        'name': 'Access READY',
        'description': 'Workspace supports Remote and employee prefers Remote.',
        'expected': 'READY / Eligible',
        'actual': candidates_ready[str(ready.id)]['access']['readiness'],
        'pass': candidates_ready[str(ready.id)]['is_eligible'],
    })

    analysis_support = AdaptiveEngine.analyze_task(task_support)
    candidates_support = {c['member_id']: c for c in analysis_support['candidates']}
    results.append({
        'name': 'Access NEEDS_SUPPORT',
        'description': 'Flexible Hours is required but not supported and employee has no preference.',
        'expected': 'NEEDS_SUPPORT / REVIEW_REQUIRED',
        'actual': candidates_support[str(needs_support.id)]['access']['readiness'],
        'pass': (candidates_support[str(needs_support.id)]['access']['readiness'] == AccessReadiness.NEEDS_SUPPORT.value
                 and candidates_support[str(needs_support.id)]['recommendation_result']['recommendation'] == 'REVIEW_REQUIRED'),
    })

    analysis_unresolved = AdaptiveEngine.analyze_task(task_unresolved)
    candidates_unresolved = {c['member_id']: c for c in analysis_unresolved['candidates']}
    results.append({
        'name': 'Access UNRESOLVED',
        'description': 'Screen Reader is not supported at all.',
        'expected': 'UNRESOLVED / REVIEW_REQUIRED',
        'actual': candidates_unresolved[str(unresolved.id)]['access']['readiness'],
        'pass': (candidates_unresolved[str(unresolved.id)]['access']['readiness'] == AccessReadiness.UNRESOLVED.value
                 and not candidates_unresolved[str(unresolved.id)]['is_eligible']),
    })

    return {
        'title': 'Access Readiness',
        'results': results,
        'sample_analysis': analysis_support,
    }


def run_policy_scenarios():
    """Policy evaluation: all 16 adversarial personas."""
    results = []

    def base_candidate():
        return {
            'member_id': 'EMP-1',
            'capability': {
                'status': 'ELIGIBLE', 'level': 'STRONG', 'confidence': 'HIGH',
                'mandatory_missing': [],
                'relevant_experience_result': {'evidence_task_ids': []},
                'reason_codes': ['OBSERVED_EVIDENCE_SUPPORTS_REQUIREMENT'],
            },
            'capacity': {'current_fit': 'AVAILABLE', 'fit': 'BALANCED', 'signal_level': 'AVAILABLE'},
            'access': {'readiness': 'READY'},
        }

    personas = [
        ('cold_start_expert', {'capability__confidence': 'LOW'}, 'ALTERNATIVE', 'LIMITED_HISTORICAL_EVIDENCE'),
        ('declared_observed_disagree', {'capability__status': 'REVIEW_REQUIRED'}, 'REVIEW_REQUIRED', 'MIXED_PROFICIENCY_EVIDENCE'),
        ('many_minor_evidence', {'capability__level': 'LIMITED', 'capability__confidence': 'MEDIUM'}, 'ALTERNATIVE', 'MANDATORY_REQUIREMENTS_MET'),
        ('few_primary_evidence', {'capability__confidence': 'LOW'}, 'ALTERNATIVE', 'LIMITED_HISTORICAL_EVIDENCE'),
        ('identical_contexts', {'capability__confidence': 'MEDIUM'}, 'ALTERNATIVE', 'SUSTAINABLE_PROJECTED_CAPACITY'),
        ('strong_but_stale', {'capability__status': 'REVIEW_REQUIRED', 'capability__reason_codes': ['STALE_OBSERVED_EVIDENCE']}, 'REVIEW_REQUIRED', 'STALE_OBSERVED_EVIDENCE'),
        ('mandatory_missing', {'capability__mandatory_missing': ['react'], 'capability__level': 'VERY_STRONG'}, 'NOT_VIABLE', 'MANDATORY_REQUIREMENT_MISSING'),
        ('required_fit_missing', {'capability__status': 'REQUIREMENT_NOT_MET'}, 'NOT_VIABLE', 'CAPABILITY_REQUIREMENT_NOT_MET'),
        ('preferred_missing', {}, 'ALTERNATIVE', 'MANDATORY_REQUIREMENTS_MET'),
        ('overqualified', {'capability__level': 'VERY_STRONG'}, 'ALTERNATIVE', 'ACCESS_READY'),
        ('strong_over_capacity', {'capability__level': 'VERY_STRONG', 'capacity__fit': 'OVER_CAPACITY'}, 'REVIEW_REQUIRED', 'PROJECTED_OVER_CAPACITY'),
        ('moderate_available', {'capability__level': 'MODERATE', 'capacity__fit': 'AVAILABLE'}, 'ALTERNATIVE', 'SUSTAINABLE_PROJECTED_CAPACITY'),
        ('unresolved_access', {'access__readiness': 'UNRESOLVED'}, 'REVIEW_REQUIRED', 'ACCESS_UNRESOLVED'),
        ('resolvable_access', {'access__readiness': 'NEEDS_SUPPORT'}, 'REVIEW_REQUIRED', 'ACCESS_SUPPORT_REQUIRED'),
        ('employee_over_signal', {'capacity__signal_level': 'OVER_CAPACITY'}, 'REVIEW_REQUIRED', 'EMPLOYEE_CAPACITY_SIGNAL'),
        ('near_capacity', {'capacity__fit': 'NEAR_CAPACITY'}, 'ALTERNATIVE', 'PROJECTED_NEAR_CAPACITY'),
    ]

    for name, changes, expected_category, expected_code in personas:
        cand = base_candidate()
        for key, value in changes.items():
            section, field = key.split('__')
            cand[section][field] = value
        result = evaluate_candidate(cand)
        results.append({
            'name': f'Persona: {name}',
            'description': f"Expected category '{expected_category}' and reason code '{expected_code}'.",
            'expected': f'{expected_category} / {expected_code}',
            'actual': f"{result['recommendation']} / {result['reason_codes']}",
            'pass': result['recommendation'] == expected_category and expected_code in result['reason_codes'],
        })

    # Selection invariant: sustainable beats overloaded
    sustainable = base_candidate()
    overloaded = base_candidate()
    overloaded['member_id'] = 'EMP-2'
    overloaded['capacity']['fit'] = 'OVER_CAPACITY'
    sustainable['recommendation_result'] = evaluate_candidate(sustainable)
    overloaded['recommendation_result'] = evaluate_candidate(overloaded)
    winner = select_candidate([overloaded, sustainable])
    results.append({
        'name': 'Selection: Sustainable beats stronger overloaded',
        'description': 'select_candidate prefers lower workload over stronger capability.',
        'expected': 'EMP-1 (sustainable)',
        'actual': winner['member_id'] if winner else 'None',
        'pass': winner is sustainable,
    })

    return {
        'title': 'Policy Evaluation (16 Adversarial Personas)',
        'results': results,
        'sample_analysis': {'personas_total': len(personas), 'invariant_test': 'sustainable_beats_overloaded'},
    }


def run_reanalysis_scenarios():
    """Re-analysis triggers: capacity signal changes, blockers, task changes."""
    results = []
    workspace, team = setup_team('Reanalysis Team')
    project = create_project(team, workspace, 'Reanalysis Project')

    ensure_skill('python')
    dev = create_member(team, 'Reanalysis Dev', 'reanalysis@test.com', ['python'], capacity_level='AVAILABLE')
    task = create_task(project, 'Reanalysis Task', ['python'], effort=8)

    first = AdaptiveEngine.save_analysis(task)
    second = AdaptiveEngine.save_analysis(task, trigger='capacity_signal_changed')
    results.append({
        'name': 'No Change => Same Analysis',
        'description': 'Re-running without changes returns the existing analysis.',
        'expected': f'first.pk == second.pk ({first.pk})',
        'actual': f'first.pk == second.pk == {second.pk}',
        'pass': first.pk == second.pk,
    })

    CapacitySignal.objects.create(member=dev, level='OVER_CAPACITY')
    third = AdaptiveEngine.save_analysis(task, trigger='capacity_signal_changed')
    results.append({
        'name': 'Capacity Signal Change => New Analysis',
        'description': 'OVER_CAPACITY signal triggers reanalysis.',
        'expected': 'New AdaptiveAnalysis object',
        'actual': f'third.pk={third.pk}, first.pk={first.pk}',
        'pass': third.pk != first.pk,
    })
    results.append({
        'name': 'Redistribution Review Triggered',
        'description': 'Reason codes include REDISTRIBUTION_REVIEW.',
        'expected': 'REDISTRIBUTION_REVIEW in reason_codes',
        'actual': third.recommendation.get('reason_codes', []),
        'pass': 'REDISTRIBUTION_REVIEW' in third.recommendation.get('reason_codes', []),
    })

    # Blocker trigger
    Blocker.objects.create(task=task, type='DEPENDENCY', note='Waiting for API')
    fourth = AdaptiveEngine.save_analysis(task, trigger='blocker_added')
    results.append({
        'name': 'Blocker => New Analysis',
        'description': 'Adding an active blocker triggers reanalysis.',
        'expected': 'New AdaptiveAnalysis, open_blockers non-empty',
        'actual': f'fourth.pk={fourth.pk}, open_blockers={fourth.evidence.get("open_blockers", [])}',
        'pass': fourth.pk != third.pk and fourth.evidence.get('open_blockers'),
    })

    # Task change trigger (title / effort)
    task.title = 'Reanalysis Task Updated'
    task.estimated_effort = 16
    task.save()
    fifth = AdaptiveEngine.save_analysis(task, trigger='task_changed')
    results.append({
        'name': 'Task Change => New Analysis',
        'description': 'Modifying task attributes triggers reanalysis.',
        'expected': 'New AdaptiveAnalysis object',
        'actual': f'fifth.pk={fifth.pk}, fourth.pk={fourth.pk}',
        'pass': fifth.pk != fourth.pk,
    })

    return {
        'title': 'Re-analysis Triggers',
        'results': results,
        'sample_analysis': fifth.to_dict() if hasattr(fifth, 'to_dict') else {
            'recommendation': fifth.recommendation,
            'evidence': fifth.evidence,
        },
    }


def run_skill_evidence_scenarios():
    """Skill evidence workflow: proposal, review, confirmation."""
    results = []
    workspace, team = setup_team('Evidence Team')
    project = create_project(team, workspace, 'Evidence Project')

    skill = ensure_skill('python')
    dev = create_member(team, 'Evidence Dev', 'evidence@test.com', ['python'], capacity_level='AVAILABLE')
    task = create_task(project, 'Evidence Task', ['python'], effort=8)

    # Assign and complete the task
    Assignment.objects.create(task=task, member=dev, decided_by=dev)
    CompletionEvidence.objects.create(task=task, estimated_effort=8, actual_effort=10, factors=['unit_tested'])
    task.status = TaskStatus.COMPLETED
    task.save()

    # Propose evidence based on the latest assignment
    propose_task_evidence(task)
    proposed = SkillEvidence.objects.filter(member=dev, skill=skill, task=task)
    results.append({
        'name': 'Evidence Proposed',
        'description': 'propose_task_evidence creates a SkillEvidence row for the completed task.',
        'expected': '1 SkillEvidence row, not confirmed',
        'actual': f'count={proposed.count()}, confirmed={proposed.first().confirmed_by_employee if proposed.exists() else None}',
        'pass': proposed.exists() and not proposed.first().confirmed_by_employee,
    })

    # Confirm evidence and observe proficiency update
    evidence = proposed.first()
    confirm_evidence(evidence)
    evidence.refresh_from_db()
    results.append({
        'name': 'Evidence Confirmed',
        'description': 'confirm_evidence marks the row confirmed and updates EmployeeSkill.',
        'expected': 'confirmed_by_employee == True',
        'actual': f'confirmed={evidence.confirmed_by_employee}',
        'pass': evidence.confirmed_by_employee,
    })

    emp_skill = EmployeeSkill.objects.get(member=dev, skill=skill)
    results.append({
        'name': 'Observed Proficiency Updated',
        'description': 'Confirmed evidence updates observed_proficiency and evidence_confidence.',
        'expected': 'observed_proficiency in [BEGINNER, INTERMEDIATE, ADVANCED] and evidence_confidence set',
        'actual': f'observed={emp_skill.observed_proficiency}, confidence={emp_skill.evidence_confidence}',
        'pass': emp_skill.observed_proficiency != 'UNKNOWN' and emp_skill.evidence_confidence != 'UNKNOWN',
    })

    return {
        'title': 'Skill Evidence Workflow',
        'results': results,
        'sample_analysis': {
            'evidence_id': str(evidence.id),
            'employee_skill': {
                'declared': emp_skill.declared_proficiency,
                'observed': emp_skill.observed_proficiency,
                'confidence': emp_skill.evidence_confidence,
            },
        },
    }


def run_edge_case_scenarios():
    """Edge cases: cold start, stale evidence, conflicting proficiency."""
    results = []
    workspace, team = setup_team('Edge Team')
    project = create_project(team, workspace, 'Edge Project')

    # Cold start: profile exists, no observed evidence
    ensure_skill('react')
    cold = create_member(team, 'Cold Start Dev', 'cold@test.com',
                         [{'skill': 'react', 'level': 'ADVANCED'}], capacity_level='AVAILABLE')
    task = create_task(project, 'Cold Start Task',
                       [{'skill': 'react', 'priority': 'MANDATORY', 'min_level': 'ADVANCED'}], effort=5)
    analysis = AdaptiveEngine.analyze_task(task)
    cold_candidate = analysis['candidates'][0]
    results.append({
        'name': 'Cold Start',
        'description': 'Declared proficiency without observed evidence remains low confidence.',
        'expected': 'ELIGIBLE with LOW confidence, SELF_DECLARED_ONLY',
        'actual': f"status={cold_candidate['capability']['status']}, confidence={cold_candidate['capability']['confidence']}",
        'pass': (cold_candidate['capability']['status'] == 'ELIGIBLE'
                 and cold_candidate['capability']['confidence'] == 'LOW'),
    })

    # Stale observed evidence: declared lower than observed, observed meets requirement
    emp_skill = EmployeeSkill.objects.get(member=cold, skill=resolve_skill('react'))
    emp_skill.declared_proficiency = 'INTERMEDIATE'
    emp_skill.observed_proficiency = 'ADVANCED'
    emp_skill.evidence_confidence = 'HIGH'
    emp_skill.last_evidence_at = timezone.now() - timedelta(days=400)
    emp_skill.save()
    stale_result = AdaptiveEngine.calculate_capability(task, cold.work_profile)
    results.append({
        'name': 'Stale Observed Evidence',
        'description': 'Evidence older than 365 days reduces confidence; declared INTERMEDIATE, observed ADVANCED triggers review.',
        'expected': 'REVIEW_REQUIRED, confidence MEDIUM or LOW, observed still ADVANCED',
        'actual': f"status={stale_result['status']}, confidence={stale_result['proficiency']['react']['confidence']}, observed={stale_result['proficiency']['react']['observed']}",
        'pass': (stale_result['status'] == 'REVIEW_REQUIRED'
                 and stale_result['proficiency']['react']['observed'] == 'ADVANCED'
                 and stale_result['proficiency']['react']['confidence'] in ('MEDIUM', 'LOW')),
    })

    # Conflicting proficiency: declared ADVANCED, observed INTERMEDIATE with HIGH confidence
    emp_skill.declared_proficiency = 'ADVANCED'
    emp_skill.observed_proficiency = 'INTERMEDIATE'
    emp_skill.evidence_confidence = 'HIGH'
    emp_skill.last_evidence_at = timezone.now()
    emp_skill.save()
    conflict_result = AdaptiveEngine.calculate_capability(task, cold.work_profile)
    results.append({
        'name': 'Conflicting Proficiency',
        'description': 'Declared ADVANCED but observed INTERMEDIATE with HIGH confidence triggers review.',
        'expected': 'REVIEW_REQUIRED, MIXED_PROFICIENCY_EVIDENCE',
        'actual': f"status={conflict_result['status']}, reasons={conflict_result['reason_codes']}",
        'pass': (conflict_result['status'] == 'REVIEW_REQUIRED'
                 and 'MIXED_PROFICIENCY_EVIDENCE' in conflict_result['reason_codes']),
    })

    # Alias normalization standalone
    ensure_skill('react', aliases=['reactjs'])
    alias_dev = create_member(team, 'Alias Dev', 'alias@test.com', ['ReactJS'], capacity_level='AVAILABLE')
    alias_task = create_task(project, 'Alias Task', ['react'], effort=5)
    alias_analysis = AdaptiveEngine.analyze_task(alias_task)
    alias_candidate = alias_analysis['candidates'][0]
    results.append({
        'name': 'Alias Normalization',
        'description': 'ReactJS declared skill maps to canonical react.',
        'expected': 'Eligible',
        'actual': 'ELIGIBLE' if alias_candidate['is_eligible'] else 'NOT ELIGIBLE',
        'pass': alias_candidate['is_eligible'],
    })

    return {
        'title': 'Edge Cases',
        'results': results,
        'sample_analysis': conflict_result,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(all_results):
    report_path = r'D:\Grinding Coder\CODING PROJECT\HACKATON\Pantara\backend\ADAPTIVE_ENGINE_TEST_REPORT.md'

    all_assertions = []
    for section in all_results:
        for r in section['results']:
            all_assertions.append((section['title'], r))

    total = len(all_assertions)
    passed = sum(1 for _, r in all_assertions if r['pass'])
    failed = total - passed

    lines = []
    lines.append('# Adaptive Engine Dummy-Data Test Report')
    lines.append('')
    lines.append(f'**Generated at**: {timezone.now().isoformat()}')
    lines.append('')
    lines.append('## Executive Summary')
    lines.append('')
    lines.append(f'- **Total assertions**: {total}')
    lines.append(f'- **Passed**: {passed}')
    lines.append(f'- **Failed**: {failed}')
    lines.append(f'- **Pass rate**: {passed / total * 100 if total else 0:.1f}%')
    lines.append('')
    lines.append('This report exercises the adaptive engine across capability, capacity, access, policy, re-analysis, evidence workflow, and edge-case dimensions. Each assertion compares expected behavior against actual deterministic output.')
    lines.append('')

    for section in all_results:
        lines.append(f"## {section['title']}")
        lines.append('')
        lines.append('| Scenario | Expected | Actual | Status |')
        lines.append('|----------|----------|--------|--------|')
        for r in section['results']:
            status = 'PASS' if r['pass'] else 'FAIL'
            lines.append(f"| {r['name']} | {r['expected']} | {r['actual']} | {status} |")
        lines.append('')
        for r in section['results']:
            lines.append(f"### {r['name']}")
            lines.append(f"- **Description**: {r['description']}")
            lines.append(f"- **Expected**: {r['expected']}")
            lines.append(f"- **Actual**: {r['actual']}")
            lines.append(f"- **Status**: {'PASS' if r['pass'] else 'FAIL'}")
            lines.append('')

        lines.append('### Sample Data')
        lines.append('```json')
        try:
            lines.append(json.dumps(section['sample_analysis'], indent=2, default=str)[:1500])
        except Exception as e:
            lines.append(str(e))
        lines.append('```')
        lines.append('')

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'Report written to {report_path}')
    return report_path


def run_all():
    all_results = []
    all_results.append(run_capability_scenarios())
    all_results.append(run_capacity_scenarios())
    all_results.append(run_access_scenarios())
    all_results.append(run_policy_scenarios())
    all_results.append(run_reanalysis_scenarios())
    all_results.append(run_skill_evidence_scenarios())
    all_results.append(run_edge_case_scenarios())

    report_path = generate_report(all_results)
    print('Testing complete. Report:', report_path)
    return report_path


if __name__ == '__main__':
    run_all()
