from django.urls import path
from . import views

app_name = "risk_app"

urlpatterns = [
    path("", views.predict_view, name="predict"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("patients/", views.patients_list_view, name="patients_list"),
    path("patients/new/", views.patient_register_view, name="patient_register"),
    path("patients/<int:pk>/", views.patient_detail_view, name="patient_detail"),
    path("patients/export/", views.export_patients_csv, name="export_patients_csv"),
    path("alerts/", views.alerts_view, name="alerts"),
]
