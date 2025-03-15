"""
URL configuration for contracttrackingmanagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from contracts.views import (
    ContractViewSet,
    login_view,
    signup,
    dashboard,
    contract_edit,
    contract_list,
    user_list,
    contract_create,
    delete_contract,
    about_view,
    contract_detail,
    logout_view,
)

# API Router for contract management
router = DefaultRouter()
router.register(r"contracts", ContractViewSet)

urlpatterns = [
    # Admin & Authentication Routes
    path("admin/", admin.site.urls),
    path("signup/", signup, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # API Routes
    path("api/auth/", include("djoser.urls")),  # Djoser authentication routes
    path("api/", include(router.urls)),  # Contract API routes

    # Frontend Views
    path("", dashboard, name="home"),  # Homepage
    path("dashboard/", dashboard, name="dashboard"),
    path("contracts/", contract_list, name="contract_list"),  # List contracts
    path("users/", user_list, name="user_list"),
    
    # Contract Management
    path("contracts/<int:pk>/", contract_detail, name="contract_detail"),  # View contract details
    path("contracts/<int:pk>/edit/", contract_edit, name="contract_edit"),  # Edit contract
    path("contracts/<int:pk>/delete/", delete_contract, name="contract_delete"),  # Delete contract
    path("contracts/new/", contract_create, name="contract_create"),  # Create contract

    # About Page
    path("about/", about_view, name="about"),
]

# Serve static and media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
