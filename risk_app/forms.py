from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Patient

YES_NO = [("No", "No"), ("Yes", "Yes")]
POS_NEG = [("Negative", "Negative"), ("Positive", "Positive")]


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["full_name", "phone_number"]
        widgets = {
            "full_name": forms.TextInput(attrs={"placeholder": "e.g. Jane Wanjiru"}),
            "phone_number": forms.TextInput(attrs={"placeholder": "e.g. +254 700 000 000 (optional)"}),
        }


class PatientRiskForm(forms.Form):
    patient = forms.ModelChoiceField(
        label="Patient",
        queryset=None,
        required=False,
        empty_label="Walk-in / not linked to a patient record",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient"].queryset = Patient.objects.all().order_by("-date_registered")

    # --- Demographics -------------------------------------------------
    age = forms.IntegerField(label="Age", min_value=12, max_value=55, initial=28)
    education_level = forms.ChoiceField(
        label="Education Level",
        choices=[(c, c) for c in ["None", "Primary", "Secondary", "Tertiary"]],
        initial="Secondary",
    )
    distance_to_facility_km = forms.FloatField(label="Distance to Facility (km)", min_value=0, initial=5.0)
    substance_use = forms.ChoiceField(label="Substance Use", choices=YES_NO, initial="No")
    socioeconomic_index = forms.ChoiceField(
        label="Socioeconomic Index", choices=[(c, c) for c in ["Low", "Medium", "High"]], initial="Medium"
    )

    # --- Obstetric history ---------------------------------------------
    gravida = forms.IntegerField(label="Gravida (total pregnancies)", min_value=1, max_value=15, initial=1)
    parity = forms.IntegerField(label="Parity (previous live births)", min_value=0, max_value=14, initial=0)
    previous_c_section = forms.ChoiceField(label="Previous C-Section", choices=YES_NO, initial="No")
    previous_stillbirth_miscarriage = forms.ChoiceField(
        label="Previous Stillbirth/Miscarriage", choices=YES_NO, initial="No"
    )
    interval_since_last_pregnancy_months = forms.FloatField(
        label="Months Since Last Pregnancy (0 if first pregnancy)", min_value=0, initial=0
    )

    # --- Current pregnancy ------------------------------------------------
    gestational_age_weeks = forms.IntegerField(label="Gestational Age (weeks)", min_value=4, max_value=42, initial=28)
    anc_visits_count = forms.IntegerField(label="ANC Visits So Far", min_value=0, max_value=15, initial=4)
    first_anc_visit_week = forms.IntegerField(label="Week of First ANC Visit", min_value=4, max_value=40, initial=10)
    multiple_gestation = forms.ChoiceField(label="Multiple Gestation (twins/triplets)", choices=YES_NO, initial="No")
    fetal_presentation = forms.ChoiceField(
        label="Fetal Presentation", choices=[(c, c) for c in ["Cephalic", "Breech", "Transverse"]], initial="Cephalic"
    )

    # --- Vitals ---------------------------------------------------------
    bmi = forms.ChoiceField(label="BMI Category", choices=[(c, c) for c in ["underweight", "normal", "overweight"]], initial="normal")
    weight_kg = forms.FloatField(label="Current Weight (kg)", min_value=30, max_value=150, initial=65)
    prepregnancy_weight_kg = forms.FloatField(label="Pre-pregnancy Weight (kg)", min_value=30, max_value=150, initial=58)
    pulse = forms.IntegerField(label="Pulse (bpm)", min_value=40, max_value=180, initial=80)
    systolic = forms.IntegerField(label="Systolic BP (mmHg)", min_value=70, max_value=220, initial=118)
    diastolic = forms.IntegerField(label="Diastolic BP (mmHg)", min_value=40, max_value=140, initial=76)
    fundal_height_cm = forms.FloatField(label="Fundal Height (cm)", min_value=4, max_value=45, initial=28)
    fetal_heart_rate_bpm = forms.IntegerField(label="Fetal Heart Rate (bpm)", min_value=100, max_value=180, initial=140)

    # --- Labs -------------------------------------------------------------
    hemoglobin_g_dl = forms.FloatField(label="Hemoglobin (g/dL)", min_value=4, max_value=16, initial=12)
    anaemia_severity = forms.ChoiceField(
        label="Anaemia Severity", choices=[(c, c) for c in ["None", "Mild", "Moderate", "Severe"]], initial="None"
    )
    blood_glucose_mg_dl = forms.FloatField(label="Blood Glucose (mg/dL)", min_value=50, max_value=350, initial=95)
    diabetes_severity = forms.ChoiceField(
        label="Diabetes Severity",
        choices=[(c, c) for c in ["None", "Diet-controlled", "Medication-controlled", "Insulin-dependent"]],
        initial="None",
    )
    urine_protein = forms.ChoiceField(
        label="Urine Protein", choices=[(c, c) for c in ["Negative", "Trace", "1+", "2+", "3+"]], initial="Negative"
    )
    eclampsia_severity = forms.ChoiceField(
        label="Eclampsia/Pre-eclampsia Severity",
        choices=[(c, c) for c in ["None", "Mild pre-eclampsia", "Severe pre-eclampsia", "Eclampsia"]],
        initial="None",
    )
    haemorrhage_severity = forms.ChoiceField(
        label="Haemorrhage Severity", choices=[(c, c) for c in ["None", "Mild", "Moderate", "Severe"]], initial="None"
    )
    uti_severity = forms.ChoiceField(
        label="UTI Severity", choices=[(c, c) for c in ["None", "Mild", "Recurrent"]], initial="None"
    )
    liver_disorder_severity = forms.ChoiceField(
        label="Liver Disorder Severity", choices=[(c, c) for c in ["None", "Mild", "Severe"]], initial="None"
    )
    blood_group = forms.ChoiceField(label="Blood Group", choices=[(c, c) for c in ["O", "A", "B", "AB"]], initial="O")
    rh_factor = forms.ChoiceField(label="Rh Factor", choices=POS_NEG, initial="Negative")
    hiv_status = forms.ChoiceField(label="HIV Status", choices=POS_NEG, initial="Negative")
    syphilis_status = forms.ChoiceField(label="Syphilis Status", choices=POS_NEG, initial="Negative")
    vomiting = forms.ChoiceField(label="Persistent Vomiting", choices=YES_NO, initial="No")
