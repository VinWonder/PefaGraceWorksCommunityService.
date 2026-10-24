from rest_framework import serializers

from apps.events.models import Event
from apps.news.models import Post
from apps.programs.models import FocusArea, Project


class FocusAreaSerializer(serializers.ModelSerializer):
    activities = serializers.SerializerMethodField()
    outcomes = serializers.SerializerMethodField()

    class Meta:
        model = FocusArea
        fields = ["id", "title", "slug", "icon", "summary", "goal", "activities", "outcomes"]

    def get_activities(self, obj):
        return [i.text for i in obj.items.all() if i.kind == "activity"]

    def get_outcomes(self, obj):
        return [i.text for i in obj.items.all() if i.kind == "outcome"]


class ProjectSerializer(serializers.ModelSerializer):
    focus_area = serializers.StringRelatedField()
    amount_raised = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "title", "slug", "focus_area", "status", "summary", "target_outcome", "funding_goal",
                  "amount_raised", "progress_percent", "start_date", "end_date"]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ["id", "title", "slug", "kind", "summary", "start", "end", "venue", "address"]


class PostSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Post
        fields = ["id", "title", "slug", "category", "summary", "published_at"]
