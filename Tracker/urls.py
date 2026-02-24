from django.urls import path
from . import views
from .views import CSVUploadView


urlpatterns = [
    path("api/set-csrf-token", views.set_csrf_token, name="set_csrf_token"),
    path("api/login", views.login_view, name="login"),
    path("api/logout", views.logout_view, name="logout"),
    path("api/user", views.user, name="user"),
    path("api/register", views.register, name="register"),
    path("api/upload-csv/", CSVUploadView.as_view(), name="upload-csv"),
    path("api/portfolio/", views.portfolio_view, name="portfolio"),
    path("api/save-symbol/", views.save_symbol, name="save_symbol"),
    path("api/adjust-holding/", views.adjust_holding_view, name="adjust_holding"),
    path(
        "api/transfer/",
        views.create_transfer_transaction,
        name="create_transfer_transaction",
    ),
]
