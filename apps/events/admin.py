from django.contrib import admin

from apps.core.utils import export_as_csv_action

from .models import Event, EventRegistration


class RegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    fields = ["full_name", "phone", "email", "attendees", "attended"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "start", "venue", "registered", "is_published"]
    list_filter = ["kind", "focus_area", "is_published", "registration_open"]
    search_fields = ["title", "venue"]
    prepopulated_fields = {"slug": ["title"]}
    date_hierarchy = "start"
    inlines = [RegistrationInline]

    @admin.display(description="Registered")
    def registered(self, obj):
        return obj.registrations.count()


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ["full_name", "phone", "event", "attendees", "attended", "created_at"]
    list_filter = ["event", "attended"]
    list_editable = ["attended"]
    search_fields = ["full_name", "phone", "email"]
    actions = [export_as_csv_action()]
