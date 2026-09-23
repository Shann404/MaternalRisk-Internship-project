import os
import csv
import joblib
import pandas as pd
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

from .forms import PatientRiskForm, RegisterForm, PatientForm
from .models import PredictionRecord, Patient

# ---------------------------------------------------------------------------
# MODEL LOADING
# ---------------------------------------------------------------------------
# Two supported backends:
#
#   1. CatBoost (.cbm) -- DROP YOUR TRAINED MODEL FILE HERE:
#        risk_app/ml/model.cbm
#      CatBoost handles categorical columns natively (no OneHot/Ordinal
#      encoding needed), so if this file is present we skip the sklearn
#      preprocessor entirely and feed it the raw feature values directly,
#      passing CAT_FEATURE_NAMES so it knows which columns are categorical.
#
#   2. sklearn fallback (risk_model.joblib + preprocessor.joblib) -- the
#      Gradient Boosting model from prepare_maternal_risk_data.py, used
#      automatically if no .cbm file has been added yet, so the app still
#      runs out of the box.
#
# Whichever backend is active, PREDICT_FN(X_row_dataframe) -> (risk_level, probabilities)
# is what the views below call, so nothing else in this file needs to change
# once you drop in your .cbm file.

ML_DIR = os.path.join(settings.BASE_DIR, "risk_app", "ml")

MODEL_PATH = os.path.join(
    ML_DIR,
    "gradient_boosting_model.joblib"
)

PREPROCESSOR_PATH = os.path.join(
    ML_DIR,
    "preprocessor.joblib"
)

META_PATH = os.path.join(
    ML_DIR,
    "model_metadata.joblib"
)

# Load metadata
META = joblib.load(META_PATH)

TARGET_ORDER = META["target_order"]
# ["Low", "Medium", "High"]

# Load Gradient Boosting model
SKLEARN_MODEL = joblib.load(MODEL_PATH)

# Load fitted preprocessing pipeline
PREPROCESSOR = joblib.load(PREPROCESSOR_PATH)

MODEL_BACKEND = "sklearn"

print(f"[risk_app] Loaded Gradient Boosting model from {MODEL_PATH}")
print(f"[risk_app] Loaded preprocessor from {PREPROCESSOR_PATH}")



RISK_COLORS = {"Low": "#3ddc84", "Medium": "#f1c94a", "High": "#e05252"}


def get_feature_importance_list(top_n=8):
    """
    Returns the top features used by the Gradient Boosting model.
    """

    names = PREPROCESSOR.get_feature_names_out()
    names = [n.split("__")[-1] for n in names]

    importances = SKLEARN_MODEL.feature_importances_

    pairs = sorted(
        zip(names, importances),
        key=lambda x: -x[1]
    )[:top_n]

    total = sum(v for _, v in pairs) or 1

    return [
        {
            "name": n.replace("_", " "),
            "pct": round(v / total * 100, 1)
        }
        for n, v in pairs
    ]


FEATURE_IMPORTANCE_LIST = get_feature_importance_list()



