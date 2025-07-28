from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db import connection
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
import json
import pandas as pd
from io import StringIO, BytesIO
from PIL import Image
import io
from django_otp.plugins.otp_totp.models import TOTPDevice
from two_factor.utils import default_device
import logging

logger = logging.getLogger(__name__)

# Helper Functions
def get_satellite(sat_id):
    """
    Returns the name of the satellite schema.
    We have only two satellites, "RIBAT-SAT" and "UM5-EOSAT"
    """
    try:
        sat_id = int(sat_id)
        if sat_id == 1:
            return "UM5-EOSAT"
        elif sat_id == 2:
            return "RIBAT-SAT"
        else:
            raise ValueError(f"Satellite ID {sat_id} does not exist in the database.")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid satellite ID: {str(e)}")

def set_search_path(schema):
    """Set the database search path to the specified schema"""
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{schema}"')

# API Views
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow public access if needed
def satellite_list(request):
    """
    GET /api/satellites/
    Returns the list of available satellites
    """
    logger.info(f"Fetching satellites for user {request.user.username if request.user.is_authenticated else 'anonymous'}")
    data = {
        "satellites": [
            {"id": 1, "name": "UM5-EOSAT"},
            {"id": 2, "name": "RIBAT-SAT"}
        ]
    }
    return Response({"status": "success", "data": data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def satellite_subsystems(request, sat_id):
    """
    GET /api/satellites/<int:sat_id>/subsystems/
    Returns unique subsystem IDs for the specified satellite
    """
    try:
        name = get_satellite(sat_id)
        logger.info(f"Fetching subsystems for satellite {sat_id}, user {request.user.username}")
        with connection.cursor() as cursor:
            cursor.execute(
                f'''SELECT DISTINCT subsystem_id as id 
                    FROM "{name}".sat_files 
                    ORDER BY subsystem_id'''
            )
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        return Response({
            "status": "success",
            "satellite_id": sat_id,
            "subsystems": data
        })
        
    except ValueError as e:
        logger.error(f"Error fetching subsystems for satellite {sat_id}: {str(e)}")
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Database error for satellite {sat_id}: {str(e)}")
        return Response(
            {"status": "error", "detail": f"Database error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subsystem_files(request, sat_id, sub_id):
    """
    GET /api/satellites/<int:sat_id>/subsystems/<int:sub_id>/files/
    Returns files for a specific subsystem
    """
    try:
        name = get_satellite(sat_id)
        logger.info(f"Fetching files for satellite {sat_id}, subsystem {sub_id}, user {request.user.username}")
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT 
                    id_in_subsystem as file_id,
                    COUNT(*) as version_numero
                FROM "{name}".sat_files 
                WHERE subsystem_id = %s
                GROUP BY id_in_subsystem
                ORDER BY id_in_subsystem
                ''',
                [sub_id]
            )
            columns = [col[0] for col in cursor.description]
            data = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
        return Response({
            "status": "success",
            "satellite_id": sat_id,
            "subsystem_id": sub_id,
            "files": data
        })
        
    except Exception as e:
        logger.error(f"Error fetching files for satellite {sat_id}, subsystem {sub_id}: {str(e)}")
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def file_versions(request, sat_id, sub_id, id_in_subsystem):
    """
    GET /api/satellites/<sat_id>/subsystems/<sub_id>/files/<id_in_subsystem>/
    """
    try:
        schema = get_satellite(sat_id)
        logger.info(f"Fetching versions for file {id_in_subsystem}, satellite {sat_id}, subsystem {sub_id}, user {request.user.username}")
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT df.*
                  FROM "{schema}".db_files AS df
                  JOIN "{schema}".sat_files AS sf
                    ON df.sat_file_id = sf.id
                 WHERE sf.id_in_subsystem = %s      
                   AND sf.subsystem_id    = %s
                 ORDER BY df.file_ver;              
                ''',
                [id_in_subsystem, sub_id],
            )
            rows = cursor.fetchall()

        if not rows:
            return Response(
                {"status": "error", "detail": "No versions found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        columns = [c[0] for c in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        return Response({"status": "success", "data": data})

    except Exception as e:
        logger.error(f"Error fetching versions for file {id_in_subsystem}: {str(e)}")
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def file_metadata(request, sat_id, sub_id, id_in_subsystem, file_ver): 
    """
    GET /api/satellites/<sat_id>/subsystems/<sub_id>/files/<id_in_subsystem>/<file_ver>
    """
    try:
        schema = get_satellite(sat_id)
        logger.info(f"Fetching metadata for file {id_in_subsystem}, version {file_ver}, satellite {sat_id}, subsystem {sub_id}, user {request.user.username}")
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT df.*
                  FROM "{schema}".db_files AS df
                  JOIN "{schema}".sat_files AS sf
                    ON df.sat_file_id = sf.id
                 WHERE sf.id_in_subsystem = %s         
                   AND sf.subsystem_id    = %s
                   AND df.file_ver        = %s;
                ''',
                [id_in_subsystem, sub_id, file_ver], 
            )
            row = cursor.fetchone()

        if row is None:
            return Response(
                {"status": "error", "detail": "File version not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        columns = [c[0] for c in cursor.description]
        return Response({"status": "success", "data": dict(zip(columns, row))})

    except Exception as e:
        logger.error(f"Error fetching metadata for file {id_in_subsystem}, version {file_ver}: {str(e)}")
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_file(request, sat_id, sub_id, id_in_subsystem, file_ver):
    """
    GET /api/satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/version/<int:file_ver>/download
    Downloads a specific file version
    """
    try:
        schema = get_satellite(sat_id)
        logger.info(f"Downloading file {id_in_subsystem}, version {file_ver}, satellite {sat_id}, subsystem {sub_id}, user {request.user.username}")
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT dea.entry_data
                FROM "{schema}".download_entries_archive AS dea
                JOIN "{schema}".sat_files AS sf ON sf.id = dea.sat_file_id
                WHERE sf.id_in_subsystem = %s
                AND sf.subsystem_id = %s
                AND dea.file_ver = %s
                ORDER BY dea.entry_nr
                ''',
                [id_in_subsystem, sub_id, file_ver]
            )
            rows = cursor.fetchall()

        if not rows:
            return Response(
                {"status": "error", "detail": "File not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        file_bytes = b''.join(bytes(r[0]) for r in rows)
        filename = f"sat{sat_id}_sub{sub_id}_file{id_in_subsystem}_v{file_ver}.bin"

        response = HttpResponse(
            file_bytes,
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(file_bytes)
        return response

    except Exception as e:
        logger.error(f"Error downloading file {id_in_subsystem}, version {file_ver}: {str(e)}")
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parsed_file(request, sat_id, sub_id, id_in_subsystem, file_ver, format):
    """
    GET /api/satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/version/<int:file_ver>/parsed/<str:format>/
    Returns parsed file data in specified format
    """
    try:
        schema = get_satellite(sat_id)
        logger.info(f"Parsing file {id_in_subsystem}, version {file_ver}, format {format}, satellite {sat_id}, subsystem {sub_id}, user {request.user.username}")
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT dea.entry_data
                FROM "{schema}".download_entries_archive AS dea
                JOIN "{schema}".sat_files AS sf ON sf.id = dea.sat_file_id
                WHERE sf.id_in_subsystem = %s
                AND sf.subsystem_id = %s
                AND dea.file_ver = %s
                ORDER BY dea.entry_nr
                ''',
                [id_in_subsystem, sub_id, file_ver]
            )
            rows = cursor.fetchall()

        if not rows:
            return Response(
                {"status": "error", "detail": "File not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        file_bytes = b''.join(bytes(r[0]) for r in rows)
        filename = f"sat{sat_id}_sub{sub_id}_file{id_in_subsystem}_v{file_ver}"

        if format.lower() == 'txt':
            response = HttpResponse(
                file_bytes.decode('utf-8'),
                content_type='text/plain'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}.txt"'
            return response

        elif format.lower() == 'csv':
            df = pd.read_json(BytesIO(file_bytes))
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            response = HttpResponse(
                csv_buffer.getvalue(),
                content_type='text/csv'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
            return response

        elif format.lower() == 'json':
            json_data = json.loads(file_bytes.decode('utf-8'))
            return Response({
                "status": "success",
                "data": json_data
            })

        elif format.lower() in ('png', 'jpg', 'jpeg'):
            img = Image.open(io.BytesIO(file_bytes))
            img_io = io.BytesIO()
            img.save(img_io, format=format.upper())
            response = HttpResponse(
                img_io.getvalue(),
                content_type=f'image/{format.lower()}'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}.{format.lower()}"'
            return response

        else:
            return Response(
                {"status": "error", "detail": f"Unsupported format: {format}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.error(f"Error parsing file {id_in_subsystem}, version {file_ver}, format {format}: {str(e)}")
        return Response(
            {"status": "error", "detail": f"Could not parse file: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAdminUser])
def system_status(request):
    """
    GET /api/admin/system-status/
    Returns system administration statistics
    """
    try:
        logger.info(f"Fetching system status for user {request.user.username}")
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM auth_user WHERE is_active=True')
            active_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM auth_user WHERE is_superuser=True')
            admin_users = cursor.fetchone()[0]
            
        return Response({
            "status": "success",
            "data": {
                "active_users": active_users,
                "admin_users": admin_users,
                "satellites": [
                    {"id": 1, "name": "UM5-EOSAT"},
                    {"id": 2, "name": "RIBAT-SAT"}
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching system status: {str(e)}")
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def two_factor_status(request):
    """
    GET /account/two_factor/
    Returns 2FA status for the current user
    """
    try:
        user = request.user
        logger.info(f"Checking 2FA status for user {user.username}")
        device = default_device(user)
        return Response({
            "required": True,  # 2FA is always required in this setup
            "enabled": bool(device)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error checking 2FA status for user {user.username}: {str(e)}")
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )