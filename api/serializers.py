from rest_framework import serializers
from .models import *

class SchemaMigrationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaMigrations
        fields = '__all__'

class SatFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SatFiles
        fields = '__all__'

class DownloadEntriesArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownloadEntriesArchive
        fields = '__all__'

class UploadEntriesArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadEntriesArchive
        fields = '__all__'

class DbFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbFiles
        fields = '__all__'

class DownloadGapsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DownloadGaps
        fields = '__all__'

class UploadGapsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadGaps
        fields = '__all__'