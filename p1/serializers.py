from rest_framework import serializers

class PurJurnalSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    provinsi = serializers.CharField()
    kabupaten = serializers.CharField()
    merk = serializers.CharField()


class ServiceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    lat = serializers.FloatField()
    long = serializers.FloatField()
    provinsi = serializers.CharField()
    kabupaten = serializers.CharField()
    alamat = serializers.CharField()
    phone = serializers.CharField()



class GeofenceSerializer(serializers.Serializer):
    nomorRangka = serializers.CharField(allow_null=True)
    nomorMesin = serializers.CharField(allow_null=True)
    namaBarang = serializers.CharField(allow_null=True)
    merk = serializers.CharField(allow_null=True)
    tipe = serializers.CharField(allow_null=True)
    provinsi = serializers.CharField(allow_null=True)
    kabupaten = serializers.CharField(allow_null=True)
    event = serializers.CharField(allow_null=True)
    time = serializers.CharField(allow_null=True)

class AlsintanSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tahun = serializers.CharField(allow_null=True)
    nomorRangka = serializers.CharField(allow_null=True)
    nomorMesin = serializers.CharField(allow_null=True)
    namaBarang = serializers.CharField(allow_null=True)
    merk = serializers.CharField(allow_null=True)
    tipe = serializers.CharField(allow_null=True)
    pihak = serializers.CharField(allow_null=True)
    kelompok = serializers.CharField(allow_null=True)
    nama = serializers.CharField(allow_null=True)
    telp = serializers.CharField(allow_null=True)
    alamat = serializers.CharField(allow_null=True)
    provinsi = serializers.CharField(allow_null=True)
    kabupaten = serializers.CharField(allow_null=True)
    kecamatan = serializers.CharField(allow_null=True)
    kelurahan = serializers.CharField(allow_null=True)
    engineHour = serializers.CharField(allow_null=True)
    km = serializers.CharField(allow_null=True)
    lat = serializers.CharField(allow_null=True)
    lng = serializers.CharField(allow_null=True)
    lastUpdated = serializers.CharField(allow_null=True)


class AlsintanPaginatedSerializer(serializers.Serializer):
    total_items = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    current_page = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    results = AlsintanSerializer(many=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['from'] = serializers.IntegerField(allow_null=True)
        self.fields['to'] = serializers.IntegerField(allow_null=True)


class DistributionSerializer(serializers.Serializer):
    group_name = serializers.CharField()
    total = serializers.IntegerField()


class KabupatenHourVsKmSerializer(serializers.Serializer):
    regency = serializers.CharField()
    sum_engine_hours = serializers.FloatField()
    sum_distance_km = serializers.FloatField()





class RecipientGroupHourVsKmSerializer(serializers.Serializer):
    recipient_group = serializers.CharField()
    sum_engine_hours = serializers.FloatField()
    sum_distance_km = serializers.FloatField()


class JenisAlsintanSerializer(serializers.Serializer):
    vehicle_name = serializers.CharField()
    count = serializers.IntegerField()


class RecipmentCountSerializer(serializers.Serializer):
    recipment_group = serializers.CharField()
    count = serializers.IntegerField()

class ProvinceCountSerializer(serializers.Serializer):
    province = serializers.CharField()
    count = serializers.IntegerField()


class RegencyCountSerializer(serializers.Serializer):
    regency = serializers.CharField()
    count = serializers.IntegerField()

class SubdistrictCountSerializer(serializers.Serializer):
    subdistrict = serializers.CharField()
    count = serializers.IntegerField()

class WardCountSerializer(serializers.Serializer):
    ward = serializers.CharField()
    count = serializers.IntegerField()

class TotalAlsintanSerializer(serializers.Serializer):
    count = serializers.IntegerField()

class ProvHourVsKmSerializer(serializers.Serializer):
    province = serializers.CharField()
    sum_engine_hours = serializers.FloatField()
    sum_distance_km = serializers.FloatField()


class AverageEngineHoursSerializer(serializers.Serializer):
    category = serializers.CharField()
    average_engine_hours = serializers.FloatField()

class AverageDistanceKmSerializer(serializers.Serializer):
    category = serializers.CharField()
    average_distance_km = serializers.FloatField()