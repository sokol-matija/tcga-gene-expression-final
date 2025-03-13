"""
Functions for interacting with MiniO storage.
"""

from minio import Minio
from minio.error import S3Error
import io
import os
from config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME, MINIO_SECURE

def get_minio_client():
    """
    Create and return a MiniO client.
    
    Returns:
        Minio: Configured MiniO client
    """
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )

def ensure_bucket_exists():
    """
    Ensure that the configured bucket exists in MiniO.
    
    Returns:
        bool: True if bucket exists or was created successfully
    """
    client = get_minio_client()
    
    try:
        # Check if bucket exists, create if it doesn't
        if not client.bucket_exists(MINIO_BUCKET_NAME):
            client.make_bucket(MINIO_BUCKET_NAME)
            print(f"Bucket '{MINIO_BUCKET_NAME}' created successfully")
        else:
            print(f"Bucket '{MINIO_BUCKET_NAME}' already exists")
        return True
    except S3Error as e:
        print(f"Error with bucket operation: {e}")
        return False

def upload_file(file_path, object_name=None):
    """
    Upload a file to MiniO storage.
    
    Args:
        file_path (str): Path to the file to upload
        object_name (str, optional): Name to give the object in MiniO. 
                                     If None, use the filename.
    
    Returns:
        bool: True if successful, False otherwise
    """
    if object_name is None:
        object_name = os.path.basename(file_path)
        
    client = get_minio_client()
    
    try:
        # Upload the file
        client.fput_object(
            MINIO_BUCKET_NAME, 
            object_name,
            file_path,
        )
        print(f"'{file_path}' successfully uploaded as '{object_name}'")
        return True
    except S3Error as e:
        print(f"Error uploading file: {e}")
        return False

def upload_data(data, object_name):
    """
    Upload data directly to MiniO storage.
    
    Args:
        data (bytes or str): Data to upload
        object_name (str): Name to give the object in MiniO
    
    Returns:
        bool: True if successful, False otherwise
    """
    client = get_minio_client()
    
    try:
        # Convert string to bytes if needed
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Upload the data
        client.put_object(
            MINIO_BUCKET_NAME,
            object_name,
            io.BytesIO(data),
            length=len(data)
        )
        print(f"Data successfully uploaded as '{object_name}'")
        return True
    except S3Error as e:
        print(f"Error uploading data: {e}")
        return False

def download_file(object_name, file_path=None):
    """
    Download a file from MiniO storage.
    
    Args:
        object_name (str): Name of the object in MiniO
        file_path (str, optional): Path to save the file to. 
                                   If None, return the data.
    
    Returns:
        bytes or bool: File data if file_path is None, True if save successful, False otherwise
    """
    client = get_minio_client()
    
    try:
        if file_path is not None:
            # Download to file
            client.fget_object(
                MINIO_BUCKET_NAME,
                object_name,
                file_path
            )
            print(f"'{object_name}' successfully downloaded to '{file_path}'")
            return True
        else:
            # Return data
            response = client.get_object(MINIO_BUCKET_NAME, object_name)
            data = response.read()
            response.close()
            return data
    except S3Error as e:
        print(f"Error downloading file: {e}")
        return False

def list_objects():
    """
    List all objects in the MiniO bucket.
    
    Returns:
        list: List of object names
    """
    client = get_minio_client()
    
    try:
        objects = client.list_objects(MINIO_BUCKET_NAME)
        return [obj.object_name for obj in objects]
    except S3Error as e:
        print(f"Error listing objects: {e}")
        return [] 