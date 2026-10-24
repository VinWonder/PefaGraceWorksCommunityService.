from django.contrib import admin

from apps.core.utils import export_as_csv_action

from .models import (FocusArea, FocusAreaItem, ImplementationStage, Indicator, IndicatorMeasurement, Project,
                     ProjectUpdate, ServiceStandard)


class FocusAreaItemInline(admin.TabularInline):
    model = FocusAreaItem
    extra = 1


class ServiceStandardInline(admin.StackedInline):
    model = ServiceStandard
    extra = 0


@admin.register(FocusArea)
class FocusAreaAdmin(admin.ModelAdmin):
    list_display = ["title", "icon", "order", "is_active"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"slug": ["title"]}
    inlines = [FocusAreaItemInline, ServiceStandardInline]


class ProjectUpdateInline(admin.StackedInline):
    model = ProjectUpdate
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "focus_area", "status", "funding_goal", "raised", "progress", "is_featured"]
    list_filter = ["status", "focus_area", "is_featured"]
    list_editable = ["status", "is_featured"]
    search_fields = ["title", "summary"]
    prepopulated_fields = {"slug": ["title"]}
    inlines = [ProjectUpdateInline]

    @admin.display(description="Raised (KES)")
    def raised(self, obj):
        return f"{obj.amount_raised:,.0f}"

    @admin.display(description="%")
    def progress(self, obj):
        return f"{obj.progress_percent}%"


@admin.register(ImplementationStage)
class ImplementationStageAdmin(admin.ModelAdmin):
    list_display = ["title", "order"]
    list_editable = ["order"]


class MeasurementInline(admin.TabularInline):
    model = IndicatorMeasurement
    extra = 1


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ["name", "focus_area", "baseline", "target", "target_year", "current", "progress", "is_public"]
    list_filter = ["focus_area", "target_year", "is_public"]
    search_fields = ["name"]
    inlines = [MeasurementInline]
    actions = [export_as_csv_action()]

    @admin.display(description="Current")
    def current(self, obj):
        return obj.current_value

    @admin.display(description="Progress")
    def progress(self, obj):
        return f"{obj.progress_percent}%"
