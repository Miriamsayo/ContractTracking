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
from django.urls import path
from contracts import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from contracts.views import (
    ContractViewSet, login_view, signup, home, add_contract, edit_contract, contract_list, contract_create
)

router = DefaultRouter()
router.register(r'contracts', ContractViewSet)  # API routes for contract management

urlpatterns = [
    # Authentication & Admin Routes
    path('signup/', signup, name='signup'),
    path('login/', login_view, name="login"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),

    # API Routes
    path('auth/', include('djoser.urls')),  # Djoser authentication routes
    path('api/', include(router.urls)),  # Contract API routes

    # Frontend Routes for Contracts
    path('', home, name="home"),  # Homepage
    path('contracts/', contract_list, name='contract_list'),  # List contracts
    path('contracts/add/', add_contract, name='add_contract'),  # Add new contract
    path('contracts/edit/<int:pk>/', edit_contract, name='edit_contract'), 
    path('create/',contract_create, name='contract_create'),
]

# Serve static and media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
