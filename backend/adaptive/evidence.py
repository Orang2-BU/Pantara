from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from adaptive.models import EmployeeSkill, Skill, SkillEvidence, TaskSkillRequirement


def resolve_skill(name):
    name = name.casefold().strip()
    for skill in Skill.objects.all():
        if name == skill.canonical_name.casefold() or name in {a.casefold() for a in skill.aliases}:
            return skill
    return None


def sync_profile_skills(profile):
    """Keep legacy profile writes usable with the relational catalog."""
    resolved = []
    for entry in profile.skills:
        name = entry if isinstance(entry, str) else entry['skill']
        skill = resolve_skill(name)
        if skill is None:
            raise ValueError(f'Unresolved skill: {name}')
        level = entry.get('level', 'INTERMEDIATE') if isinstance(entry, dict) else 'INTERMEDIATE'
        resolved.append((skill, level.upper()))
    profile.member.employee_skills.exclude(skill__in=[s for s, _ in resolved]).delete()
    for skill, level in resolved:
        EmployeeSkill.objects.update_or_create(
            member=profile.member, skill=skill,
            defaults={'declared_proficiency': level},
        )


def sync_task_requirements(task):
    resolved = []
    for entry in task.required_skills:
        name = entry if isinstance(entry, str) else entry['skill']
        skill = resolve_skill(name)
        if skill is None:
            raise ValueError(f'Unresolved skill: {name}')
        priority = entry.get('priority', 'REQUIRED') if isinstance(entry, dict) else 'REQUIRED'
        level = entry.get('min_level', 'INTERMEDIATE') if isinstance(entry, dict) else 'INTERMEDIATE'
        resolved.append((skill, priority.upper(), level.upper()))
    task.skill_requirements.exclude(skill__in=[s for s, _, _ in resolved]).delete()
    for skill, priority, level in resolved:
        TaskSkillRequirement.objects.update_or_create(
            task=task, skill=skill,
            defaults={'requirement_type': priority, 'minimum_proficiency': level},
        )


def reflect_profile_skills(member):
    from core.models import WorkProfile
    profile, _ = WorkProfile.objects.get_or_create(member=member)
    profile.skills = [
        {'skill': row.skill.canonical_name, 'level': row.declared_proficiency}
        for row in member.employee_skills.select_related('skill').order_by('skill__canonical_name')
    ]
    profile.save(update_fields=['skills', 'updated_at'])


def reflect_task_requirements(task):
    task.required_skills = [
        {'skill': row.skill.canonical_name, 'priority': row.requirement_type,
         'min_level': row.minimum_proficiency}
        for row in task.skill_requirements.select_related('skill').order_by('skill__canonical_name')
    ]
    task.save(update_fields=['required_skills', 'updated_at'])


def propose_task_evidence(task):
    """Task requirements only propose evidence; nobody gains observed proficiency yet."""
    requirements = list(TaskSkillRequirement.objects.filter(task=task).select_related('skill'))
    # ponytail: latest assignment is treated as the contributor; store a completion actor if handoffs become common.
    assignments = task.assignments.order_by('-created_at', '-id')[:1]
    for assignment in assignments:
        for requirement in requirements:
            SkillEvidence.objects.get_or_create(
                member=assignment.member, task=task, skill=requirement.skill,
                defaults={
                    'usage_level': 'SUPPORTING' if requirement.requirement_type == 'PREFERRED' else 'PRIMARY',
                    'task_complexity': task.complexity,
                    'context_tags': task.completion_evidence.factors,
                },
            )


def evaluate_evidence(records):
    """Conservative one-year heuristic. Contextual delays never count as a penalty."""
    records = [r for r in records if r.confirmed_by_employee
               and r.created_at >= timezone.now() - timedelta(days=365)]
    records.sort(key=lambda r: r.created_at, reverse=True)
    primary = [r for r in records if r.usage_level == 'PRIMARY']
    strong = [r for r in primary if r.task_complexity == 'HIGH']
    contexts = {str(tag) for r in records for tag in r.context_tags}
    observed = ('UNKNOWN' if not records else
                'ADVANCED' if len(strong) >= 2 and len({r.task_id for r in strong}) >= 2
                else 'INTERMEDIATE' if primary else 'BEGINNER')
    confidence = ('HIGH' if len(primary) >= 3 and len(contexts) >= 2
                  else 'MEDIUM' if len(records) >= 2 else 'LOW')
    return {'observed_proficiency': observed, 'evidence_confidence': confidence,
            'evidence_count': len(records), 'strong_evidence_count': len(strong),
            'context_diversity': len(contexts),
            'last_evidence_at': records[0].created_at if records else None}


@transaction.atomic
def confirm_evidence(evidence):
    if evidence.confirmed_by_employee:
        return evidence
    evidence.confirmed_by_employee = True
    evidence.save(update_fields=['confirmed_by_employee'])
    records = SkillEvidence.objects.filter(member=evidence.member, skill=evidence.skill,
                                           confirmed_by_employee=True)
    result = evaluate_evidence(list(records))
    skill, _ = EmployeeSkill.objects.get_or_create(member=evidence.member, skill=evidence.skill,
                                                    defaults={'declared_proficiency': 'BEGINNER'})
    skill.observed_proficiency = result['observed_proficiency']
    skill.evidence_confidence = result['evidence_confidence']
    skill.last_evidence_at = result['last_evidence_at'] or evidence.created_at
    skill.save(update_fields=['observed_proficiency', 'evidence_confidence', 'last_evidence_at'])
    return evidence
