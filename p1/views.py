from django.shortcuts import render

from django.http import JsonResponse
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from rest_framework.decorators import api_view
from .serializers import *
import json
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter
)




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


@extend_schema(
    summary="Monitoring Dashboard",
    description="Get vehicle statistics from Traccar",
    parameters=[
        OpenApiParameter(
            name='refas',
            description='Category Group Name',
            required=True,
            type=str,
            location=OpenApiParameter.PATH
        ),
        OpenApiParameter(
            name='year',
            description='Vehicle Year',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='province',
            description='Province',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='regency',
            description='Regency',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='subdistrict',
            description='Subdistrict',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='ward',
            description='Ward',
            required=False,
            type=str
        ),
    ]
)
@api_view(['GET'])
def testdrive(request,refas):
    print("this giw")
    
    bergerak = 0
    diam = 0
    berhenti = 0
    not_conected = 0
    not_actived = 0
    never_conected = 0 
    payload = []  # List ini akan kita gunakan untuk menampung hasil akhir dari Traccar

    # 1. AMBIL DAFTAR IMEI DARI DATABASE UTAMA (VEHICLES)
    imei_list = []



    raw_year = request.GET.getlist('year')
    year_list = []
    for item in raw_year:
        for val in item.split(','):
            if val.strip():
                year_list.append(val.strip())

    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = [
        "v.imei != ''",
    ]

    params = []

    # refas filter
    if refas and refas.lower() != "semua":
        conditions.append("v.category_group_name ILIKE %s")
        params.append(f"%{refas}%")

    # location filters
    if year_list:
        placeholders = ", ".join(["%s"] * len(year_list))
        conditions.append(f"v.vehicle_year IN ({placeholders})")
        params.extend(year_list)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
    SELECT distinct  v.imei
    FROM vehicles v
    """

    if conditions:
        qry += " WHERE " + " AND ".join(conditions)

    print(qry)
    print(params)
    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()
        
        # Bersihkan string imei langsung saat dimasukkan ke list
        imei_list = [str(row[0]).strip() for row in rows if row[0]]

    # 2. AMBIL DATA DARI DATABASE KEDUA (TRACCAR) MENGGUNAKAN KLAUSA "IN"


    if imei_list:
        placeholders = ", ".join(["%s"] * len(imei_list))

        qry2 = f"""
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
            """
        # Buat string placeholder %s dinamis sebanyak jumlah imei

        # print(qry2)
        # print(imei_list)

        with connections['second'].cursor() as cursor:
            cursor.execute(qry2, imei_list)
            # print(cursor.query.decode())
            traccar_rows = cursor.fetchall()

            # Format hasil query Traccar ke dalam bentuk list of dictionary (JSON)
            #
            i = 0;
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
                        event_name = attr_dict.get("event", "unknown")
                        motion_status = attr_dict.get("motion", False)
                        ignation = attr_dict.get("ignition", False)
                        if event_name == "ignitionOn" or ignation == True:
                            i+=1
                            print(f"{i}. IMEI: {row[0]} -> disable: {disable},status: {status}, ignation: {ignation}, Motion: {motion_status}, Event: {event_name}")
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

@api_view(['GET'])
def monitoringalshintant(request,refas):


    print("this giw")
    
    bergerak = 0
    diam = 0
    berhenti = 0
    not_conected = 0
    not_actived = 0
    never_conected = 0 
    payload = []  # List ini akan kita gunakan untuk menampung hasil akhir dari Traccar

    # 1. AMBIL DAFTAR IMEI DARI DATABASE UTAMA (VEHICLES)
    imei_list = []



    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = [
        "v.imei != ''",
    ]

    params = []

    # refas filter
    if refas and refas.lower() != "semua":
        conditions.append("v.category_group_name ILIKE %s")
        params.append(f"%{refas}%")

    # location filters
    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
    SELECT distinct  v.imei
    FROM vehicles v
    """

    if conditions:
        qry += " WHERE " + " AND ".join(conditions)

    print(qry)
    print(params)
    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()
        
        # Bersihkan string imei langsung saat dimasukkan ke list
        imei_list = [str(row[0]).strip() for row in rows if row[0]]

    # 2. AMBIL DATA DARI DATABASE KEDUA (TRACCAR) MENGGUNAKAN KLAUSA "IN"


    if imei_list:
        placeholders = ", ".join(["%s"] * len(imei_list))

        qry2 = f"""
                SELECT 
                    td.uniqueid,
                    td.positionid,
                    tp.id,
                    tp.speed,
                    tp.servertime,
                    tp.devicetime,
                    td.disabled,
                    td.status,
                    tp.attributes,
                    tp.protocol 
                FROM tc_devices td
                INNER JOIN tc_positions tp ON td.positionid = tp.id
                WHERE td.uniqueid IN ({placeholders});
            """
        # Buat string placeholder %s dinamis sebanyak jumlah imei

        # print(qry2)
        # print(imei_list)

        with connections['second'].cursor() as cursor:
            cursor.execute(qry2, imei_list)
            # print(cursor.query.decode())
            traccar_rows = cursor.fetchall()

            # Format hasil query Traccar ke dalam bentuk list of dictionary (JSON)
            #
            i = 0;
            for row in traccar_rows:
                speed = row[3]
                status = row[7].strip()
                disable = row[6]
                protocol = row[9]
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
                        event_name = attr_dict.get("event", "unknown")
                        motion_status = attr_dict.get("motion", False)
                        ignation = attr_dict.get("ignition", False)
                        # if event_name == "ignitionOn" or ignation == True:
                            
                        #     print(f"{i}. IMEI: {row[0]} -> disable: {disable},status: {status}, ignation: {ignation}, Motion: {motion_status}, Event: {event_name}")
                    except Exception as e:
                        # Berjaga-jaga jika format JSON rusak di database
                        pass
                
                    
                    if protocol== "teltonika" and ignation == True  and motion_status ==True and disable == False and status == "online" :
                        bergerak += 1
                    elif protocol== "osmand" and  event_name == "deviceMoving" and motion_status ==True  and disable == False and status == "online" :
                        bergerak += 1

                    elif ignation == True and motion_status ==False and disable == False and status == "online":
                        diam+=1

                    elif disable == False and status == "online" and ignation == False:
                      berhenti+=1

                    elif  protocol== "osmand"  and event_name in ("deviceStopped", "ignitionOff") and motion_status ==False and disable == False and status == "online":
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



