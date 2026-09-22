from django.urls import path

from inspection import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.list_view, name="list"),
    path("ledger/", views.ledger_view, name="ledger"),
    path("ledger/new/", views.card_create_view, name="card_create"),
    path("ledger/<str:aid_code>/", views.card_detail_view, name="card_detail"),
    path("inspections/new/", views.create_view, name="create"),
    path("inspections/<int:pk>/", views.detail_view, name="detail"),
]
