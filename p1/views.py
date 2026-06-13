from django.shortcuts import render

from django.http import JsonResponse
from django.db import connections
from django.views.decorators.csrf import csrf_exempt

# def purjunal(request):


#     with connections['default'].cursor() as cursor:
#         cursor.execute("""
#         select v.vehicle_merk ,v.latitude_longitude , v.province , v.regency   from vehicles v 
#         """)

#         rows = cursor.fetchall()
        
#         payload = []

#         for row in rows:
#             data = {}
#             latlong = row[1].split(",")
            
#             # print(latlong)
#             idx = 0
#             lat =""
#             long = ""
#             for la in latlong:
#             # print(lat)
#                 if idx ==0 or idx == 1:
                    
#                     lat += la + "." if idx == 0 else la
#                 if idx == 2 or idx == 3:
#                     long +=la + "." if idx == 2 else la

#                 idx+=1
#             data["lat"] = lat
#             data["long"] = long
#             data["provinsi"] = row[2]
#             data["kabupaten"] = row[3]
#             data["merk"] = row[0]

#             payload.append(data)
            
#         print(payload)
      


#     return JsonResponse(payload, safe=False)



# const purnajual = [
   
# ];


def purjunal(request):
    return JsonResponse(   {
        "merk": "BASKARA", 
        "lat": -6.510863, 
        "lng": 108.2697981, 
        "provinsi": "JAWA BARAT", 
        "kabupaten": "INDRAMAYU"
    }
)

def services(request):
    return JsonResponse(   {
        "nama": "NAMA BENGKEL", 
        "provinsi": "PROVINSI", 
        "kabupaten": "KABUPATEN", 
        "alamat": "ALAMAT"
    }
)

def geofence(request):
    return JsonResponse(   {
        "nomorRangka": "ZH20241236352", 
        "nomorMesin": "C52500839A", 
        "namaBarang": "TRAKTOR RODA CRAWLER", 
        "merk": "BASKARA", 
        "tipe": "Suprema 100", 
        "provinsi": "JAWA BARAT", 
        "kabupaten": "INDRAMAYU", 
        "event": "Geofence In", 
        "time": "2026-06-12T15:56:48"
    }
)

@csrf_exempt
def alsintan(request):
    return JsonResponse(   {
        "id": "ZH20241236352", 
        "tahun": "2025", 
        "nomorRangka": "ZH20241236352", 
        "nomorMesin": "C52500839A", 
        "namaBarang": "TRAKTOR RODA CRAWLER", 
        "merk": "BASKARA", 
        "tipe": "Suprema 100", 
        "pihak": "BRIGADE SRI UNGGUL", 
        "kelompok": "BRIGADE PANGAN", 
        "nama": "SUNTANA", 
        "telp": "0", 
        "alamat": "-", 
        "provinsi": "PROV. JAWA BARAT", 
        "kabupaten": "KAB. INDRAMAYU", 
        "kecamatan": "KEC. BANGODUA", 
        "kelurahan": "WANASARI", 
        "engineHour": 1621956, 
        "km": 461, 
        "lat": -6.510863, 
        "lng": 108.2697981, 
        "lastUpdated": None
    }

)
