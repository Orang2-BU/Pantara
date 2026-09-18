from django.contrib import admin
from work.models import Project, Task, Assignment, Blocker, CompletionEvidence

admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Assignment)
admin.site.register(Blocker)
admin.site.register(CompletionEvidence)
