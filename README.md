# Maternal Risk Prediction System (Django)

A Django web application for classifying pregnant women into Low / Medium /
High maternal risk, built as a proposal-ready system for hospital use:
patient records, risk history, a high-risk alerts queue, and a live
monitoring dashboard, on top of the original prediction engine.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # for /admin/ and staff-only sidebar links
python manage.py runserver
```

Then open http://127.0.0.1:8000/register/ to create an account, or
http://127.0.0.1:8000/login/ if you already have one. After login you land
on the Dashboard.

## Login / Register slideshow

The left panel on the login and register pages (`risk_app/templates/risk_app/base_auth.html`)
is a 4-slide auto-rotating slideshow (5s per slide, click a dot to jump manually).
It currently uses custom line-icon illustrations rather than photos, since this
environment has no internet access to source real stock photography.

To swap in real photographs:
1. Add your images to `risk_app/static/risk_app/img/` (e.g. `slide-1.jpg`).
2. In `base_auth.html`, replace the `<div class="slide-art">...</div>` SVG block in
   each `.auth-slide` with `<img src="{% static 'risk_app/img/slide-1.jpg' %}" alt="...">`,
   and add `.auth-slide img { width: 100%; height: 100%; object-fit: cover; position: absolute; inset: 0; }`
   plus `.slide-art { display: none; }` to `static/css/style.css` (or restyle to taste).
3. Free sources for maternal/clinical health photography with permissive licenses:
   Unsplash (unsplash.com) and Pexels (pexels.com) both have "maternal health" /
   "prenatal care" / "African mother" search results usable without attribution
   under their free license — always double-check the license on the specific photo.

## Modules

- **Dashboard** (`/dashboard/`) — 7-day prediction volume, registered
  patient count, high-risk alert count, Low/Medium/High breakdown, a
  Recent Predictions table (linked to patient names where applicable),
  and the model's top weighted risk factors.
- **Predict Risk** (`/`) — the clinical input form. Optionally link the
  prediction to a registered patient (so it's saved to their history), or
  leave it as a walk-in/one-off prediction.
- **Patient Records** (`/patients/`) — searchable list of every registered
  patient with their latest risk level; **Export CSV** produces a
  hospital-ready report (patient ID, name, phone, latest risk, prediction
  count) for handing to management.
- **Register Patient** (`/patients/new/`) — adds a patient with an
  auto-generated ID (`PT-00001`, `PT-00002`, ...).
- **Patient detail** (`/patients/<id>/`) — full risk history for one
  patient across every prediction made for them, plus a shortcut to run a
  new prediction pre-linked to that patient.
- **High-Risk Alerts** (`/alerts/`) — every patient whose most recent
  prediction is High risk, most recent first, with a live count badge in
  the sidebar.
- **Manage Users** — visible in the sidebar only to staff accounts
  (`is_staff=True`), links to Django's built-in `/admin/` for user and
  data management.
- **Login / Register** (`/login/`, `/register/`) — all of the above
  requires being signed in.

## Project structure

```
maternal_risk_site/     Django project settings/urls (auth routes included)
risk_app/
  forms.py              PatientRiskForm (includes patient selector), RegisterForm, PatientForm
  models.py               Patient (auto-generated PT-##### IDs) and PredictionRecord
                          (now linked to Patient via FK, in addition to the
                          staff user who ran it)
  views.py               Model loading (sklearn fallback OR your CatBoost .cbm),
                          prediction logic, patients list/detail/register views,
                          alerts view, CSV export, login_required throughout,
                          register_view, dashboard aggregation queries
  context_processors.py   Computes the sidebar's High-Risk Alerts badge count
                          on every page (small N+1 query loop -- fine at
                          hospital-ward scale, worth an annotate() rewrite if
                          the patient list grows into the thousands)
  migrations/
    0002_seed_demo_predictions.py   Seeds 8 demo prediction rows
    0004_seed_demo_patients.py      Seeds 4 demo patients and links 2 of
                                     them to the seeded High-risk predictions
                                     (safe to delete/reverse)
  urls.py                 /  and  /dashboard/  (login/register/logout are
                          wired in the project-level urls.py via Django's
                          built-in auth views)
  ml/                      Trained model artifacts (see "Model" below)
  templates/risk_app/
    base_app.html          Sidebar + topbar shell for logged-in pages
    base_auth.html          Split dark-teal/white shell for login/register
    login.html, register.html
    predict.html, dashboard.html
    patients_list.html, patient_detail.html, patient_form.html, alerts.html
static/css/style.css      Modern clinical theme: light surfaces, teal accent,
                          dark-teal sidebar (all pages)
```

## Model

By default the app runs on the sklearn Gradient Boosting model from
`prepare_maternal_risk_data.py`:

- `risk_app/ml/risk_model.joblib`
- `risk_app/ml/preprocessor.joblib`
- `risk_app/ml/model_metadata.joblib`

### Switching to your CatBoost model

Drop your trained model in as:

```
risk_app/ml/model.cbm
```

`views.py` checks for this file at startup and, if present, automatically
switches to it — no other code changes needed. Full details, including
how CatBoost's native categorical handling is wired up, are in
`risk_app/ml/PUT_YOUR_MODEL_HERE.txt`. You'll also need to
`pip install catboost` (commented out in requirements.txt by default).

## ⚠️ Before using this for real patients

This model was trained on a synthetic dataset (see the project's earlier
`Notes & Methodology` sheet) and its target label (`Risk_Level`) comes from
a hand-built scoring rubric, not real birth outcomes. Retrain on genuine
patient data with real outcomes (NICU admission, postpartum hemorrhage,
maternal near-miss/mortality, emergency C-section, etc.) before this
informs any real triage or care decisions.

