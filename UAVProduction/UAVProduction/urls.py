"""
URL configuration for UAVProduction project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.urls import path
from DjangoAPI import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('partproduction/', views.partproduction, name='partproduction'),
    path('partproduction/list/', views.part_production_list, name='part_production_list'),  
    path('partproduction/create/', views.create_partproduction, name='create_partproduction'),
    path('partproduction/edit/<int:part_production_id>/', views.edit_partproduction, name='edit_partproduction'),
    path('partproduction/delete/<int:part_production_id>/', views.delete_partproduction, name='delete_partproduction'),
    path('assembly/', views.assembly, name='assembly'),
    path('assembly/create/', views.create_assembly, name='create_assembly'),
    path('uav_production_list/', views.uav_production_list, name='uav_production_list'),
    path('get_parts_for_assembly/<int:assembly_id>/', views.get_parts_for_assembly, name='get_parts_for_assembly'),
    path('logout/', views.custom_logout, name='logout'),

]
