from django.urls import path
from . import views

urlpatterns = [
    path('purnajuals', views.purjunal, name='purjunal'),
    # path('purnajuals/<str:year>', views.purjunal, name='purjunal'),
    path('services', views.services, name='services'),
    path('geofence', views.geofence, name='geofence'),
    # path('geofence/', views.geofence, name='geofence'),
    path('alsintan', views.alsintan, name='alsintan'),
    path('distribution', views.distribution, name='distribution'),
    path('distributiondetail/<str:refas>/', views.testdrive, name='testdrive'),
    path('selectdistribution/<str:gn>/', views.selectdistribution, name='selectdistribution'),
    path('kabupatenhourvskm', views.kabupatenhourvskm, name='kabupatenhourvskm'),
    path('recipientgrouphourvskm', views.recipientgrouphourvskm, name='recipientgrouphourvskm'),
    path('jenisalsintan', views.jenisalsintan, name='jenisalsintan'),
    path('recipmentcount', views.recipmentcount, name='recipmentcount'),
    path('provincecount', views.provincecount, name='provincecount'),
    path('regencycount', views.regencycount, name='regencycount'),
    path('subdistriccount', views.subdistriccount, name='subdistriccount'),
    path('wardcount', views.wardcount, name='wardcount'),



    



    path('totalashintant', views.totalashintant, name='totalashintant'),

    path('testdrive', views.testdrive, name='testdrive'),

    # path('alsintan/<str:year>', views.alsintan, name='alsintan-y'),
    # path('alsintan/<str:year>/<str:provience>', views.alsintan, name='alsintan-y-p'),
    # path('alsintan/<str:year>/<str:provience>/<str:regency>', views.alsintan, name='alsintan-y-p-r-'),
    # path('alsintan/<str:year>/<str:provience>/<str:regency>/<str:subdistric>', views.alsintan, name='alsintan-y-p-r-s'),
    # path('alsintan/<str:year>/<str:provience>/<str:regency>/<str:subdistric>/<str:ward>', views.alsintan, name='alsintan-y-p-r-s-w'),


    
    # path('distributiondetail/<str:distribution_id>/', views.testdrive, name='testdrive'),
   
   
  
    # path('recipmentcount', views.recipmentcount, name='recipmentcount'),
    # path('provincecount', views.provincecount, name='provincecount'),
    # path('regencycount', views.regencycount, name='regencycount'),
    # path('totalashintant', views.totalashintant, name='totalashintant'),
    # path('testdrive', views.testdrive, name='testdrive'),
    path('provhourvskm', views.provhourvskm, name='provhourvskm'),
    path('average-engine-hours/<str:category>/', views.average_engine_hours, name='average_engine_hours'),
    path('average-distance-km/<str:category>/', views.average_distance_km, name='average_distance_km'),
    
















]
"""

172.18.216.82:8000/cards/purjunal/
172.18.216.82:8000/cards/services/
172.18.216.82:8000/cards/geofence/
172.18.216.82:8000/cards/alsintan/



"""