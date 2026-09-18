from django.db import migrations


ALIASES = {
    'react': ['reactjs', 'react.js', 'react-js'],
    'typescript': ['ts'],
    'python': ['py'],
}


def seed_catalog(apps, schema_editor):
    Skill = apps.get_model('adaptive', 'Skill')
    EmployeeSkill = apps.get_model('adaptive', 'EmployeeSkill')
    TaskSkillRequirement = apps.get_model('adaptive', 'TaskSkillRequirement')
    WorkProfile = apps.get_model('core', 'WorkProfile')
    Task = apps.get_model('work', 'Task')
    known = set(ALIASES) | {'django', 'system design', 'architecture', 'rest api', 'algorithm',
                            'postgresql', 'react', 'typescript', 'tailwind', 'ui/ux'}
    for profile in WorkProfile.objects.all():
        for entry in profile.skills or []:
            name = entry if isinstance(entry, str) else entry.get('skill') if isinstance(entry, dict) else None
            if name:
                known.add(name.casefold().strip())
    for task in Task.objects.all():
        for entry in task.required_skills or []:
            name = entry if isinstance(entry, str) else entry.get('skill') if isinstance(entry, dict) else None
            if name:
                known.add(name.casefold().strip())
    alias_lookup = {alias: key for key, aliases in ALIASES.items() for alias in aliases}
    catalog = {}
    for name in sorted(known):
        canonical = alias_lookup.get(name, name)
        if canonical not in catalog:
            catalog[canonical] = Skill.objects.create(canonical_name=canonical, aliases=ALIASES.get(canonical, []))
    for profile in WorkProfile.objects.all():
        for entry in profile.skills or []:
            name = entry if isinstance(entry, str) else entry.get('skill') if isinstance(entry, dict) else None
            if name:
                level = entry.get('level', 'INTERMEDIATE') if isinstance(entry, dict) else 'INTERMEDIATE'
                EmployeeSkill.objects.get_or_create(member_id=profile.member_id,
                    skill=catalog[alias_lookup.get(name.casefold().strip(), name.casefold().strip())],
                    defaults={'declared_proficiency': str(level).upper()})
    for task in Task.objects.all():
        for entry in task.required_skills or []:
            name = entry if isinstance(entry, str) else entry.get('skill') if isinstance(entry, dict) else None
            if name:
                TaskSkillRequirement.objects.get_or_create(task_id=task.id,
                    skill=catalog[alias_lookup.get(name.casefold().strip(), name.casefold().strip())],
                    defaults={
                        'requirement_type': str(entry.get('priority', 'REQUIRED')).upper() if isinstance(entry, dict) else 'REQUIRED',
                        'minimum_proficiency': str(entry.get('min_level', 'INTERMEDIATE')).upper() if isinstance(entry, dict) else 'INTERMEDIATE',
                    })


class Migration(migrations.Migration):
    dependencies = [('adaptive', '0002_skill_employeeskill_skillevidence_and_more')]
    operations = [migrations.RunPython(seed_catalog, migrations.RunPython.noop)]
