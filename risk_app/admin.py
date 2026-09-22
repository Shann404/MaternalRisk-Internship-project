from django.contrib import admin
from .models import PredictionRecord, Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "full_name", "phone_number", "date_registered", "registered_by")
    search_fields = ("patient_id", "full_name", "phone_number")
    ordering = ("-date_registered",)


@admin.register(PredictionRecord)
class PredictionRecordAdmin(admin.ModelAdmin):
    list_display = ("created_at", "patient", "user", "age", "gestational_age_weeks", "risk_level", "model_backend")
    list_filter = ("risk_level", "model_backend")
    ordering = ("-created_at",)
