from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core.views import (
    WorkspaceViewSet,
    TeamViewSet,
    MemberViewSet,
    WorkProfileViewSet,
    CapacitySignalViewSet,
)
from work.views import (
    ProjectViewSet,
    TaskViewSet,
    AssignmentViewSet,
    BlockerViewSet,
    CompletionEvidenceViewSet,
)
from adaptive.views import AdaptiveAnalysisViewSet

router = DefaultRouter()
router.register(r'workspaces', WorkspaceViewSet)
router.register(r'teams', TeamViewSet)
router.register(r'members', MemberViewSet)
router.register(r'work-profiles', WorkProfileViewSet)
router.register(r'capacity-signals', CapacitySignalViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'assignments', AssignmentViewSet)
router.register(r'blockers', BlockerViewSet)
router.register(r'completion-evidences', CompletionEvidenceViewSet)
router.register(r'adaptive-analyses', AdaptiveAnalysisViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),

    # OpenAPI 3.0 Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
