from django.contrib import admin
from adaptive.models import AdaptiveAnalysis, EmployeeSkill, Skill, SkillEvidence, TaskSkillRequirement

admin.site.register(AdaptiveAnalysis)
admin.site.register([Skill, EmployeeSkill, TaskSkillRequirement, SkillEvidence])
