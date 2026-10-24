from django.contrib import admin
from django.db.models import Sum

from apps.core.utils import export_as_csv_action

from .models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ["reference", "donor_name", "amount", "method", "status", "designation_display", "mpesa_receipt", "created_at"]
    list_filter = ["status", "method", "frequency", "project", "focus_area", "created_at"]
    search_fields = ["reference", "donor_name", "phone", "email", "mpesa_receipt"]
    date_hierarchy = "created_at"
    readonly_fields = ["reference", "merchant_request_id", "checkout_request_id", "raw_callback", "completed_at", "created_at"]
    actions = [export_as_csv_action(), "mark_completed"]

    @admin.display(description="For")
    def designation_display(self, obj):
        return obj.designation

    @admin.action(description="Mark selected as completed (bank / cash received)")
    def mark_completed(self, request, queryset):
        n = 0
        for d in queryset.exclude(status="completed"):
            d.status = "completed"
            d.save()
            n += 1
        self.message_user(request, f"{n} donation(s) marked completed.")

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data["cl"].queryset
            total = qs.filter(status="completed").aggregate(t=Sum("amount"))["t"] or 0
            response.context_data["title"] = f"Donations — completed in this view: KES {total:,.0f}"
        except (AttributeError, KeyError):
            pass
        return response