def build_feature_row(form):
    """Turn cleaned form data into the single-row DataFrame the model expects
    (raw categorical values -- encoding, if needed, happens per-backend below)."""
    d = form.cleaned_data
    row = {
        "Age": d["age"],
        "Age_Risk_Flag": 1 if (d["age"] < 18 or d["age"] > 35) else 0,
        "Gravida": d["gravida"],
        "Parity": d["parity"],
        "Previous_C_Section": d["previous_c_section"],
        "Previous_Stillbirth_Miscarriage": d["previous_stillbirth_miscarriage"],
        "Interval_Since_Last_Pregnancy_Months": d["interval_since_last_pregnancy_months"],
        "Gestational_Age_Weeks": d["gestational_age_weeks"],
        "ANC_Visits_Count": d["anc_visits_count"],
        "First_ANC_Visit_Week": d["first_anc_visit_week"],
        "Multiple_Gestation": d["multiple_gestation"],
        "Fetal_Presentation": d["fetal_presentation"],
        "BMI": d["bmi"],
        "Pulse": d["pulse"],
        "Systolic": d["systolic"],
        "Diastolic": d["diastolic"],
        "Weight (kg)": d["weight_kg"],
        "Prepregnancy_Weight_kg": d["prepregnancy_weight_kg"],
        "Weight_Gain_kg": d["weight_kg"] - d["prepregnancy_weight_kg"],
        "Fundal_Height_cm": d["fundal_height_cm"],
        "Fetal_Heart_Rate_bpm": d["fetal_heart_rate_bpm"],
        "Hemoglobin_g_dL": d["hemoglobin_g_dl"],
        "Anaemia_Severity": d["anaemia_severity"],
        "Blood_Glucose_mg_dL": d["blood_glucose_mg_dl"],
        "Diabetes_Severity": d["diabetes_severity"],
        "Urine_Protein": d["urine_protein"],
        "Eclampsia_Severity": d["eclampsia_severity"],
        "Haemorrhage_Severity": d["haemorrhage_severity"],
        "UTI_Severity": d["uti_severity"],
        "Liver_Disorder_Severity": d["liver_disorder_severity"],
        "Blood_Group": d["blood_group"],
        "Rh_Factor": d["rh_factor"],
        "HIV_Status": d["hiv_status"],
        "Syphilis_Status": d["syphilis_status"],
        "Vomiting": d["vomiting"],
        "Education_Level": d["education_level"],
        "Distance_To_Facility_km": d["distance_to_facility_km"],
        "Substance_Use": d["substance_use"],
        "Socioeconomic_Index": d["socioeconomic_index"],
    }
    return pd.DataFrame([row])[META["feature_cols"]]


def run_prediction(patient_df):
    """
    Run the trained Gradient Boosting model on a single patient row.
    patient_df must already be a 2-D pandas DataFrame.
    """

    # Make sure the columns are in exactly the same order
    # used when the model was trained.
    feature_cols = META["feature_cols"]
    patient_df = patient_df.reindex(columns=feature_cols).copy()

    # Match the binary conversions used during model training
    binary_yes_no = [
        "Previous_C_Section",
        "Previous_Stillbirth_Miscarriage",
        "Multiple_Gestation",
        "Substance_Use",
        "Vomiting",
    ]

    for c in binary_yes_no:
        if c in patient_df.columns:
            patient_df[c] = (patient_df[c] == "Yes").astype(int)

    binary_pos_neg = [
        "HIV_Status",
        "Syphilis_Status",
        "Rh_Factor",
    ]

    for c in binary_pos_neg:
        if c in patient_df.columns:
            patient_df[c] = (patient_df[c] == "Positive").astype(int)

    # Apply the fitted preprocessing used during training
    X_processed = PREPROCESSOR.transform(patient_df)

    # Generate prediction
    prediction = SKLEARN_MODEL.predict(X_processed)[0]

    # Generate class probabilities
    probabilities_raw = SKLEARN_MODEL.predict_proba(X_processed)[0]

    # Convert numeric prediction back to Low / Medium / High
    risk_level = TARGET_ORDER[int(prediction)]

    # Format probabilities for the template and database
    probabilities = [
        {
            "label": TARGET_ORDER[i],
            "pct": round(float(probabilities_raw[i]) * 100, 2),
        }
        for i in range(len(TARGET_ORDER))
    ]

    return risk_level, probabilities

@login_required
def predict_view(request):
    result = None
    preselected_patient = request.GET.get("patient")

    if request.method == "POST":
        form = PatientRiskForm(request.POST)
        if form.is_valid():
            X_raw = build_feature_row(form)
            risk_level, probabilities = run_prediction(X_raw)
            result = {
                "risk_level": risk_level,
                "color": RISK_COLORS[risk_level],
                "probabilities": probabilities,
            }

            prob_by_label = {p["label"]: p["pct"] for p in probabilities}
            PredictionRecord.objects.create(
                user=request.user,
                patient=form.cleaned_data.get("patient"),
                age=form.cleaned_data["age"],
                gestational_age_weeks=form.cleaned_data["gestational_age_weeks"],
                eclampsia_severity=form.cleaned_data["eclampsia_severity"],
                haemorrhage_severity=form.cleaned_data["haemorrhage_severity"],
                risk_level=risk_level,
                prob_low=prob_by_label.get("Low", 0),
                prob_medium=prob_by_label.get("Medium", 0),
                prob_high=prob_by_label.get("High", 0),
                model_backend=MODEL_BACKEND,
            )
    else:
        initial = {}
        if preselected_patient:
            initial["patient"] = preselected_patient
        form = PatientRiskForm(initial=initial)

    return render(request, "risk_app/predict.html",
                  {"form": form, "result": result, "model_backend": MODEL_BACKEND})


