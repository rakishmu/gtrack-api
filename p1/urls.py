from django.urls import path
from . import views

urlpatterns = [
    path('purnajual', views.purjunal, name='purjunal'),
    path('services', views.services, name='services'),
    path('geofence', views.geofence, name='geofence'),
    # path('geofence/', views.geofence, name='geofence'),
    path('alsintan', views.alsintan, name='alsintan'),


]
"""

172.18.216.82:8000/cards/purjunal/
172.18.216.82:8000/cards/services/
172.18.216.82:8000/cards/geofence/
172.18.216.82:8000/cards/alsintan/



"""