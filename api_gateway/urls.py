"""
FinEdge — API Gateway URL Configuration
=========================================
"""

from django.urls import path

from . import views, dashboard_views

urlpatterns = [
    # Public
    path("", views.landing_page, name="landing_page"),
    path("docs/", views.api_docs, name="api_docs"),
    path("privacy/", views.privacy_policy, name="privacy_policy"),
    path("contact/", views.submit_contact_form, name="submit_contact_form"),
    path("health/", views.health_check, name="health_check"),

    # Authenticated — Edge SDK scoring endpoint
    path("v1/score/", views.SubmitEdgeMetadataView.as_view(), name="submit_edge_metadata"),
    path("v1/trigger_score/<str:application_id>/", views.trigger_trust_score, name="trigger_trust_score"),
    path("v1/trigger_decision/<str:application_id>/", views.trigger_decision, name="trigger_decision"),
    path("v1/application/<str:application_id>/status/", views.application_status_check, name="application_status_check"),

    # Dashboards (Server-rendered Django templates)
    path("dashboard/admin/", dashboard_views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/officer/<str:tenant_code>/", dashboard_views.officer_dashboard, name="officer_dashboard"),

    # JSON API for Vercel static frontend
    path("officer/<str:tenant_code>/applications/", dashboard_views.officer_api_applications, name="officer_api_applications"),
]