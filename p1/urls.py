from django.urls import path
from . import views

urlpatterns = [
    path('purnajuals', views.purjunal, name='purjunal'),
    path('services', views.services, name='services'),
    path('geofence', views.geofence, name='geofence'),
    # path('geofence/', views.geofence, name='geofence'),
    path('alsintan', views.alsintan, name='alsintan'),
    path('distribution', views.distribution, name='distribution'),
    # path('distributiondetail/<str:distribution_id>/', views.testdrive, name='testdrive'),
    path('distributiondetail/<str:refas>/', views.testdrive, name='testdrive'),
    path('distributiondetail/<str:refas>/<str:status>/', views.testdrive_detail, name='testdrive_detail'),
    path('selectdistribution/<str:gn>/', views.selectdistribution, name='selectdistribution'),
    path('kabupatenhourvskm', views.kabupatenhourvskm, name='kabupatenhourvskm'),
    path('recipientgrouphourvskm', views.recipientgrouphourvskm, name='recipientgrouphourvskm'),
    path('jenisalsintan', views.jenisalsintan, name='jenisalsintan'),
    path('recipmentcount', views.recipmentcount, name='recipmentcount'),
    path('provincecount', views.provincecount, name='provincecount'),
    path('regencycount', views.regencycount, name='regencycount'),
    path('totalashintant', views.totalashintant, name='totalashintant'),
    path('testdrive', views.testdrive, name='testdrive'),
    path('provhourvskm', views.provhourvskm, name='provhourvskm'),
    















]
"""

172.18.216.82:8000/cards/purjunal/
172.18.216.82:8000/cards/services/
172.18.216.82:8000/cards/geofence/
172.18.216.82:8000/cards/alsintan/



"""