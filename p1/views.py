from django.shortcuts import render

from django.http import JsonResponse
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

import json





def longlatExtractor(longlat):

    longlat= longlat.split(",")
    idx = 0
    lat =""
    long = ""
    for la in longlat:
                # print(lat)
        if idx ==0 or idx == 1:
                        
            lat += la + "." if idx == 0 else la
        if idx == 2 or idx == 3:
            long +=la + "." if idx == 2 else la

        idx+=1


    return (lat,long)


# select v.province   , count(v.vehicle_id ) from vehicles v group by v.province ;
# select v.regency    , count(v.vehicle_id ) from vehicles v group by v.regency ;



def testdrive(request,refas):
    
    bergerak = 0
    diam = 0
    berhenti = 0
    not_conected = 0
    not_actived = 0
    never_conected = 0 
    payload = []  # List ini akan kita gunakan untuk menampung hasil akhir dari Traccar

    # 1. AMBIL DAFTAR IMEI DARI DATABASE UTAMA (VEHICLES)
    imei_list = []
    with connections['default'].cursor() as cursor:

        if refas =="semua":
            cursor.execute("""
                SELECT v.imei 
                FROM vehicles v 
                WHERE v.imei != '' 
                AND v.category_group_name != '' 
            """)
        else:
             
            cursor.execute("""
                SELECT v.imei 
                FROM vehicles v 
                WHERE v.imei != '' 
                AND v.category_group_name != '' 
                AND v.category_group_name ilike %s;
            """,[refas])
        rows = cursor.fetchall()
        
        # Bersihkan string imei langsung saat dimasukkan ke list
        imei_list = [str(row[0]).strip() for row in rows if row[0]]

    # 2. AMBIL DATA DARI DATABASE KEDUA (TRACCAR) MENGGUNAKAN KLAUSA "IN"
    if imei_list:
        # Buat string placeholder %s dinamis sebanyak jumlah imei
        placeholders = ", ".join(["%s"] * len(imei_list))

        with connections['second'].cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    td.uniqueid,
                    td.positionid,
                    tp.id,
                    tp.speed,
                    tp.servertime,
                    tp.devicetime,
                    td.disabled,
                    td.status,
                    tp.attributes
                FROM tc_devices td
                INNER JOIN tc_positions tp ON td.positionid = tp.id
                WHERE td.uniqueid IN ({placeholders});
            """, imei_list)

            traccar_rows = cursor.fetchall()

            # Format hasil query Traccar ke dalam bentuk list of dictionary (JSON)
            #
            for row in traccar_rows:
                speed = row[3]
                status = row[7].strip()
                disable = row[6]
                attributes_raw = row[8]
                # event_name = "unknown"
                motion_status = False
                ignation = False

                # {"priority":1,"sat":0,"event":246,"ignition":false,"motion":false,"io80":4,"rssi":5,"io69":3,"in1":false,"out1":false,"io246":1,"power":12.393,"io206":60054,"battery":4.067,"io68":0,"io9":0,"axisX":126,"axisY":75,"axisZ":-10,"operator":51001,"odometer":3000,"io12":332003,"io11":894447440000,"io14":3560794,"distance":0.0,"totalDistance":4.739835508374251}
                if attributes_raw:
                    try:
                        # Ubah string JSON menjadi Python Dictionary
                        attr_dict = json.loads(attributes_raw) 
                        
                        # Ambil properti 'event' dan 'motion' di dalamnya
                        # event_name = attr_dict.get("event", "unknown")
                        motion_status = attr_dict.get("motion", False)
                        ignation = attr_dict.get("ignition", False)

                        print(f"IMEI: {row[0]} -> disable: {disable},status: {status}, ignation: {ignation}, Motion: {motion_status}, Event: {event_name}")
                    except Exception as e:
                        # Berjaga-jaga jika format JSON rusak di database
                        pass
                
                    
                    if disable == False and status == "online" and ignation == True and motion_status ==True:
                        bergerak += 1
                    elif  ignation == True and motion_status ==False:
                        diam+=1
                    elif disable == False and status == "online" and ignation == False:
                        berhenti+=1
                    elif disable == False and status == "unknown":
                        not_conected+=1
                    elif disable == True:
                        not_actived+=1
                    else:
                        never_conected+=1
                        
                
                # # if(disable == False and status == "online" )


                # #tc_device disable = off
                # #status = online
                # #ignation true
                # ##motion true
                # if speed > 0:
                #      bergerak+=1


                # #ignation true motion false
                # if status == "online" and speed == 0:
                #      diam +=1

                # #disable =false
                # #status = online
                # #ignation =off
                # #state berhenti


                # #disable off
                # #status = ofline
                # #tidak terhubung


                # #positon_id = null
                # never_conected
                

                combined = {
                    "imei": row[0],
                    "td_postid": row[1],
                    "tp_id": row[2],
                    "tp_speed": row[3],
                    "tp_servertime": row[4],
                    "tp_devicetime": row[5],  
                    "td_disabled": row[6],
                    "td_status": row[7].strip() if row[7] else "unknown"
                }
                payload.append(combined)

    # Mengintip hasil akhir yang sudah matang di terminal
    print(len(payload))

    # 3. KEMBALIKAN HASIL PELACAKAN TRACCAR KE BROWSER/API
    return JsonResponse( {
          "bergerak" : bergerak,
          "diam" : diam,
          "berhenti" : berhenti,
          "not_conected" : not_conected,
          "not_active" : not_actived,
          "never_active" : never_conected,
     }, safe=False)


def totalashintant(request):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
            select  count(v.vehicle_id ) from vehicles v  ;
            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                data={}
                data["count"] = row[0]
                
                payload.append(data)
    return JsonResponse(payload, safe=False)

def regencycount(request):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
            select v.regency   , count(v.vehicle_id ) from vehicles v group by v.regency ;
            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                data={}
                data["regency"] = row[0].upper()
                data["count"] = row[1]
                
                payload.append(data)
    return JsonResponse(payload, safe=False)



def provincecount(request):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
select v.province   , count(v.vehicle_id ) from vehicles v group by v.province ;
            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                data={}
                data["province"] = row[0].upper()
                data["count"] = row[1]
                
                payload.append(data)
    return JsonResponse(payload, safe=False)



def recipmentcount(request):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
select v.category_group_name  , count(v.vehicle_id ) from vehicles v group by v.category_group_name 

            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                data={}
                data["recipment_group"] = row[0].upper()
                data["count"] = row[1]
                
                payload.append(data)
    return JsonResponse(payload, safe=False)



def jenisalsintan(request):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
            select v.vehicle_name , count(v.vehicle_id ) from vehicles v group by v.vehicle_name 

            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                data={}
                data["vehivle_name"] = row[0].upper()
                data["count"] = row[1]
                
                payload.append(data)
    return JsonResponse(payload, safe=False)

def recipientgrouphourvskm(request):

    with connections['default'].cursor() as cursor:
            cursor.execute("""

                SELECT
                v.category_group_name,
                SUM(
                    CASE
                        WHEN v.engine_hours ~ '^[0-9]+(\.[0-9]+)?$'
                        THEN v.engine_hours::NUMERIC
                        ELSE 0
                    END
                ) AS sum_engine_hour,
                SUM(
                    CASE
                        WHEN v.distance_km ~ '^[0-9]+(\.[0-9]+)?$'
                        THEN v.distance_km::NUMERIC
                        ELSE 0
                    END
                ) AS sum_distance
            FROM vehicles v
            WHERE v.category_group_name IS NOT NULL
            AND v.category_group_name <> ''
            GROUP BY v.category_group_name;
            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                data={}
                data["recipient_group"] = row[0].upper()
                data["sum_engine_hours"] = row[1]
                data["sum_distance_km"] = row[2]
                payload.append(data)
    return JsonResponse(payload, safe=False)
    

 
