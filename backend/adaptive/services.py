"""Deterministic assignment support; thresholds are demo heuristics."""

from datetime import date
from datetime import timedelta
from django.utils import timezone

from core.models import CapacityLevel, CapacitySignal, WorkProfile
from work.models import Assignment, TaskStatus
from adaptive.models import (AccessReadiness, AdaptiveAnalysis, CapabilityFit, CapacityFit,
                             EmployeeSkill, TaskSkillRequirement)

SKILL_ALIASES = {'reactjs': 'react', 'react.js': 'react', 'react-js': 'react', 'ts': 'typescript', 'py': 'python'}
LEVELS = {'BEGINNER': 1, 'INTERMEDIATE': 2, 'ADVANCED': 3, 'EXPERT': 4, 'UNKNOWN': 0}


def _skill(value):
    value = value.casefold().strip()
    return SKILL_ALIASES.get(value, value)


def _entries(values, default_level='INTERMEDIATE'):
    result = []
    for value in values or []:
        if isinstance(value, str):
            result.append((_skill(value), default_level))
        elif isinstance(value, dict) and value.get('skill'):
            result.append((_skill(value['skill']), str(value.get('level', default_level)).upper()))
    return result


def _requirements(values):
    result = []
    for value in values or []:
        if not isinstance(value, str) and not isinstance(value, dict):
            continue
        skill = value if isinstance(value, str) else value.get('skill')
        if not skill:
            continue
        priority = 'REQUIRED' if isinstance(value, str) else str(value.get('priority', 'REQUIRED')).upper()
        min_level = 'INTERMEDIATE' if isinstance(value, str) else str(value.get('min_level', 'INTERMEDIATE')).upper()
        result.append({'skill': _skill(skill),
                       'priority': priority if priority in {'MANDATORY', 'REQUIRED', 'PREFERRED'} else 'REQUIRED',
                       'min_level': min_level if min_level in LEVELS else 'INTERMEDIATE'})
    return result


def task_load(task):
    if task.status == TaskStatus.COMPLETED:
        return 0.0
    days = (task.deadline - date.today()).days if task.deadline else None
    deadline_factor = 1.5 if days is not None and days < 3 else 1.2 if days is not None and days <= 7 else 1.0
    complexity_factor = {'LOW': 0.8, 'MEDIUM': 1.0, 'HIGH': 1.3}[task.complexity]
    return round(task.estimated_effort * (1 - task.progress / 100) * complexity_factor * deadline_factor, 2)


class AdaptiveEngine:
    @staticmethod
    def calculate_capability(task, profile, completed_assignments=None, requirement_rows=None, employee_rows=None):
        if requirement_rows is None:
            requirement_rows = list(TaskSkillRequirement.objects.filter(task=task).select_related('skill')) if task.pk else []
        if employee_rows is None:
            employee_rows = list(EmployeeSkill.objects.filter(member=profile.member).select_related('skill')) if profile and profile.pk else []
        requirements = ([{'skill': row.skill.canonical_name.casefold(), 'priority': row.requirement_type,
                          'min_level': row.minimum_proficiency} for row in requirement_rows]
                        if requirement_rows else _requirements(task.required_skills))
        skill_levels = {skill: level for skill, level in _entries(profile.skills if profile else [])}
        if employee_rows:
            skill_levels = {row.skill.canonical_name.casefold(): row.declared_proficiency for row in employee_rows}
        observed = {row.skill.canonical_name.casefold(): row for row in employee_rows}
        required = {r['skill'] for r in requirements if r['priority'] != 'PREFERRED'}
        reasons = []
        conflicts = []
        matched = []
        proficiency = {}
        for r in requirements:
            name = r['skill']
            declared = LEVELS.get(skill_levels.get(name, 'UNKNOWN'), 0)
            row = observed.get(name)
            fresh = bool(row and row.last_evidence_at and row.last_evidence_at >= timezone.now() - timedelta(days=365))
            observed_level = LEVELS.get(row.observed_proficiency, 0) if fresh else 0
            high = bool(fresh and row.evidence_confidence == 'HIGH')
            minimum = LEVELS.get(r['min_level'], 2)
            proficiency[name] = {
                'declared': skill_levels.get(name, 'UNKNOWN'),
                'observed': row.observed_proficiency if fresh else 'UNKNOWN',
                'confidence': row.evidence_confidence if fresh else 'LOW',
            }
            if high and observed_level >= minimum:
                meets = True
                reasons.append('OBSERVED_EVIDENCE_SUPPORTS_REQUIREMENT')
            elif high and observed_level < minimum and declared >= minimum:
                meets = False
                conflicts.append(name)
                reasons.append('MIXED_PROFICIENCY_EVIDENCE')
            else:
                meets = declared >= minimum
                if meets:
                    reasons.append('SELF_DECLARED_ONLY')
            if meets and r['priority'] != 'PREFERRED':
                matched.append(name)
        matched = sorted(set(matched))
        missing = sorted(required - set(matched))
        ratio = len(matched) / len(required) if required else 1.0
        mandatory = {r['skill'] for r in requirements if r['priority'] == 'MANDATORY'}
        mandatory_missing = sorted(mandatory - set(matched))
        preferred = sorted(r['skill'] for r in requirements if r['priority'] == 'PREFERRED'
                           and LEVELS.get(skill_levels.get(r['skill'], 'UNKNOWN'), 0) >= LEVELS.get(r['min_level'], 2))
        experience = {_skill(e.get('skill', '')) for e in (profile.experience if profile else []) if isinstance(e, dict)}
        relevant_experience = sorted(required & experience)
        if completed_assignments is None:
            if profile and getattr(profile, 'member', None):
                previous = Assignment.objects.filter(
                    member=profile.member, task__status=TaskStatus.COMPLETED,
                    task__completion_evidence__isnull=False,
                ).select_related('task').distinct()
                completed_assignments = list(previous)
            else:
                completed_assignments = []
        related = []
        task_tags = {_skill(tag) for tag in task.tags}
        for assignment in completed_assignments:
            old = assignment.task
            old_skills = {r['skill'] for r in _requirements(old.required_skills)}
            skill_overlap = len(required & old_skills) / len(required) if required else 0
            category_match = bool(task.category and task.category.casefold() == old.category.casefold())
            tag_overlap = bool(task_tags & {_skill(tag) for tag in old.tags})
            # ponytail: structured overlap is a demo heuristic; tune with labeled task pairs later.
            relevance = 0.6 * skill_overlap + 0.2 * category_match + 0.2 * tag_overlap
            if relevance >= 0.3:
                related.append((str(old.id), relevance))
        related.sort(key=lambda item: item[1], reverse=True)
        similar = len(related)
        status = ('REVIEW_REQUIRED' if conflicts else 'REQUIREMENT_NOT_MET' if mandatory_missing or ratio < 0.5
                  else 'ELIGIBLE')
        required_confidences = [proficiency[name]['confidence'] for name in required]
        confidence = ('HIGH' if required_confidences and all(c == 'HIGH' for c in required_confidences)
                      else 'MEDIUM' if required_confidences and all(c in {'HIGH', 'MEDIUM'} for c in required_confidences)
                      else 'LOW')
        fit = CapabilityFit.STRONG if not missing else CapabilityFit.PARTIAL if ratio >= 0.5 else CapabilityFit.LIMITED
        level = ('VERY_STRONG' if ratio == 1 and confidence == 'HIGH' and similar >= 2 else
                 'STRONG' if ratio == 1 else 'MODERATE' if ratio >= 0.5 else
                 'LIMITED' if skill_levels else 'INSUFFICIENT_EVIDENCE')
        return {
            'status': status, 'confidence': confidence, 'proficiency': proficiency,
            'level': level, 'fit': fit, 'score': 2.0 if ratio == 1 else 1.0 if ratio >= 0.5 else 0.0,
            'skill_match': {'level': 'FULL' if not missing else 'PARTIAL' if matched else 'NONE'},
            'required_match': round(ratio, 2), 'matched_skills': matched,
            'missing_skills': missing, 'relevant_experience': relevant_experience,
            'mandatory_missing': mandatory_missing, 'preferred_matches': preferred,
            'missing_requirements': missing, 'considerations': (['MIXED_PROFICIENCY_EVIDENCE'] if conflicts else
                                                                 ['MANDATORY_PROFICIENCY_NOT_MET'] if mandatory_missing else []),
            'similar_completed_tasks': similar,
            'relevant_experience_result': {'level': 'STRONG' if similar >= 2 else 'MODERATE' if similar else 'NONE',
                                           'evidence_task_ids': [item[0] for item in related[:3]]},
            'task_familiarity': {'level': 'HIGH' if related and related[0][1] >= 0.8 else
                                 'MODERATE' if related else 'LOW' if completed_assignments else 'UNKNOWN',
                                 'similar_task_ids': [item[0] for item in related[:3]]},
            'evidence': f'{len(matched)}/{len(required)} required skills matched; {len(relevant_experience)} experience records; {similar} relevant completed tasks.',
            'reason_codes': (['REQUIRED_SKILLS_MATCH'] if not missing else ['MISSING_REQUIRED_SKILLS'])
                            + (['MANDATORY_REQUIREMENT_MISSING'] if mandatory_missing else [])
                            + (['RELEVANT_EXPERIENCE'] if relevant_experience else [])
                            + (['SIMILAR_TASK_HISTORY'] if similar else []) + sorted(set(reasons)),
        }

    @staticmethod
    def calculate_capacity(member, task, active_assignments=None, signal_level=None):
        if active_assignments is None:
            assignments = member.assignments.filter(
                task__status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]
            ).select_related('task')
            active_assignments = list(assignments)
        if signal_level is None:
            signal_level = member.latest_capacity_signal

        active_tasks = {a.task_id: a.task for a in active_assignments if a.task_id != task.id}
        current = round(sum(task_load(t) for t in active_tasks.values()), 2)
        projected = round(current + task_load(task), 2)
        signal = signal_level or CapacityLevel.BALANCED
        # ponytail: 40 weighted hours is a demo baseline; calibrate per team with observed workload.
        system_fit = (CapacityFit.OVER_CAPACITY if projected >= 40 else
                      CapacityFit.NEAR_CAPACITY if projected >= 30 else
                      CapacityFit.BALANCED if projected >= 15 else CapacityFit.AVAILABLE)
        levels = list(CapacityLevel.values)
        signal_floor = CapacityLevel.NEAR_CAPACITY if signal == CapacityLevel.OVER_CAPACITY else signal
        fit = levels[max(levels.index(system_fit), levels.index(signal_floor))]
        score = {CapacityFit.AVAILABLE: 2.0, CapacityFit.BALANCED: 1.5,
                 CapacityFit.NEAR_CAPACITY: 0.8, CapacityFit.OVER_CAPACITY: 0.0}[fit]
        return {
            'fit': fit, 'system_fit': system_fit, 'score': score, 'current_hours': current,
            'projected_hours': projected, 'weighted_workload_units': projected,
            'current_workload_units': current, 'signal_level': signal,
            'active_tasks_count': len(active_tasks),
            'evidence': f'{len(active_tasks)} active tasks; {current} weighted hours now, {projected} if assigned; self-report: {signal}.',
            'reason_codes': ['CAPACITY_' + fit],
        }

    @staticmethod
    def calculate_access(task, profile, workspace_support=None):
        if workspace_support is None:
            workspace = getattr(getattr(task, 'project', None), 'workspace', None)
            workspace_support = workspace.access_support if workspace else []

        required = {_skill(item) for item in task.access_requirements}
        explicit_needs = bool(getattr(profile, 'access_needs', []) if profile else [])
        needs = {_skill(item) for item in (profile.access_needs if explicit_needs else [])}
        legacy_support = {_skill(item) for item in (profile.access_preferences if profile else [])}
        support = {_skill(item) for item in workspace_support}
        available = support if explicit_needs else (legacy_support | support)
        ready = sorted(required & available)
        unmet = sorted(required - available)
        readiness = (AccessReadiness.READY if not unmet else
                     AccessReadiness.NEEDS_SUPPORT if ready else AccessReadiness.UNRESOLVED)
        return {
            'readiness': readiness, 'score': 2.0 if readiness == AccessReadiness.READY else 1.0 if ready else 0.0,
            'employee_needs': sorted(needs), 'matched_preferences': sorted(required & (needs or legacy_support)),
            'workplace_support': sorted(required & support), 'unmet_preferences': unmet,
            'evidence': f'Available: {", ".join(ready) or "none"}; needs review: {", ".join(unmet) or "none"}.',
            'reason_codes': ['ACCESS_READY' if not unmet else 'ACCESS_REVIEW_REQUIRED'],
        }

    @classmethod
    def _fetch_team_context(cls, team):
        """Batch fetch team data to avoid per-candidate database queries."""
        from collections import defaultdict
        members = list(team.members.all())
        member_ids = [m.id for m in members]

        profiles = {p.member_id: p for p in WorkProfile.objects.filter(member_id__in=member_ids)}
        skills_by_member = defaultdict(list)
        for row in EmployeeSkill.objects.filter(member_id__in=member_ids).select_related('skill'):
            skills_by_member[row.member_id].append(row)
        requirements_by_task = defaultdict(list)
        for row in TaskSkillRequirement.objects.filter(task__project__team=team).select_related('skill'):
            requirements_by_task[row.task_id].append(row)

        completed_qs = Assignment.objects.filter(
            member_id__in=member_ids,
            task__status=TaskStatus.COMPLETED,
            task__completion_evidence__isnull=False
        ).select_related('task')
        completed_by_member = defaultdict(list)
        for a in completed_qs:
            completed_by_member[a.member_id].append(a)

        active_qs = Assignment.objects.filter(
            member_id__in=member_ids,
            task__status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]
        ).select_related('task')
        active_by_member = defaultdict(list)
        for a in active_qs:
            active_by_member[a.member_id].append(a)

        signals = CapacitySignal.objects.filter(member_id__in=member_ids).order_by('member_id', '-created_at', '-id')
        signals_by_member = {}
        for s in signals:
            if s.member_id not in signals_by_member:
                signals_by_member[s.member_id] = s.level

        workspace_support = team.workspace.access_support if hasattr(team, 'workspace') else []

        return {
            'members': members,
            'profiles': profiles,
            'skills_by_member': skills_by_member,
            'requirements_by_task': requirements_by_task,
            'completed_by_member': completed_by_member,
            'active_by_member': active_by_member,
            'signals_by_member': signals_by_member,
            'workspace_support': workspace_support,
        }

    @classmethod
    def analyze_task(cls, task, context=None):
        if context is None:
            team = task.project.team
            context = cls._fetch_team_context(team)

        workspace_support = context['workspace_support']
        open_blockers = list(task.blockers.exclude(status='RESOLVED').values_list('type', flat=True)) if hasattr(task, 'blockers') else []

        candidates = []
        for member in context['members']:
            profile = context['profiles'].get(member.id)
            completed_assignments = context['completed_by_member'].get(member.id, [])
            active_assignments = context['active_by_member'].get(member.id, [])
            signal_level = context['signals_by_member'].get(member.id, CapacityLevel.BALANCED)

            capability = cls.calculate_capability(
                task, profile, completed_assignments,
                context['requirements_by_task'].get(task.id, []),
                context['skills_by_member'].get(member.id, []),
            ) if profile else {
                'status': 'REQUIREMENT_NOT_MET', 'confidence': 'LOW',
                'level': 'INSUFFICIENT_EVIDENCE',
                'fit': CapabilityFit.LIMITED, 'score': 0.0, 'required_match': 0.0,
                'matched_skills': [], 'missing_skills': task.required_skills,
                'relevant_experience': [], 'mandatory_missing': task.required_skills,
                'preferred_matches': [], 'similar_completed_tasks': 0,
                'relevant_experience_result': {'level': 'NONE', 'evidence_task_ids': []},
                'task_familiarity': {'level': 'UNKNOWN', 'similar_task_ids': []},
                'evidence': 'Work profile missing.', 'reason_codes': ['PROFILE_MISSING'],
            }
            capacity = cls.calculate_capacity(member, task, active_assignments, signal_level)
            access = cls.calculate_access(task, profile, workspace_support) if profile else {
                'readiness': AccessReadiness.UNRESOLVED, 'score': 0.0,
                'employee_needs': [], 'matched_preferences': [], 'workplace_support': [],
                'unmet_preferences': task.access_requirements,
                'evidence': 'Work profile missing.', 'reason_codes': ['PROFILE_MISSING'],
            }
            viable = capability['status'] == 'ELIGIBLE' and access['readiness'] == AccessReadiness.READY
            candidates.append({
                'member_id': str(member.id), 'member_name': member.name, 'role': member.role,
                'total_score': round(capability['score'] + capacity['score'], 2),
                'capability': capability, 'capacity': capacity, 'access': access,
                'is_eligible': viable,
                'review_required': not viable or capacity['fit'] == CapacityFit.OVER_CAPACITY
                                   or capacity['signal_level'] == CapacityLevel.OVER_CAPACITY,
            })

        candidates.sort(key=lambda c: (
            c['is_eligible'], c['capacity']['fit'] != CapacityFit.OVER_CAPACITY,
            c['capacity']['score'], c['capability']['score'], c['capability']['similar_completed_tasks'],
            len(c['capability']['relevant_experience'])
        ), reverse=True)

        viable = next((c for c in candidates if c['is_eligible']), None)
        recommendation = {'reason': 'No eligible candidate; review required skills and access support.'}
        if viable:
            recommendation = {
                'recommended_member_id': viable['member_id'],
                'recommended_member_name': viable['member_name'],
                'score': viable['total_score'], 'review_required': viable['review_required'],
                'reason_codes': viable['capability']['reason_codes'] + viable['capacity']['reason_codes'] + viable['access']['reason_codes'],
                'reason': f"{viable['member_name']}: {viable['capability']['evidence']} {viable['capacity']['evidence']} {viable['access']['evidence']}",
                'alternatives': [
                    {'member_id': c['member_id'], 'member_name': c['member_name'],
                     'review_required': c['review_required'], 'reason_codes':
                     c['capability']['reason_codes'] + c['capacity']['reason_codes'] + c['access']['reason_codes']}
                    for c in candidates if c is not viable
                ],
            }

        return {
            'candidates': candidates, 'recommendation': recommendation,
            'evidence': {'task_title': task.title, 'complexity': task.complexity,
                         'estimated_effort': task.estimated_effort,
                         'required_skills': task.required_skills,
                         'access_requirements': task.access_requirements,
                         'open_blockers': open_blockers},
            'workload_impact': {c['member_id']: {
                'before_hours': c['capacity']['current_hours'],
                'after_hours': c['capacity']['projected_hours'],
                'signal': c['capacity']['signal_level']
            } for c in candidates},
        }

    @classmethod
    def save_analysis(cls, task, trigger='manual', context=None, previous_analysis=None):
        result = cls.analyze_task(task, context=context)
        previous = previous_analysis if previous_analysis is not None else task.analyses.first()
        old_id = previous.recommendation.get('recommended_member_id') if previous else None
        new_id = result['recommendation'].get('recommended_member_id')
        result['recommendation']['trigger'] = trigger
        result['recommendation']['changed_from_previous'] = previous is not None and old_id != new_id
        if previous and previous.candidates == result['candidates'] and previous.evidence == result['evidence']:
            return previous
        if previous and trigger != 'manual' and (
            old_id != new_id or result['evidence']['open_blockers']
            or result['recommendation'].get('review_required')
        ):
            result['recommendation']['intervention'] = 'REVIEW_REDISTRIBUTION'
        return AdaptiveAnalysis.objects.create(task=task, **result)

    @classmethod
    def refresh_team(cls, team, trigger):
        """Refresh open work; changed recommendations are review prompts, not assignments."""
        from work.models import Task
        tasks = list(Task.objects.filter(
            project__team=team,
            status__in=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]
        ).prefetch_related('blockers', 'analyses'))
        if not tasks:
            return

        context = cls._fetch_team_context(team)
        for task in tasks:
            prev = task.analyses.all()[0] if task.analyses.all() else None
            cls.save_analysis(task, trigger=trigger, context=context, previous_analysis=prev)
