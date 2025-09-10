
from django.urls import path
from django.contrib import admin

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("account/<str:name>", views.account, name="account"),
    path("transfer", views.ex_transfer, name="transfer"),
    path("inttransfer", views.internal_transfer, name="inttransfer"),
    path("categorize", views.categorize, name="categorize"),
    path("search", views.search, name="search"),
    path("spending", views.spending, name="spending"),
    path("chart_data/<str:period>", views.chart_data, name="chart_data"),
    path("savings_data/<str:period>", views.savings_data, name="savings_data"),
    path("savings", views.savings, name="savings"),
    path("paycheck", views.paycheck, name="paycheck"),
    path("paycheck_data/<str:month>", views.paycheck_data, name="spending_data"),
    path("admin/", admin.site.urls)
]