def provhourvskm(request):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
            SELECT
                v.province,
                SUM(
                    CASE
                        WHEN v.engine_hours ~ '^[0-9]+(\.[0-9]+)?$'
                        THEN v.engine_hours::NUMERIC
                        ELSE 0
                    END
                ) AS sum_engine_hour,
                SUM(
                    CASE
                        WHEN v.distance_km ~ '^[0-9]+(\.[0-9]+)?$'
                        THEN v.distance_km::NUMERIC
                        ELSE 0
                    END
                ) AS sum_distance
            FROM vehicles v
            WHERE v.province IS NOT NULL
            AND v.province <> ''
            GROUP BY v.province;
            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                data={}
                data["regency"] = row[0].upper()
                data["sum_engine_hours"] = row[1]
                data["sum_distance_km"] = row[2]
                payload.append(data)
    return JsonResponse(payload, safe=False)

def kabupatenhourvskm(request):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
            SELECT
                v.regency,
                SUM(
                    CASE
                        WHEN v.engine_hours ~ '^[0-9]+(\.[0-9]+)?$'
                        THEN v.engine_hours::NUMERIC
                        ELSE 0
                    END
                ) AS sum_engine_hour,
                SUM(
                    CASE
                        WHEN v.distance_km ~ '^[0-9]+(\.[0-9]+)?$'
                        THEN v.distance_km::NUMERIC
                        ELSE 0
                    END
                ) AS sum_distance
            FROM vehicles v
            WHERE v.regency IS NOT NULL
            AND v.regency <> ''
            AND v.regency != 'Brigade Dinas'
            GROUP BY v.regency;
            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                data={}
                data["regency"] = row[0].upper()
                data["sum_engine_hours"] = row[1]
                data["sum_distance_km"] = row[2]
                payload.append(data)
    return JsonResponse(payload, safe=False)
    

