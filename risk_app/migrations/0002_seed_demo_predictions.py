from django.db import migrations
from datetime import timedelta
from django.utils import timezone
import random


DEMO_ROWS = [
    # age, gest_weeks, eclampsia, haemorrhage, risk_level, prob_low, prob_med, prob_high, days_ago
    (24, 32, "None", "None", "Low", 92.0, 6.5, 1.5, 0),
    (29, 28, "None", "None", "Low", 88.0, 10.0, 2.0, 0),
    (36, 34, "Mild pre-eclampsia", "None", "Medium", 20.0, 68.0, 12.0, 1),
    (41, 36, "Severe pre-eclampsia", "Moderate", "High", 4.0, 21.0, 75.0, 1),
    (19, 30, "None", "None", "Medium", 35.0, 55.0, 10.0, 2),
    (27, 38, "None", "Mild", "Low", 70.0, 25.0, 5.0, 3),
    (33, 26, "None", "None", "Low", 90.0, 8.0, 2.0, 4),
    (44, 33, "Eclampsia", "Severe", "High", 1.0, 8.0, 91.0, 5),
]


def seed_demo_predictions(apps, schema_editor):
    PredictionRecord = apps.get_model("risk_app", "PredictionRecord")
    now = timezone.now()
    for age, gw, ecl, haem, risk, plow, pmed, phigh, days_ago in DEMO_ROWS:
        obj = PredictionRecord.objects.create(
            user=None,
            age=age,
            gestational_age_weeks=gw,
            eclampsia_severity=ecl,
            haemorrhage_severity=haem,
            risk_level=risk,
            prob_low=plow,
            prob_medium=pmed,
            prob_high=phigh,
            model_backend="sklearn",
        )
        # auto_now_add ignores any created_at passed to create(), so backdate it
        # with a separate update -- that's allowed since auto_now_add only
        # fires on INSERT, not on later UPDATEs.
        backdated = now - timedelta(days=days_ago, hours=random.randint(0, 20))
        PredictionRecord.objects.filter(pk=obj.pk).update(created_at=backdated)


def remove_demo_predictions(apps, schema_editor):
    PredictionRecord = apps.get_model("risk_app", "PredictionRecord")
    PredictionRecord.objects.filter(user__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("risk_app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_predictions, remove_demo_predictions),
    ]
