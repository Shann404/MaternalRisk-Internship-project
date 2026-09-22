from django.db import models
from django.conf import settings


class Patient(models.Model):
    """A registered patient the hospital tracks over multiple visits/predictions."""
    patient_id = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    date_registered = models.DateTimeField(auto_now_add=True)
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="patients_registered",
    )

    class Meta:
        ordering = ["-date_registered"]

    def save(self, *args, **kwargs):
        if not self.patient_id:
            last = Patient.objects.order_by("-id").first()
            next_num = (last.id + 1) if last else 1
            self.patient_id = f"PT-{next_num:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} - {self.full_name}"

    @property
    def latest_prediction(self):
        return self.predictions.order_by("-created_at").first()


class PredictionRecord(models.Model):
    RISK_CHOICES = [("Low", "Low"), ("Medium", "Medium"), ("High", "High")]

    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    patient = models.ForeignKey(
        Patient, null=True, blank=True, on_delete=models.SET_NULL, related_name="predictions"
    )

    # Key inputs, kept for the "Recent Predictions" table
    age = models.IntegerField()
    gestational_age_weeks = models.IntegerField()
    eclampsia_severity = models.CharField(max_length=30)
    haemorrhage_severity = models.CharField(max_length=30)

    # Result
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES)
    prob_low = models.FloatField()
    prob_medium = models.FloatField()
    prob_high = models.FloatField()
    model_backend = models.CharField(max_length=20, default="sklearn")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} - {self.risk_level}"
