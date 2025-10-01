import datetime
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
        sat_id = int(sat_id)  # Ensure sat_id is integer
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
def satellite_list(request):
    """
    GET /api/satellites/
    Returns the list of available satellites
    """
    data = {
        "satellites": [
            {"id": 1, "name": "UM5-EOSAT"},
            {"id": 2, "name": "RIBAT-SAT"}
        ]
    }
    return Response({"status": "success", "data": data})

@api_view(['GET'])
def satellite_subsystems(request, sat_id):
    """
    GET /api/satellites/<int:sat_id>/subsystems/
    Returns unique subsystem IDs for the specified satellite
    """
    try:
        name = get_satellite(sat_id)
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
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"status": "error", "detail": f"Database error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def subsystem_files(request, sat_id, sub_id):
    """
    GET /api/satellites/<int:sat_id>/subsystems/<int:sub_id>/files/
    Returns files for a specific subsystem
    """
    try:
        name = get_satellite(sat_id)
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
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def file_versions(request, sat_id, sub_id, id_in_subsystem):
    """
    GET /api/satellites/<sat_id>/subsystems/<sub_id>/files/<id_in_subsystem>/
    """
    try:
        schema = get_satellite(sat_id)          

        # First check if the file exists
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT COUNT(*)
                FROM "{schema}".sat_files
                WHERE id_in_subsystem = %s
                AND subsystem_id = %s
                ''',
                [id_in_subsystem, sub_id]
            )
            file_count = cursor.fetchone()[0]
            
            if file_count == 0:
                return Response({
                    "status": "error", 
                    "detail": f"File not found in satellite {sat_id}, subsystem {sub_id}"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # File exists, now it tries to get versions
            cursor.execute(
                f'''
                SELECT df.*
                FROM "{schema}".db_files AS df
                JOIN "{schema}".sat_files AS sf
                    ON df.sat_file_id = sf.id
                WHERE sf.id_in_subsystem = %s      
                AND sf.subsystem_id = %s
                ORDER BY df.file_ver;              
                ''',
                [id_in_subsystem, sub_id],
            )
            rows = cursor.fetchall()
            
            # Return empty data array when no versions found (this is the key fix)
            if not rows:
                return Response({"status": "success", "data": []})

            columns = [c[0] for c in cursor.description]
            data = [dict(zip(columns, row)) for row in rows]
            return Response({"status": "success", "data": data})
                
    except Exception as e:
        return Response({
            "status": "error", 
            "detail": f"Server error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    


@api_view(['GET'])
def file_metadata(request, sat_id, sub_id, id_in_subsystem, file_ver): 
    """
    GET /api/satellites/<sat_id>/subsystems/<sub_id>/files/<id_in_subsystem>/version/<file_ver>/
    """
    try:
        schema = get_satellite(sat_id)
        
        print(f"Metadata request: sat={sat_id}, schema={schema}, sub={sub_id}, file={id_in_subsystem}, ver={file_ver}")

        # First, get sat_file_id from sat_files table
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT id
                FROM "{schema}".sat_files
                WHERE id_in_subsystem = %s
                AND subsystem_id = %s
                ''',
                [id_in_subsystem, sub_id]
            )
            row = cursor.fetchone()
            
            if not row:
                return Response({
                    "status": "error", 
                    "detail": f"File not found in satellite {sat_id}, subsystem {sub_id}"
                }, status=status.HTTP_404_NOT_FOUND)
            
            sat_file_id = row[0]
            
            # Get metadata from db_files table
            cursor.execute(
                f'''
                SELECT file_ver, sat_file_id, init_ts, update_ts, type_id, capacity, 
                       last_entry, remaining_seq_nr, total_seq_nr, removed
                FROM "{schema}".db_files
                WHERE sat_file_id = %s
                AND file_ver = %s
                ''',
                [sat_file_id, file_ver]
            )
            row = cursor.fetchone()
            
            if not row:
                return Response({
                    "status": "success", 
                    "data": {
                        "file_id": id_in_subsystem,
                        "version": file_ver,
                        "message": "No metadata available for this version"
                    }
                })
            
            columns = [c[0] for c in cursor.description]
            raw_metadata = dict(zip(columns, row))
            
            # Create a user-friendly metadata display
            user_friendly_metadata = {
                "File Information": {
                    "File ID": id_in_subsystem,
                    "Version": raw_metadata.get('file_ver'),
                    "Satellite": f"{schema} (ID: {sat_id})",
                    "Subsystem": f"Subsystem {sub_id}",
                    "File Type": get_file_type_name(raw_metadata.get('type_id')),
                    "Status": "Removed" if raw_metadata.get('removed') else "Active"
                },
                "Timestamps": {
                    "Created": format_datetime(raw_metadata.get('init_ts')),
                    "Last Updated": format_datetime(raw_metadata.get('update_ts'))
                },
                "Storage Information": {
                    "Capacity": f"{raw_metadata.get('capacity')} bytes" if raw_metadata.get('capacity') is not None else "Unknown",
                    "Last Entry": raw_metadata.get('last_entry'),
                    "Total Sequences": raw_metadata.get('total_seq_nr'),
                    "Remaining Sequences": raw_metadata.get('remaining_seq_nr')
                }
            }
            
            return Response({
                "status": "success", 
                "data": user_friendly_metadata
            })
            
    except Exception as e:
        import traceback
        print(f"Metadata error: {str(e)}")
        print(traceback.format_exc())
        return Response({
            "status": "success",  # Still return success to avoid frontend errors
            "data": {
                "File Information": {
                    "File ID": id_in_subsystem,
                    "Version": file_ver,
                    "Error": "Could not retrieve complete metadata"
                },
                "Message": f"Database error: {str(e)}"
            }
        })

