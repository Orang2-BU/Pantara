from rest_framework import serializers
from adaptive.models import AdaptiveAnalysis


class AdaptiveAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptiveAnalysis
        fields = ['id', 'task', 'candidates', 'recommendation', 'evidence', 'workload_impact', 'created_at']
        read_only_fields = ['id', 'created_at']
