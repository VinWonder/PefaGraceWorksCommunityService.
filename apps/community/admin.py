from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from apps.core.utils import export_as_csv_action

from .models import (Beneficiary, ContactMessage, Feedback, HelpRequest, NewsletterSubscriber, PartnershipInquiry,
                     VolunteerApplication)

csv_action = export_as_csv_action()


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["subject", "name", "email", "phone", "created_at", "is_handled"]
    list_filter = ["is_handled", "created_at"]
    list_editable = ["is_handled"]
    search_fields = ["name", "email", "subject", "message"]
    actions = [csv_action]


@admin.register(VolunteerApplication)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ["full_name", "phone", "location", "availability", "status", "created_at"]
    list_filter = ["status", "availability", "focus_areas"]
    list_editable = ["status"]
    search_fields = ["full_name", "email", "phone", "skills"]
    filter_horizontal = ["focus_areas"]
    actions = [csv_action]


@admin.register(PartnershipInquiry)
class PartnershipAdmin(admin.ModelAdmin):
    list_display = ["organisation", "contact_person", "partner_type", "status", "created_at"]
    list_filter = ["partner_type", "status"]
    list_editable = ["status"]
    search_fields = ["organisation", "contact_person", "email"]
    actions = [csv_action]


@admin.register(NewsletterSubscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "name", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["email", "name"]
    actions = [csv_action]


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["reference", "kind", "status", "focus_area", "created_at", "sla"]
    list_filter = ["kind", "status", "focus_area"]
    search_fields = ["reference", "name", "phone", "message"]
    readonly_fields = ["reference", "acknowledge_by", "resolve_by", "acknowledged_at", "resolved_at", "created_at"]
    actions = [csv_action]

    @admin.display(description="Service charter")
    def sla(self, obj):
        if obj.status == "resolved":
            ok = obj.met_charter
            return format_html('<b style="color:{}">{}</b>', "green" if ok else "#b45309", "Met" if ok else "Late")
        if obj.ack_overdue:
            return format_html('<b style="color:#b91c1c">Acknowledgement overdue</b>')
        if obj.resolution_overdue:
            return format_html('<b style="color:#b91c1c">Resolution overdue</b>')
        days = (obj.resolve_by - timezone.localdate()).days if obj.resolve_by else 0
        return f"{days} day(s) left"


class PriorityFilter(admin.SimpleListFilter):
    title = "priority"
    parameter_name = "priority"

    def lookups(self, request, model_admin):
        return [("high", "High (60+)"), ("medium", "Medium (35–59)"), ("low", "Low (<35)")]

    def queryset(self, request, qs):
        if self.value() == "high":
            return qs.filter(priority_score__gte=60)
        if self.value() == "medium":
            return qs.filter(priority_score__gte=35, priority_score__lt=60)
        if self.value() == "low":
            return qs.filter(priority_score__lt=35)
        return qs


@admin.register(HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ["reference", "full_name", "need_type", "urgency", "score", "status", "location", "created_at"]
    list_filter = [PriorityFilter, "status", "need_type", "urgency", "ward"]
    list_editable = ["status"]
    search_fields = ["reference", "full_name", "phone", "location"]
    readonly_fields = ["reference", "priority_score", "created_at"]
    actions = [csv_action, "create_beneficiaries"]

    @admin.display(description="Priority", ordering="priority_score")
    def score(self, obj):
        colour = {"High": "#b91c1c", "Medium": "#b45309", "Low": "#475569"}[obj.priority_band]
        return format_html('<b style="color:{}">{} · {}</b>', colour, obj.priority_score, obj.priority_band)

    @admin.action(description="Register selected as beneficiaries (marks them assisted)")
    def create_beneficiaries(self, request, queryset):
        from apps.programs.models import FocusArea

        need_map = {"school_fees": ("education", "school_fees"), "sanitary": ("education", "sanitary"),
                    "food": ("faith-and-outreach", "food"), "medical": ("health", "medical"),
                    "water": ("water-and-sanitation", "water"), "skills": ("economic-empowerment", "skills"),
                    "counseling": ("faith-and-outreach", "counseling"), "other": ("faith-and-outreach", "other")}
        created = 0
        for hr in queryset:
            slug, support = need_map.get(hr.need_type, ("faith-and-outreach", "other"))
            area = FocusArea.objects.filter(slug=slug).first() or FocusArea.objects.first()
            if not area or Beneficiary.objects.filter(help_request=hr).exists():
                continue
            Beneficiary.objects.create(full_name=hr.full_name, gender="other", phone=hr.phone, location=hr.location,
                                       ward=hr.ward, focus_area=area, support_type=support, help_request=hr,
                                       has_disability=hr.has_disability)
            hr.status = "assisted"
            hr.save()
            created += 1
        self.message_user(request, f"{created} beneficiary record(s) created. Open each one to add gender, school and amount.")


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ["full_name", "gender", "focus_area", "support_type", "level", "school", "amount_supported", "start_date", "is_active"]
    list_filter = ["focus_area", "support_type", "gender", "level", "is_active", "ward", "project"]
    search_fields = ["full_name", "phone", "school", "guardian_name"]
    date_hierarchy = "start_date"
    raw_id_fields = ["help_request"]
    actions = [csv_action]
