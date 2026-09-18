from rest_framework import viewsets
from adaptive.models import AdaptiveAnalysis
from adaptive.serializers import AdaptiveAnalysisSerializer


class AdaptiveAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AdaptiveAnalysis.objects.all()
    serializer_class = AdaptiveAnalysisSerializer
