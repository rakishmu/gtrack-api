from django.shortcuts import render

from django.http import JsonResponse
from django.db import connections
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache

import json


# Create your views here.
def GetProvince(request):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
                    SELECT DISTINCT mw.province
                    FROM master_wilayah mw
                    ORDER BY mw.province;
            """)

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                payload.append( row[0])
    return JsonResponse(payload, safe=False)


def Getregency(request,province):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT mw.regency 
                FROM master_wilayah mw
                WHERE mw.province ILIKE %s;
            """,[province])

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                payload.append( row[0])
    return JsonResponse(payload, safe=False)

def Getsubdistrict(request,regency):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT mw.subdistrict 
                FROM master_wilayah mw
                WHERE mw.regency ILIKE %s;
            """,[regency])

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                payload.append( row[0])
    return JsonResponse(payload, safe=False)


def Getward(request,regency,subdistrict):

    with connections['default'].cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT mw.ward 
                FROM master_wilayah mw
                WHERE mw.subdistrict ILIKE %s and mw.regency ILIKE %s ;
            """,[subdistrict,regency])

            rows = cursor.fetchall()
            
            payload = []

            for row in rows:    
                payload.append( row[0])
    return JsonResponse(payload, safe=False)

