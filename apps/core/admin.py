from django.contrib import admin
from django.utils.html import format_html

from .models import FAQ, CoreValue, HeroSlide, ImpactStat, Milestone, Partner, Person, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Identity", {"fields": ["org_name", "short_name", "tagline", "closing_statement"]}),
        ("Who we are", {"fields": ["vision", "mission", "about_short", "about_long", "legal_status"]}),
        ("Church block (home page)", {"fields": ["church_block_title", "church_block_text", "church_block_image"]}),
        ("Registration", {"fields": ["registration_number", "registration_date", "registered_under", "affiliation"]}),
        ("Contact", {"fields": ["phone", "whatsapp", "email", "po_box", "address", "physical_location", "office_hours", "map_embed_url"]}),
        ("Social media", {"fields": ["facebook", "x_twitter", "instagram", "youtube", "linkedin", "tiktok"]}),
        ("Giving", {"fields": ["mpesa_paybill", "mpesa_account", "bank_details"]}),
        ("Service charter targets", {"fields": ["feedback_ack_hours", "feedback_resolve_working_days"]}),
    ]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ["preview", "title", "order", "is_active"]
    list_editable = ["order", "is_active"]
    list_display_links = ["preview", "title"]

    @admin.display(description="Image")
    def preview(self, obj):
        return format_html('<img src="{}" style="height:48px;border-radius:4px">', obj.image.url) if obj.image else "—"


@admin.register(CoreValue)
class CoreValueAdmin(admin.ModelAdmin):
    list_display = ["title", "icon", "order"]
    list_editable = ["order"]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["role", "name", "group", "order", "is_active"]
    list_filter = ["group", "is_active"]
    list_editable = ["order", "is_active"]
    search_fields = ["name", "role"]


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "order", "is_active"]
    list_filter = ["category", "is_active"]
    list_editable = ["order", "is_active"]
    search_fields = ["name"]


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ["title", "focus_area", "date", "order"]
    list_editable = ["order"]
    list_filter = ["focus_area"]


@admin.register(ImpactStat)
class ImpactStatAdmin(admin.ModelAdmin):
    list_display = ["label", "source", "manual_value", "minimum_value", "current_value", "order", "is_active"]
    list_editable = ["order", "is_active"]

    @admin.display(description="Shown on site")
    def current_value(self, obj):
        return f"{obj.value}{obj.suffix}"


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ["question", "order", "is_active"]
    list_editable = ["order", "is_active"]
