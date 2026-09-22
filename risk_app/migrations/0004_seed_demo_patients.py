from django.db import migrations

DEMO_PATIENTS = [
    ("Amina Mohammed", "+254 700 111 222"),
    ("Grace Wanjiru", "+254 700 222 333"),
    ("Fatuma Hassan", "+254 700 333 444"),
    ("Naliaka Wafula", ""),
]


def link_demo_patients(apps, schema_editor):
    Patient = apps.get_model("risk_app", "Patient")
    PredictionRecord = apps.get_model("risk_app", "PredictionRecord")

    demo_records = list(PredictionRecord.objects.filter(user__isnull=True).order_by("created_at"))
    if not demo_records:
        return

    patients = []
    for i, (name, phone) in enumerate(DEMO_PATIENTS):
        patients.append(Patient.objects.create(
            patient_id=f"PT-{i + 1:05d}",
            full_name=name,
            phone_number=phone,
        ))

    # Link the two most recent demo predictions (the High-risk ones) to the
    # first two demo patients, so the Alerts page has something to show.
    for record, patient in zip(demo_records, patients):
        record.patient = patient
        record.save(update_fields=["patient"])


def unlink_demo_patients(apps, schema_editor):
    Patient = apps.get_model("risk_app", "Patient")
    Patient.objects.filter(patient_id__in=[f"PT-{i+1:05d}" for i in range(len(DEMO_PATIENTS))]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("risk_app", "0003_patient_predictionrecord_patient"),
    ]

    operations = [
        migrations.RunPython(link_demo_patients, unlink_demo_patients),
    ]
