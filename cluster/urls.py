from django.urls import path
from . import views

urlpatterns = [
    path('getprovince', views.GetProvince, name='GetProvince'),
    path('getregency/<str:province>/', views.Getregency, name='Getregency'),
    path('getsubdistrict/<str:regency>/', views.Getsubdistrict, name='Getsubdistrict'),
    path('getward/<str:regency>/<str:subdistrict>/', views.Getward, name='Getward'),



    















]
"""

172.18.216.82:8000/cards/purjunal/
172.18.216.82:8000/cards/services/
172.18.216.82:8000/cards/geofence/
172.18.216.82:8000/cards/alsintan/



"""