def build_filter_clause(request):
    clauses = []
    params = []
    
    # Mapping request query parameters to SQL columns
    filter_mappings = {
        'year': 'v.vehicle_year',
        'province': 'v.province',
        'regency': 'v.regency',
        'subdistrict': 'v.subdistrict',
        'ward': 'v.ward'
    }
    
    for param_name, sql_col in filter_mappings.items():
        vals = request.GET.getlist(param_name)
        vals = [v.strip() for v in vals if v.strip()]
        if vals:
            if len(vals) == 1:
                clauses.append(f"{sql_col} ILIKE %s")
                params.append(vals[0])
            else:
                lower_placeholders = ", ".join(["LOWER(%s)"] * len(vals))
                clauses.append(f"LOWER({sql_col}) IN ({lower_placeholders})")
                params.extend(vals)
                
    return clauses, params


@api_view(['GET'])
def testdrive_detail(request, refas, status):
    # Normalize status parameter
    status_lower = status.lower().strip()
    target_status = status_lower
    if status_lower == "not_connected":
        target_status = "not_conected"
    elif status_lower == "not_active":
        target_status = "not_actived"
    elif status_lower == "never_active":
        target_status = "never_conected"

    # 1. AMBIL DAFTAR IMEI & METADATA DARI DATABASE UTAMA (VEHICLES)
    vehicle_metadata = {}
    clauses, filter_params = build_filter_clause(request)
    
    sql = """
        SELECT v.imei, v.vehicle_name, v.vehicle_merk, v.plate_number, 
               v.recipient_name, v.province, v.regency, v.category_group_name
        FROM vehicles v 
        WHERE v.imei != '' 
    """
    params = []
    if refas != "semua":
        sql += " AND v.category_group_name != '' AND v.category_group_name ilike %s"
        params.append(refas)
    else:
        sql += " AND v.category_group_name != ''"
        
    for clause in clauses:
        sql += f" AND {clause}"
    params.extend(filter_params)

    with connections['default'].cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        for row in rows:
            if row[0]:
                imei = str(row[0]).strip()
                vehicle_metadata[imei] = {
                    "vehicle_name": row[1] if row[1] else "",
                    "vehicle_merk": row[2] if row[2] else "",
                    "plate_number": row[3] if row[3] else "",
                    "recipient_name": row[4] if row[4] else "",
                    "province": row[5] if row[5] else "",
                    "regency": row[6] if row[6] else "",
                    "category_group_name": row[7] if row[7] else ""
                }
    
    imei_list = list(vehicle_metadata.keys())
    payload = []

    # 2. AMBIL DATA DARI DATABASE KEDUA (TRACCAR) MENGGUNAKAN KLAUSA "IN"
    if imei_list:
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

            for row in traccar_rows:
                imei = row[0].strip() if row[0] else ""
                speed = row[3]
                status_val = row[7].strip() if row[7] else "unknown"
                disable = row[6]
                attributes_raw = row[8]
                motion_status = False
                ignation = False

                if attributes_raw:
                    try:
                        attr_dict = json.loads(attributes_raw) 
                        motion_status = attr_dict.get("motion", False)
                        ignation = attr_dict.get("ignition", False)
                    except Exception as e:
                        pass
                
                # Classify status matching testdrive classification logic
                item_status = "never_conected"
                if disable == False and status_val == "online" and ignation == True and motion_status == True:
                    item_status = "bergerak"
                elif ignation == True and motion_status == False:
                    item_status = "diam"
                elif disable == False and status_val == "online" and ignation == False:
                    item_status = "berhenti"
                elif disable == False and status_val == "unknown":
                    item_status = "not_conected"
                elif disable == True:
                    item_status = "not_actived"

                if item_status == target_status:
                    meta = vehicle_metadata.get(imei, {})
                    combined = {
                        "imei": imei,
                        "vehicle_name": meta.get("vehicle_name", ""),
                        "vehicle_merk": meta.get("vehicle_merk", ""),
                        "plate_number": meta.get("plate_number", ""),
                        "recipient_name": meta.get("recipient_name", ""),
                        "province": meta.get("province", ""),
                        "regency": meta.get("regency", ""),
                        "category_group_name": meta.get("category_group_name", ""),
                        "td_postid": row[1],
                        "tp_id": row[2],
                        "tp_speed": row[3],
                        "tp_servertime": row[4],
                        "tp_devicetime": row[5],  
                        "td_disabled": row[6],
                        "td_status": status_val,
                        "ignition": ignation,
                        "motion": motion_status
                    }
                    payload.append(combined)

    return JsonResponse(payload, safe=False)

