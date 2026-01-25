from django.contrib import admin
from .models import (
    Supervisor,
    EvaluationRequest,
    Evaluation,
)
from django.urls import reverse
from django.utils.html import format_html




@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    readonly_fields = (
        "evaluation_request",
        "rating",
        "comment",
        "submitted_at",
        "ip_address",
        "user_agent",
        "signature",
        "pdf_link",
    )

    list_display = ("id", "submitted_at")

    def has_change_permission(self, request, obj = None):
        return False
    
    def pdf_link(self, obj):
        url = reverse("evaluation_pdf", args=[obj.id])
        return format_html('<a href="{}">PDF herunterladen</a>', url)

    pdf_link.short_description = "PDF"

admin.site.register(Supervisor)

@admin.register(EvaluationRequest)
class EvaluationRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "person",
        "supervisor",
        "expires_at",
        "is_used",
        "token",
    )

    readonly_fields = ("token",)




