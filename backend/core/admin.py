from django.contrib import admin
from core.models import Workspace, Team, Member, WorkProfile, CapacitySignal

admin.site.register(Workspace)
admin.site.register(Team)
admin.site.register(Member)
admin.site.register(WorkProfile)
admin.site.register(CapacitySignal)
