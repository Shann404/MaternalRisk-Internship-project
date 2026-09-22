from .models import Patient


def alerts_count(request):
    if not request.user.is_authenticated:
        return {}
    count = 0
    for patient in Patient.objects.all():
        latest = patient.latest_prediction
        if latest and latest.risk_level == "High":
            count += 1
    return {"high_risk_alert_count": count}