def purjunal(request):

    if cache.get("purjurnal") is not None:
        print("Key exists")
        
        # print(cache.get("name"))
        print("Using Caching")
        payload = cache.get("purjurnal")
    else:

        with connections['default'].cursor() as cursor:
            cursor.execute("""
            select v.vehicle_merk ,v.latitude_longitude , v.province , v.regency   from vehicles v 
            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:
                data = {} 
                lat ,long =longlatExtractor(row[1])
                data["lat"] = lat
                data["lng"] = long
                data["provinsi"] = row[2]
                data["kabupaten"] = row[3]
                data["merk"] = row[0]

                payload.append(data)
            cache.set("purjurnal", payload, timeout=300)    
        # print(payload)
        print("Key does not exist")
    
      

    


    return JsonResponse(payload, safe=False)


def purjunal(request,year=None,provience=None):

    if cache.get("purjurnal") is not None:
        print("Key exists")
        
        # print(cache.get("name"))
        print("Using Caching")
        payload = cache.get("purjurnal")
    else:

        with connections['default'].cursor() as cursor:
            cursor.execute("""
            select v.vehicle_merk ,v.latitude_longitude , v.province , v.regency   from vehicles v 
            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:
                data = {} 
                lat ,long =longlatExtractor(row[1])
                data["lat"] = lat
                data["lng"] = long
                data["provinsi"] = row[2]
                data["kabupaten"] = row[3]
                data["merk"] = row[0]

                payload.append(data)
            cache.set("purjurnal", payload, timeout=300)    
        # print(payload)
        print("Key does not exist")
    
      

    


    return JsonResponse(payload, safe=False)



# const purnajual = [
   
# ];


# def purjunal(request):
#     return JsonResponse(   {
#         "merk": "BASKARA", 
#         "lat": -6.510863, 
#         "lng": 108.2697981, 
#         "provinsi": "JAWA BARAT", 
#         "kabupaten": "INDRAMAYU"
#     }
# )

# def distributiondetail(request,distribution_id):
     

#      payload = {
#           "bergerak" : 0,
#           "diam" : 0,
#           "berhenti" : 0,
#           "not_conected" : 0,
#           "not_active" : 0,
#           "never_active" : 0,
#         #   "bergerak" : 0,
#      }
#      return JsonResponse(payload, safe=False)
     


def selectdistribution(request, gn):
     
     with connections['default'].cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        v.category_group_name as group_name,  
                        COUNT(v.vehicle_id) AS total 
                    FROM vehicles v
                    WHERE v.category_group_name ILIKE %s
                    GROUP BY v.category_group_name;
                """,[gn])
                rows = cursor.fetchall()
                # FIX 2: Validasi jika data tidak ditemukan agar tidak IndexError
                if rows:
                    # rows[0] adalah baris pertama hasil query, misalnya: ('UPJA', 45)
                    payload = {
                        "group_name": rows[0][0],  # Baris ke-0, Kolom ke-0 (recipient_group)
                        "total": rows[0][1]       # Baris ke-0, Kolom ke-1 (total)
                    }
                else:
                    # Jika grup tidak ditemukan di database, return data kosong / default
                    payload = {
                        "group_name": gn,
                        "total": 0
                    }

     return JsonResponse(payload, safe=False)

     



def distribution(request):
    if cache.get("distribution") is not None:
            print("Key exists")
             # print(cache.get("name"))
            print("Using Caching")
            payload = cache.get("distribution")
    with connections['default'].cursor() as cursor:
                cursor.execute("""
                SELECT
                COALESCE(v.recipient_group, 'Total') AS group_name,
                COUNT(*) AS total
                FROM vehicles v
                GROUP BY ROLLUP(v.recipient_group)
                ORDER BY (v.recipient_group IS NULL) ASC, total DESC;
                """)

                rows = cursor.fetchall()
                
                payload = []

                for row in rows:
                    data={}
                    data["group_name"] = row[0]
                    data["total"] = row[1]
                    payload.append(data)
                cache.set("distribution", payload, timeout=300)    
    return JsonResponse(payload, safe=False)




def services(request):
     

 # def purjunal(request):
    if cache.get("services") is not None:
            print("Key exists")
             # print(cache.get("name"))
            print("Using Caching")
            payload = cache.get("services")
    else:
            
        with connections['default'].cursor() as cursor:
                cursor.execute("""
                select * from services 
                """)

                rows = cursor.fetchall()
                
                payload = []

                for row in rows:
                    data={}
                    print(row)
                    lat ,long =longlatExtractor(row[2])

                    data["id"] = row[0]
                    data["name"] = row[1]
                    data["lat"] = lat
                    data["long"] = long
                    data["provinsi"] = row[3]
                    data["kabupaten"] = row[4]
                    data["alamat"] = row[5]
                    data["phone"] = row[6]
                    payload.append(data)
                    cache.set("services", payload, timeout=300)    
    return JsonResponse(payload, safe=False)

# def geofence(request):
#     return JsonResponse(   {
#         "nomorRangka": "ZH20241236352", 
#         "nomorMesin": "C52500839A", 
#         "namaBarang": "TRAKTOR RODA CRAWLER", 
#         "merk": "BASKARA", 
#         "tipe": "Suprema 100", 
#         "provinsi": "JAWA BARAT", 
#         "kabupaten": "INDRAMAYU", 
#         "event": "Geofence In", 
#         "time": "2026-06-12T15:56:48"
#     }
# )



def geofence(request):


     # def purjunal(request):
    if cache.get("geofence") is not None:
            print("Key exists")
             # print(cache.get("name"))
            print("Using Caching")
            payload = cache.get("geofence")
    else:


        with connections['default'].cursor() as cursor:
            cursor.execute("""
            select v.vin , v.engine_number , v.vehicle_name ,v.vehicle_merk ,v.vehicle_type ,v.province ,v.regency  from vehicles v 
            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:
                data = {}
                print(row)
                data["nomorRangka"] = row[0]
                data["nomorMesin"] = row[1]
                data["namaBarang"] = row[2]
                data["merk"] = row[3]
                data["tipe"] = row[4]
                data["provinsi"] = row[5]
                data["kabupaten"] = row[6]
                data["event"] = None
                data["time"] = None 
                payload.append(data)
                
            print(payload)
            cache.set("geofence", payload, timeout=300)    

    return JsonResponse(payload, safe=False)





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


def alsintan(request):

    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    qry = """
    SELECT
        v.vehicle_id,
        v.vehicle_year,
        v.vin,
        v.engine_number,
        v.vehicle_name,
        v.vehicle_merk,
        v.vehicle_type,
        v.recipient_party,
        v.recipient_group,
        v.recipient_name,
        v.phone_number,
        v.recipient_address,
        v.province,
        v.regency,
        v.subdistrict,
        v.ward,
        v.engine_hours,
        v.distance_km,
        v.latitude_longitude
    FROM vehicles v
    """

    conditions = []
    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(province)

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(regency)

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(subdistrict)

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(ward)

    if conditions:
        qry += " WHERE " + " AND ".join(conditions)
    # print(qry)

    if cache.get("alsintan") is not None:
            print("Key exists")
             # print(cache.get("name"))
            print("Using Caching")
            payload = cache.get("alsintan")
    else:

        with connections['default'].cursor() as cursor:
            cursor.execute(qry)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:
                data = {}
                latlong = row[18].split(",")
                
                # print(latlong)
                idx = 0
                lat =""
                long = ""
                for la in latlong:
                # print(lat)
                    if idx ==0 or idx == 1:
                        
                        lat += la + "." if idx == 0 else la
                    if idx == 2 or idx == 3:
                        long +=la + "." if idx == 2 else la

                    idx+=1

                data["id"] = row[0]
                data["tahun"] = row[1]
                data["nomorRangka"] = row[2]
                data["nomorMesin"] = row[3]
                data["namaBarang"] = row[4]
                data["merk"] = row[5]
                data["tipe"] = row[6]
                data["pihak"] = row[7]
                data["kelompok"] = row[8]
                data["nama"] = row[9]
                data["telp"] = row[10]
                data["alamat"] = row[11]
                data["provinsi"] = row[12]
                data["kabupaten"] = row[13]
                data["kecamatan"] = row[14]
                data["kelurahan"] = row[15]
                data["engineHour"] = row[16]
                data["km"] = row[17]
                data["lat"] = lat
                data["lng"] = long
                data["lastUpdated"] = None
                payload.append(data)
            cache.set("alsintan", payload, timeout=300)    


    return JsonResponse(payload, safe=False)

    # return JsonResponse(   {
    #     "id": "ZH20241236352", 
    #     "tahun": "2025", 
    #     "nomorRangka": "ZH20241236352", 
    #     "nomorMesin": "C52500839A", 
    #     "namaBarang": "TRAKTOR RODA CRAWLER", 
    #     "merk": "BASKARA", 
    #     "tipe": "Suprema 100", 
    #     "pihak": "BRIGADE SRI UNGGUL", 
    #     "kelompok": "BRIGADE PANGAN", 
    #     "nama": "SUNTANA", 
    #     "telp": "0", 
    #     "alamat": "-", 
    #     "provinsi": "PROV. JAWA BARAT", 
    #     "kabupaten": "KAB. INDRAMAYU", 
    #     "kecamatan": "KEC. BANGODUA", 
    #     "kelurahan": "WANASARI", 
    #     "engineHour": 1621956, 
    #     "km": 461, 
    #     "lat": -6.510863, 
    #     "lng": 108.2697981, 
    #     "lastUpdated": None
    # }

# )
# @csrf_exempt
# def alsintan(request):
    
#     return JsonResponse(   {
#         "id": "ZH20241236352", 
#         "tahun": "2025", 
#         "nomorRangka": "ZH20241236352", 
#         "nomorMesin": "C52500839A", 
#         "namaBarang": "TRAKTOR RODA CRAWLER", 
#         "merk": "BASKARA", 
#         "tipe": "Suprema 100", 
#         "pihak": "BRIGADE SRI UNGGUL", 
#         "kelompok": "BRIGADE PANGAN", 
#         "nama": "SUNTANA", 
#         "telp": "0", 
#         "alamat": "-", 
#         "provinsi": "PROV. JAWA BARAT", 
#         "kabupaten": "KAB. INDRAMAYU", 
#         "kecamatan": "KEC. BANGODUA", 
#         "kelurahan": "WANASARI", 
#         "engineHour": 1621956, 
#         "km": 461, 
#         "lat": -6.510863, 
#         "lng": 108.2697981, 
#         "lastUpdated": None
#     }

# )