# Helper functions for metadata formatting
def format_datetime(dt):
    """Format datetime in a user-friendly way"""
    if not dt:
        return "Not available"
    
    if hasattr(dt, 'isoformat'):
        return dt.strftime("%B %d, %Y at %H:%M")
    
    return str(dt)

def get_file_type_name(type_id):
    """Convert type_id to a user-friendly name"""
    type_names = {
        1: "Text Document",
        2: "Binary Data",
        3: "Image",
        4: "Log File",
        5: "Configuration",
        
    }
    
    return type_names.get(type_id, f"Type {type_id}")



@api_view(['GET'])
def download_file(request, sat_id, sub_id, id_in_subsystem, file_ver):
    """
    GET /api/satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/version/<int:file_ver>/download/
    Downloads a specific file version
    """
    try:
        schema = get_satellite(sat_id)
        
        print(f"Download request: sat={sat_id}, schema={schema}, sub={sub_id}, file={id_in_subsystem}, ver={file_ver}")
        
        # First, get sat_file_id from sat_files table
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT id
                FROM "{schema}".sat_files
                WHERE id_in_subsystem = %s
                AND subsystem_id = %s
                ''',
                [id_in_subsystem, sub_id]
            )
            row = cursor.fetchone()
            
            if not row:
                print(f"File not found in sat_files: sat={sat_id}, sub={sub_id}, file={id_in_subsystem}")
                return Response({
                    "status": "error", 
                    "detail": f"File not found in satellite {sat_id}, subsystem {sub_id}"
                }, status=status.HTTP_404_NOT_FOUND)
            
            sat_file_id = row[0]
            print(f"Found sat_file_id: {sat_file_id}")
            
            # Get entries from download_entries_archive
            cursor.execute(
                f'''
                SELECT COUNT(*)
                FROM "{schema}".download_entries_archive
                WHERE sat_file_id = %s
                AND file_ver = %s
                ''',
                [sat_file_id, file_ver]
            )
            count = cursor.fetchone()[0]
            print(f"Found {count} entries in download_entries_archive")
            
            if count == 0:
                return Response({
                    "status": "success",
                    "detail": "No file data found for this version"
                })
            
            # Get the actual entry_data
            cursor.execute(
                f'''
                SELECT entry_data
                FROM "{schema}".download_entries_archive
                WHERE sat_file_id = %s
                AND file_ver = %s
                ORDER BY seq_nr
                ''',
                [sat_file_id, file_ver]
            )
            rows = cursor.fetchall()
            
            if not rows:
                print(f"No data found despite count={count}")
                return Response({
                    "status": "success",
                    "detail": "No file data found for this version"
                })
            
            try:
                # Combine all entry_data bytes into a single binary file
                file_bytes = b''
                for row in rows:
                    if row[0] is not None:
                        file_bytes += bytes(row[0])
                
                if not file_bytes:
                    return Response({
                        "status": "success",
                        "detail": "File data exists but is empty"
                    })
                
                filename = f"sat{sat_id}_sub{sub_id}_file{id_in_subsystem}_v{file_ver}.bin"
                
                response = HttpResponse(
                    file_bytes,
                    content_type='application/octet-stream'
                )
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['Content-Length'] = len(file_bytes)
                return response
                
            except Exception as e:
                print(f"Error processing file data: {str(e)}")
                return Response({
                    "status": "error", 
                    "detail": f"Error processing file data: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        import traceback
        print(f"Download error: {str(e)}")
        print(traceback.format_exc())
        return Response({
            "status": "error", 
            "detail": f"Server error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    




#####View du parsing#########


@api_view(['GET'])
def parsed_file(request, sat_id, sub_id, id_in_subsystem, file_ver, format):
    """
    GET /api/satellites/<int:sat_id>/subsystems/<int:sub_id>/files/<int:id_in_subsystem>/version/<int:file_ver>/parsed/<str:format>/
    Returns parsed file data in specified format
    """
    try:
        schema = get_satellite(sat_id)
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

        # Handle different formats
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
        return Response(
            {"status": "error", "detail": f"Could not parse file: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
def system_status(request):
    """
    GET /api/admin/system-status/
    Returns system administration statistics
    """
    try:
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
        return Response(
            {"status": "error", "detail": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )






####views pour les fonctionalités de la recherche des files

@api_view(['GET'])
def search_files(request):
    """
    GET /api/search/files?satellite_id=<id>&subsystem_id=<id>&file_name=<name>
    Search for files based on criteria
    """
    try:
        # Get query parameters
        satellite_id = request.GET.get('satellite_id')
        subsystem_id = request.GET.get('subsystem_id')
        file_name = request.GET.get('file_name')
        
        # Validate parameters
        if satellite_id and not satellite_id.isdigit():
            return Response({
                "status": "error", 
                "detail": "Invalid satellite ID"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if subsystem_id and not subsystem_id.isdigit():
            return Response({
                "status": "error", 
                "detail": "Invalid subsystem ID"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if file_name and not file_name.isdigit():
            return Response({
                "status": "error", 
                "detail": "Invalid file ID"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert to integers if present
        sat_id = int(satellite_id) if satellite_id else None
        sub_id = int(subsystem_id) if subsystem_id else None
        file_id = int(file_name) if file_name else None
        
        # Build search results
        results = []
        
        # Define which satellites to search
        satellites_to_search = []
        if sat_id:
            try:
                schema = get_satellite(sat_id)
                satellites_to_search.append((sat_id, schema))
            except ValueError:
                return Response({
                    "status": "error", 
                    "detail": f"Satellite ID {sat_id} does not exist"
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            satellites_to_search = [(1, "UM5-EOSAT"), (2, "RIBAT-SAT")]
        
        # Search each satellite
        for sat_id, schema in satellites_to_search:
            with connection.cursor() as cursor:
                # Build the SQL query based on parameters
                query = f'''
                SELECT 
                    sf.id_in_subsystem as file_id, 
                    sf.subsystem_id, 
                    df.update_ts,
                    MAX(df.file_ver) as latest_version
                FROM 
                    "{schema}".sat_files sf
                JOIN 
                    "{schema}".db_files df ON sf.id = df.sat_file_id
                WHERE 
                    1=1
                '''
                
                params = []
                
                if sub_id:
                    query += " AND sf.subsystem_id = %s"
                    params.append(sub_id)
                    
                if file_id:
                    query += " AND sf.id_in_subsystem = %s"
                    params.append(file_id)
                
                # Group by for latest version
                query += '''
                GROUP BY 
                    sf.id_in_subsystem, 
                    sf.subsystem_id, 
                    df.update_ts
                ORDER BY 
                    df.update_ts DESC
                LIMIT 50
                '''
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Format the results
                for row in cursor.fetchall():
                    file_id, subsystem_id, updated_ts, latest_version = row
                    
                    # Get satellite name
                    sat_name = "UM5-EOSAT" if sat_id == 1 else "RIBAT-SAT"
                    
                    # Format the date
                    formatted_date = updated_ts.strftime("%Y-%m-%d %H:%M:%S")
                    
                    results.append({
                        "satellite_id": sat_id,
                        "satellite_name": sat_name,
                        "subsystem_id": subsystem_id,
                        "file_id": file_id,
                        "updated_date": formatted_date,
                        "latest_version": latest_version
                    })
        
        return Response({
            "status": "success",
            "data": results
        })
        
    except Exception as e:
        import traceback
        print(f"Search error: {str(e)}")
        print(traceback.format_exc())
        return Response({
            "status": "error", 
            "detail": f"Server error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def recent_files(request):
    """
    GET /api/files/recent?sort=desc
    Get recently updated files
    """
    try:
        # Get sort order parameter
        sort_order = request.GET.get('sort', 'desc').lower()
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        
        order_direction = "DESC" if sort_order == 'desc' else "ASC"
        
        results = []
        
        # Search across both satellites
        satellites = [(1, "UM5-EOSAT"), (2, "RIBAT-SAT")]
        
        for sat_id, schema in satellites:
            with connection.cursor() as cursor:
                query = f'''
                SELECT 
                    sf.id_in_subsystem as file_id, 
                    sf.subsystem_id, 
                    MAX(df.update_ts) as latest_update,
                    MAX(df.file_ver) as latest_version
                FROM 
                    "{schema}".sat_files sf
                JOIN 
                    "{schema}".db_files df ON sf.id = df.sat_file_id
                GROUP BY 
                    sf.id_in_subsystem, 
                    sf.subsystem_id
                ORDER BY 
                    latest_update {order_direction}
                LIMIT 20
                '''
                
                cursor.execute(query)
                
                # Format the results
                for row in cursor.fetchall():
                    file_id, subsystem_id, updated_ts, latest_version = row
                    
                    # Get satellite name
                    sat_name = "UM5-EOSAT" if sat_id == 1 else "RIBAT-SAT"
                    
                    # Format the date
                    formatted_date = updated_ts.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Calculate time ago for display
                    now = datetime.datetime.now(updated_ts.tzinfo)
                    diff = now - updated_ts
                    
                    if diff.days > 365:
                        time_ago = f"{diff.days // 365} year{'s' if diff.days // 365 != 1 else ''} ago"
                    elif diff.days > 30:
                        time_ago = f"{diff.days // 30} month{'s' if diff.days // 30 != 1 else ''} ago"
                    elif diff.days > 0:
                        time_ago = f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
                    elif diff.seconds // 3600 > 0:
                        time_ago = f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 != 1 else ''} ago"
                    elif diff.seconds // 60 > 0:
                        time_ago = f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 != 1 else ''} ago"
                    else:
                        time_ago = "Just now"
                    
                    results.append({
                        "satellite_id": sat_id,
                        "satellite_name": sat_name,
                        "subsystem_id": subsystem_id,
                        "file_id": file_id,
                        "updated_date": formatted_date,
                        "updated_time_ago": time_ago,
                        "latest_version": latest_version
                    })
        
        # Sort combined results by update date
        if sort_order == 'desc':
            results.sort(key=lambda x: x['updated_date'], reverse=True)
        else:
            results.sort(key=lambda x: x['updated_date'])
        
        # Limit to top 20
        results = results[:20]
        
        return Response({
            "status": "success",
            "data": results
        })
        
    except Exception as e:
        import traceback
        print(f"Recent files error: {str(e)}")
        print(traceback.format_exc())
        return Response({
            "status": "error", 
            "detail": f"Server error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


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


    











###################VIEWS d'authentification############

from django.contrib.auth import authenticate, logout, login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.permissions import IsAuthenticated
from two_factor.utils import default_device
from django.http import JsonResponse
import pyqrcode
from io import BytesIO
import base64
import logging
from django.db import transaction
from rest_framework.permissions import AllowAny
from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes

logger = logging.getLogger(__name__)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        remember = request.data.get('remember', False)
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Log the user in
            login(request, user)
            
            # Debug all devices
            devices = TOTPDevice.objects.filter(user=user, confirmed=True)
            logger.info(f"All confirmed TOTP devices for {username}: {list(devices)}")
            device = default_device(user)
            logger.info(f"Default 2FA device for {username}: {device}")
            if device:
                logger.info(f"2FA required for {username}, device: {device.name}, ID: {device.id}")
                return Response({
                    'status': '2fa_required',
                    'user_id': user.id,
                    'remember': remember
                }, status=status.HTTP_200_OK)
            
            logger.info(f"No 2FA device for {username}, proceeding with login")
            return Response({
                'user': {
                    'username': user.username,
                    'is_superuser': user.is_superuser
                }
            }, status=status.HTTP_200_OK)
        
        logger.error(f"Authentication failed for {username}")
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

#Ces trois views pour la gestion des 2FA


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

class Verify2FAView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        token = request.data.get('token')
        
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(id=user_id)
            device = default_device(user)
            if device and device.verify_token(token):
                login(request, user)
                return Response({
                    'user': {
                        'username': user.username,
                        'is_superuser': user.is_superuser
                    }
                }, status=status.HTTP_200_OK)
            
            return Response({'error': 'Invalid verification code'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Invalid user'}, status=status.HTTP_401_UNAUTHORIZED)

class Setup2FAView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if default_device(user):
            logger.info(f"2FA already enabled for user {user.username}")
            return Response({'error': '2FA already enabled'}, status=status.HTTP_400_BAD_REQUEST)
        
        # supprimer les devices non confirmées (pour ne pas remplir la bd avec des données inutiles)
        TOTPDevice.objects.filter(user=user, confirmed=False).delete()
        device = TOTPDevice.objects.create(user=user, name=user.username, confirmed=False)
        logger.info(f"Created TOTP device for {user.username}: ID={device.id}, name={device.name}")
        qr = pyqrcode.create(device.config_url)
        buffer = BytesIO()
        qr.png(buffer, scale=5)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            'qr_code': f"data:image/png;base64,{qr_base64}",
            'secret_key': device.key,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        token = request.data.get('token')
        
        with transaction.atomic():
            device = TOTPDevice.objects.filter(user=user, confirmed=False).first()
            if device:
                logger.info(f"Verifying TOTP token for {user.username}, device ID={device.id}")
                if device.verify_token(token):
                    device.confirmed = True
                    device.save()
                    logger.info(f"TOTP device confirmed and saved for {user.username}: ID={device.id}, name={device.name}, confirmed={device.confirmed}")
                    # Verify device in DB
                    saved_device = TOTPDevice.objects.filter(user=user, id=device.id, confirmed=True).first()
                    if saved_device:
                        logger.info(f"Confirmed device found in DB for {user.username}: ID={saved_device.id}")
                    else:
                        logger.error(f"Failed to find confirmed device for {user.username}")
                    return Response({'status': '2FA enabled successfully'}, status=status.HTTP_200_OK)
                else:
                    logger.warning(f"Invalid TOTP token for {user.username}, device ID={device.id}")
                    return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                logger.error(f"No unconfirmed TOTP device found for {user.username}")
                return Response({'error': 'No 2FA device found'}, status=status.HTTP_400_BAD_REQUEST)




##Ces deux views pour la gestion des sessions
@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """Simplified logout view"""
    logout(request)
    request.session.flush()
    return Response({
        "message": "Logged out successfully.",
        "redirect": "/login/"
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([AllowAny])  # Allow all to check session status
def check_session_status(request):
    """Check if the user is authenticated and session is valid"""
    if not request.user.is_authenticated:
        logger.info("Session check: User not authenticated")
        return JsonResponse({
            'authenticated': False,
            'expired': True,
            'redirect': '/login/'
        }, status=401)
    
    # Update last activity timestamp
    request.session['last_activity'] = timezone.now().isoformat()
    logger.info(f"Session check: User {request.user.username} authenticated")
    
    return JsonResponse({
        'authenticated': True,
        'session_type': 'basic'
    })