@extend_schema(
    summary="Total Alsintan Count",
    description="""
    Returns total count of vehicles (alsintan) based on optional filters.

    Supports filtering by:
    - year
    - province
    - regency
    - subdistrict
    - ward
    """,
    parameters=[
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=TotalAlsintanSerializer,
    tags=["Alsintan"]
)
@api_view(['GET'])
def totalashintant(request):


    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = []
    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
    SELECT COUNT(v.vehicle_id)
    FROM vehicles v
    """

    if conditions:
        qry += " WHERE " + " AND ".join(conditions)

    print(qry)
    print(params)

    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        row = cursor.fetchone()

    payload = [{
        "count": row[0] if row else 0
    }]

    return JsonResponse(payload, safe=False)



@extend_schema(
    summary="Regency Vehicle Count",
    description="""
    Returns total vehicles grouped by regency.

    Supports filtering by:
    - year
    - province
    - regency
    - subdistrict
    - ward
    """,
    parameters=[
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=RegencyCountSerializer(many=True),
    tags=["Distribution"]
)
@api_view(['GET'])
def regencycount(request):

    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = []
    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
    SELECT
        v.regency,
        COUNT(v.vehicle_id)
    FROM vehicles v
    """

    if conditions:
        qry += " WHERE " + " AND ".join(conditions)

    qry += """
    GROUP BY v.regency
    ORDER BY COUNT(v.vehicle_id) DESC
    """

    print(qry)
    print(params)

    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()

    payload = []

    for row in rows:
        payload.append({
            "regency": (row[0] or "").upper(),
            "count": row[1]
        })

    return JsonResponse(payload, safe=False)

@extend_schema(
    summary="Subdistrict Vehicle Count",
    description="""
    Returns total vehicles grouped by subdistrict.

    Supports filtering by:
    - year
    - province
    - regency
    - subdistrict
    - ward
    """,
    parameters=[
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=SubdistrictCountSerializer(many=True),
    tags=["SEUBDistribution"]
)
@api_view(['GET'])
def subdistriccount(request):

    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = []
    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
    SELECT
        v.subdistrict,
        COUNT(v.vehicle_id)
    FROM vehicles v
    """

    if conditions:
        qry += " WHERE " + " AND ".join(conditions)

    qry += """
    GROUP BY v.subdistrict
    ORDER BY COUNT(v.vehicle_id) DESC
    """

    print(qry)
    print(params)

    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()

    payload = []

    for row in rows:
        payload.append({
            "subdistric": (row[0] or "").upper(),
            "count": row[1]
        })

    return JsonResponse(payload, safe=False)


@extend_schema(
    summary="Ward Vehicle Count",
    description="""
    Returns total vehicles grouped by ward.

    Supports filtering by:
    - year
    - province
    - regency
    - subdistrict
    - ward
    """,
    parameters=[
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=WardCountSerializer(many=True),
    tags=["Distribution"]
)
@api_view(['GET'])
def wardcount(request):

    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = []
    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
    SELECT
        v.ward,
        COUNT(v.vehicle_id)
    FROM vehicles v
    """

    if conditions:
        qry += " WHERE " + " AND ".join(conditions)

    qry += """
    GROUP BY v.ward
    ORDER BY COUNT(v.vehicle_id) DESC
    """

    print(qry)
    print(params)

    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()

    payload = []

    for row in rows:
        payload.append({
            "ward": (row[0] or "").upper(),
            "count": row[1]
        })

    return JsonResponse(payload, safe=False)


@extend_schema(
    summary="Province Vehicle Count",
    description="""
    Returns total vehicles grouped by province.

    Supports filtering by:
    - year
    - province
    - regency
    - subdistrict
    - ward
    """,
    parameters=[
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=ProvinceCountSerializer(many=True),
    tags=["Distribution"]
)
def provincecount(request):


    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = []
    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
    SELECT
        v.province,
        COUNT(v.vehicle_id)
    FROM vehicles v
    """

    if conditions:
        qry += " WHERE " + " AND ".join(conditions)

    qry += """
    GROUP BY v.province
    ORDER BY COUNT(v.vehicle_id) DESC
    """

    print(qry)
    print(params)

    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()

    payload = []

    for row in rows:
        payload.append({
            "province": (row[0] or "").upper(),
            "count": row[1]
        })

    return JsonResponse(payload, safe=False)


@extend_schema(
    summary="Recipment Group Count",
    description="""
    Returns total vehicle count grouped by category_group_name (recipment group).

    No filters applied.
    """,
    responses=RecipmentCountSerializer(many=True),
    tags=["Distribution"]
)
@api_view(['GET'])
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


@extend_schema(
    summary="Jenis Alsintan Count",
    description="""
    Returns total count of vehicles grouped by vehicle name (jenis alsintan).

    Supports filtering by:
    - year
    - province
    - regency
    - subdistrict
    - ward
    """,
    parameters=[
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=JenisAlsintanSerializer(many=True),
    tags=["Alsintan"]
)
@api_view(['GET'])
def jenisalsintan(request):

    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = []
    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
    SELECT
        v.vehicle_name,
        COUNT(v.vehicle_id)
    FROM vehicles v
    """

    if conditions:
        qry += " WHERE " + " AND ".join(conditions)

    qry += """
    GROUP BY v.vehicle_name
    ORDER BY COUNT(v.vehicle_id) DESC
    """

    print(qry)
    print(params)

    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()

    payload = []

    for row in rows:
        payload.append({
            "vehicle_name": (row[0] or "").upper(),
            "count": row[1]
        })

    return JsonResponse(payload, safe=False)



@extend_schema(
    summary="Recipient Group Engine Hours vs Distance",
    description="""
    Returns total engine hours and distance grouped by recipient group.

    Filters:
    - year
    - province
    - regency
    - subdistrict
    - ward

    Only includes non-empty category_group_name values.
    """,
    parameters=[
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=RecipientGroupHourVsKmSerializer(many=True),
    tags=["Analytics"]
)
@api_view(['GET'])
def recipientgrouphourvskm(request):

    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = [
        "v.category_group_name IS NOT NULL",
        "v.category_group_name <> ''"
    ]

    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
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
    """

    qry += " WHERE " + " AND ".join(conditions)

    qry += """
    GROUP BY v.category_group_name
    ORDER BY v.category_group_name
    """

    print(qry)
    print(params)

    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()

    payload = []

    for row in rows:
        payload.append({
            "recipient_group": (row[0] or "").upper(),
            "sum_engine_hours": float(row[1] or 0),
            "sum_distance_km": float(row[2] or 0)
        })

    return JsonResponse(payload, safe=False)
    
@extend_schema(
    summary="Province Engine Hours vs Distance",
    description="""
    Returns total engine hours and distance grouped by province.

    Filters supported:
    - year
    - province
    - regency
    - subdistrict
    - ward
    """,
    parameters=[
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=ProvHourVsKmSerializer(many=True),
    tags=["Analytics"]
)
 
@api_view(['GET'])
def provhourvskm(request):
    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = [
        "v.province IS NOT NULL",
        "v.province <> ''"
    ]

    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
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
    """

    qry += " WHERE " + " AND ".join(conditions)

    qry += """
    GROUP BY v.province
    ORDER BY v.province
    """

    print(qry)
    print(params)

    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()

    payload = []

    for row in rows:
        payload.append({
            "province": (row[0] or "").upper(),
            "sum_engine_hours": float(row[1] or 0),
            "sum_distance_km": float(row[2] or 0)
        })

    return JsonResponse(payload, safe=False)
@extend_schema(
    summary="Regency Engine Hours vs Distance",
    description="""
    Returns total engine hours and distance grouped by regency.

    Filters:
    - year
    - province
    - regency
    - subdistrict
    - ward

    Excludes empty regency and 'Brigade Dinas'.
    """,
    parameters=[
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=KabupatenHourVsKmSerializer(many=True),
    tags=["Analytics"]
)
@api_view(['GET'])
def kabupatenhourvskm(request):


    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = [
        "v.regency IS NOT NULL",
        "v.regency <> ''",
        "v.regency != 'Brigade Dinas'"
    ]

    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
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
    """

    qry += " WHERE " + " AND ".join(conditions)

    qry += """
    GROUP BY v.regency
    ORDER BY v.regency
    """

    print(qry)
    print(params)

    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()

    payload = []

    for row in rows:
        payload.append({
            "regency": row[0].upper(),
            "sum_engine_hours": float(row[1] or 0),
            "sum_distance_km": float(row[2] or 0)
        })

    return JsonResponse(payload, safe=False)
    

@extend_schema(
    summary="Vehicle Location Data",
    description="""
    Returns all vehicle coordinates along with province,
    regency, and vehicle brand information.

    Data is cached for 5 minutes.
    """,
    responses=PurJurnalSerializer(many=True),
    tags=["Dashboard"]
)

@api_view(['GET'])
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
     


@api_view(['GET'])
def selectdistribution(request, gn):

    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    qry = """
    SELECT
        v.category_group_name AS group_name,
        COUNT(v.vehicle_id) AS total
    FROM vehicles v
    """

    conditions = [
        "v.category_group_name ILIKE %s"
    ]

    params = [gn]

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry += " WHERE " + " AND ".join(conditions)

    qry += """
    GROUP BY v.category_group_name
    """

    print(qry)
    print(params)

    with connections['default'].cursor() as cursor:
        cursor.execute(qry, params)
        rows = cursor.fetchall()

    if rows:
        payload = {
            "group_name": rows[0][0],
            "total": rows[0][1]
        }
    else:
        payload = {
            "group_name": gn,
            "total": 0
        }

    return JsonResponse(payload, safe=False)
     


extend_schema(
    summary="Distribution by Recipient Group",
    description="""
    Returns vehicle distribution grouped by recipient group.

    Supports filtering by:
    - year
    - province
    - regency
    - subdistrict
    - ward

    Includes a 'Total' row generated using SQL ROLLUP.
    """,
    parameters=[
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward"
        ),
    ],
    responses=DistributionSerializer(many=True),
    tags=["Distribution"]
)
@api_view(['GET'])
def distribution(request):






    year = request.GET.get('year', '').strip()
    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    conditions = []
    params = []

    if year:
        conditions.append("v.vehicle_year = %s")
        params.append(year)

    if province:
        conditions.append("v.province ILIKE %s")
        params.append(f"%{province}%")

    if regency:
        conditions.append("v.regency ILIKE %s")
        params.append(f"%{regency}%")

    if subdistrict:
        conditions.append("v.subdistrict ILIKE %s")
        params.append(f"%{subdistrict}%")

    if ward:
        conditions.append("v.ward ILIKE %s")
        params.append(f"%{ward}%")

    qry = """
    SELECT
        COALESCE(v.recipient_group, 'Total') AS group_name,
        COUNT(*) AS total
    FROM vehicles v
    """

    if conditions:
        qry += " WHERE " + " AND ".join(conditions)

    qry += """
    GROUP BY ROLLUP(v.recipient_group)
    ORDER BY (v.recipient_group IS NULL) ASC, total DESC
    """

    if cache.get("distribution1") is not None:
            print("Key exists")
             # print(cache.get("name"))
            print("Using Caching")
            payload = cache.get("distribution")
    with connections['default'].cursor() as cursor:
                cursor.execute(qry,params)

                rows = cursor.fetchall()
                
                payload = []

                for row in rows:
                    data={}
                    data["group_name"] = row[0]
                    data["total"] = row[1]
                    payload.append(data)
                cache.set("distribution", payload, timeout=300)    
    return JsonResponse(payload, safe=False)



@extend_schema(
    summary="Service Center Locations",
    description="""
    Returns all service center locations.

    Data includes:
    - Service center name
    - Coordinates
    - Province
    - Regency
    - Address
    - Phone number

    Results are cached for 5 minutes.
    """,
    responses=ServiceSerializer(many=True),
    tags=["Services"]
)
@api_view(['GET'])
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


@extend_schema(
    summary="Vehicle Geofence Data",
    description="""
    Returns vehicle information used for geofence monitoring.

    Currently event and time fields are placeholders and may be null.

    Data is cached for 5 minutes.
    """,
    responses=GeofenceSerializer(many=True),
    tags=["Geofence"]
)
@api_view(['GET'])
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

@extend_schema(
    summary="Alsintan Data",
    description="""
    Returns vehicle/alsintan information.

    Supports filtering by:
    - jenis (vehicle_name)
    - year
    - province
    - regency
    - subdistrict
    - ward
    """,
    parameters=[
               OpenApiParameter(
            name="_from",
            type=str,
            default="swagger",
            required=False,
            description="internal flag"
        ),
        OpenApiParameter(
            name="jenis",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle type/name. Supports multiple values or comma-separated values."
        ),
 
        OpenApiParameter(
            name="vehicle_name",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Alias for jenis."
        ),
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward"
        ),
    ],
    responses=AlsintanSerializer(many=True),
    tags=["Alsintan"]
)
@api_view(['GET'])
def alsintan(request):

    # Parse and clean multiple year parameter (supports repeated keys and comma separation)
    raw_year = request.GET.getlist('year')
    year_list = []
    for item in raw_year:
        for val in item.split(','):
            if val.strip():
                year_list.append(val.strip())

    # Parse and clean multiple jenis parameter (supports repeated keys and comma separation)
    raw_jenis = request.GET.getlist('jenis') + request.GET.getlist('vehicle_name')
    jenis_list = []
    for item in raw_jenis:
        for val in item.split(','):
            if val.strip():
                jenis_list.append(val.strip())

    province = request.GET.get('province', '').strip()
    regency = request.GET.get('regency', '').strip()
    subdistrict = request.GET.get('subdistrict', '').strip()
    ward = request.GET.get('ward', '').strip()

    # Build cache key using sorted values to ensure consistency
    sorted_years = sorted(list(set(year_list)))
    sorted_jenis = sorted(list(set(jenis_list)))
    print("Sorted Years:", sorted_years)
    print("Sorted Jenis:", sorted_jenis)
    keyname = (
        "alsintan_"
        + ",".join(sorted_years) + "_"
        + ",".join(sorted_jenis) + "_"
        + province + "_"
        + regency + "_"
        + subdistrict + "_"
        + ward
    )

    print(keyname)

    if cache.get(keyname) is not None:
        print("Key exists")
        print("Using Caching")
        payload = cache.get(keyname)
    else:
        print("Key not found")
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

        if jenis_list:
            lower_placeholders = ", ".join(["LOWER(%s)"] * len(jenis_list))
            conditions.append(f"LOWER(v.vehicle_name) IN ({lower_placeholders})")
            params.extend(jenis_list)

        if year_list:
            placeholders = ", ".join(["%s"] * len(year_list))
            conditions.append(f"v.vehicle_year IN ({placeholders})")
            params.extend(year_list)

        if province:
            conditions.append("v.province ILIKE %s")
            params.append(f"%{province}%")

        if regency:
            conditions.append("v.regency ILIKE %s")
            params.append(f"%{regency}%")

        if subdistrict:
            conditions.append("v.subdistrict ILIKE %s")
            params.append(f"%{subdistrict}%")

        if ward:
            conditions.append("v.ward ILIKE %s")
            params.append(f"%{ward}%")

        if conditions:
            qry += " WHERE " + " AND ".join(conditions)

        with connections['default'].cursor() as cursor:
            cursor.execute(qry, params)
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

        cache.set(keyname, payload, timeout=300) 



    is_swagger = request.GET.get("_from") == "swagger"
    if is_swagger:
        payload = payload[:100]  
    return JsonResponse(payload[:10], safe=False)

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

@extend_schema(
    summary="Average Engine Hours",
    description="""
    Returns the average engine hours for vehicles filtered by category and optional filters.

    Notes:
    - engine_hours is validated as numeric before averaging
    - category is required as path parameter
    """,
    parameters=[
        OpenApiParameter(
            name="category",
            type=str,
            location=OpenApiParameter.PATH,
            description="Vehicle category (e.g. alsintan, tractor, etc.)"
        ),
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year filter (if supported by build_filter_clause)"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=AverageEngineHoursSerializer,
    tags=["Analytics"]
)
@api_view(['GET'])
def average_engine_hours(request, category):
    category_lower = category.lower().strip()
    clauses, filter_params = build_filter_clause(request)
    
    sql = r"""
        SELECT AVG(
            CASE
                WHEN v.engine_hours ~ '^[0-9]+(\.[0-9]+)?$'
                THEN v.engine_hours::NUMERIC
                ELSE NULL
            END
        ) AS avg_hours
        FROM vehicles v
        WHERE 1=1
    """
    params = []
    if category_lower != "alsintan":
        sql += " AND v.category_group_name ILIKE %s"
        params.append(category_lower)
        
    for clause in clauses:
        sql += f" AND {clause}"
    params.extend(filter_params)
    
    with connections['default'].cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
        avg_val = float(row[0]) if row[0] is not None else 0.0
        
    return JsonResponse({
        "category": category,
        "average_engine_hours": avg_val
    })

@extend_schema(
    summary="Average Distance (KM)",
    description="""
    Returns the average distance (km) for vehicles filtered by category and optional filters.

    Notes:
    - distance_km is validated as numeric before averaging
    - category is required as path parameter
    """,
    parameters=[
        OpenApiParameter(
            name="category",
            type=str,
            location=OpenApiParameter.PATH,
            description="Vehicle category (e.g. alsintan, tractor, etc.)"
        ),
        OpenApiParameter(
            name="year",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Vehicle year filter (if supported by build_filter_clause)"
        ),
        OpenApiParameter(
            name="province",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Province filter"
        ),
        OpenApiParameter(
            name="regency",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Regency filter"
        ),
        OpenApiParameter(
            name="subdistrict",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Subdistrict filter"
        ),
        OpenApiParameter(
            name="ward",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Ward filter"
        ),
    ],
    responses=AverageDistanceKmSerializer,
    tags=["Analytics"]
)
@api_view(['GET'])
def average_distance_km(request, category):
    category_lower = category.lower().strip()
    clauses, filter_params = build_filter_clause(request)
    
    sql = r"""
        SELECT AVG(
            CASE
                WHEN v.distance_km ~ '^[0-9]+(\.[0-9]+)?$'
                THEN v.distance_km::NUMERIC
                ELSE NULL
            END
        ) AS avg_dist
        FROM vehicles v
        WHERE 1=1
    """
    params = []
    if category_lower != "alsintan":
        sql += " AND v.category_group_name ILIKE %s"
        params.append(category_lower)
        
    for clause in clauses:
        sql += f" AND {clause}"
    params.extend(filter_params)
    
    with connections['default'].cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
        avg_val = float(row[0]) if row[0] is not None else 0.0
        
    return JsonResponse({
        "category": category,
        "average_distance_km": avg_val
    })


@api_view(['GET'])
def purna_jual_list(request):
    clauses = []
    params = []
    
    # Optional query filters
    province = request.GET.get('province')
    if province:
        clauses.append("province ILIKE %s")
        params.append(province)
        
    regency = request.GET.get('regency')
    if regency:
        clauses.append("regency ILIKE %s")
        params.append(regency)
        
    brand = request.GET.get('brand')
    if brand:
        clauses.append("brand ILIKE %s")
        params.append(brand)
        
    sql = """
        SELECT purna_jual_id, brand, name, latitude_longitude, province, regency, address, phone_number
        FROM purna_jual
    """
    
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
        
    payload = []
    with connections['default'].cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        for row in rows:
            data = {}
            data["purna_jual_id"] = str(row[0])
            data["brand"] = row[1] if row[1] else ""
            data["name"] = row[2] if row[2] else ""
            
            # Extract lat/lng
            lat, long = "", ""
            if row[3]:
                try:
                    parts = row[3].split(",")
                    if len(parts) == 2:
                        lat = float(parts[0].strip())
                        long = float(parts[1].strip())
                except:
                    pass
            
            data["lat"] = lat
            data["lng"] = long
            data["province"] = row[4] if row[4] else ""
            data["regency"] = row[5] if row[5] else ""
            data["address"] = row[6] if row[6] else ""
            data["phone_number"] = row[7] if row[7] else ""
            
            payload.append(data)
            
    return JsonResponse(payload, safe=False)