@login_required
def dashboard_view(request):
    records = PredictionRecord.objects.all()
    total = records.count()

    risk_counts = {label: records.filter(risk_level=label).count() for label in ["Low", "Medium", "High"]}
    risk_pcts = {label: round(count / total * 100, 1) if total else 0 for label, count in risk_counts.items()}

    today = timezone.now().date()
    predictions_today = records.filter(created_at__date=today).count()

    # Last 7 days, oldest first, for the bar chart
    day_labels, day_counts = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_labels.append(day.strftime("%a"))
        day_counts.append(records.filter(created_at__date=day).count())
    max_day_count = max(day_counts) if max(day_counts, default=0) else 1

    daily_bars = [
        {"label": label, "count": count, "height_pct": round(count / max_day_count * 100) if max_day_count else 0}
        for label, count in zip(day_labels, day_counts)
    ]

    recent = records.select_related("user", "patient")[:8]
    total_patients = Patient.objects.count()
    high_risk_patients = sum(
        1 for pt in Patient.objects.all()
        if pt.latest_prediction and pt.latest_prediction.risk_level == "High"
    )

    context = {
        "model_backend": MODEL_BACKEND,
        "total": total,
        "predictions_today": predictions_today,
        "risk_counts": risk_counts,
        "risk_pcts": risk_pcts,
        "daily_bars": daily_bars,
        "recent": recent,
        "feature_importance": FEATURE_IMPORTANCE_LIST,
        "total_patients": total_patients,
        "high_risk_patients": high_risk_patients,
    }
    return render(request, "risk_app/dashboard.html", context)


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("risk_app:dashboard")
    else:
        form = RegisterForm()
    return render(request, "risk_app/register.html", {"form": form})


# ---------------------------------------------------------------------------
# PATIENT RECORDS
# ---------------------------------------------------------------------------

@login_required
def patients_list_view(request):
    query = request.GET.get("q", "").strip()
    patients = Patient.objects.all()
    if query:
        patients = patients.filter(full_name__icontains=query) | patients.filter(patient_id__icontains=query)

    rows = []
    for patient in patients:
        latest = patient.latest_prediction
        rows.append({"patient": patient, "latest": latest})

    return render(request, "risk_app/patients_list.html", {"rows": rows, "query": query})


@login_required
def patient_register_view(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.registered_by = request.user
            patient.save()
            return redirect("risk_app:patient_detail", pk=patient.pk)
    else:
        form = PatientForm()
    return render(request, "risk_app/patient_form.html", {"form": form})


@login_required
def patient_detail_view(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    predictions = patient.predictions.all()
    return render(request, "risk_app/patient_detail.html", {"patient": patient, "predictions": predictions})


@login_required
def alerts_view(request):
    """Patients whose most recent prediction is High risk, most recent first."""
    flagged = []
    for patient in Patient.objects.all():
        latest = patient.latest_prediction
        if latest and latest.risk_level == "High":
            flagged.append((patient, latest))
    flagged.sort(key=lambda pair: pair[1].created_at, reverse=True)
    return render(request, "risk_app/alerts.html", {"flagged": flagged})


@login_required
def export_patients_csv(request):
    """Downloadable CSV of every patient and their latest risk status, for handing to hospital management."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="patient_risk_report.csv"'
    writer = csv.writer(response)
    writer.writerow(["Patient ID", "Full Name", "Phone Number", "Date Registered",
                      "Latest Risk Level", "Latest Prediction Date", "Total Predictions"])
    for patient in Patient.objects.all():
        latest = patient.latest_prediction
        writer.writerow([
            patient.patient_id,
            patient.full_name,
            patient.phone_number,
            patient.date_registered.strftime("%Y-%m-%d"),
            latest.risk_level if latest else "No predictions yet",
            latest.created_at.strftime("%Y-%m-%d %H:%M") if latest else "",
            patient.predictions.count(),
        ])
    return response
