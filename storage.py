"""
Functions for interacting with AWS S3 storage (using MinIO client).
"""

from minio import Minio
from minio.error import S3Error
import io
import os
from config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET_NAME, MINIO_SECURE

def get_minio_client():
    """
    Create and return a MinIO client configured for AWS S3.
    
    Returns:
        Minio: Configured MinIO client for S3
    """
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
        region="us-east-1"  # Set to your AWS region
    )

def ensure_bucket_exists():
    """
    Ensure that the configured bucket exists in S3.
    
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
    Upload a file to S3 storage.
    
    Args:
        file_path (str): Path to the file to upload
        object_name (str, optional): Name to give the object in S3. 
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
    Upload data directly to S3 storage.
    
    Args:
        data (bytes or str): Data to upload
        object_name (str): Name to give the object in S3
    
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
    Download a file from S3 storage.
    
    Args:
        object_name (str): Name of the object in S3
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
    List all objects in the S3 bucket.
    
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

def test_s3_connection():
    """
    Test the S3 connection and bucket access.
    
    Returns:
        bool: True if connection and bucket access successful
    """
    client = get_minio_client()
    try:
        # Check if the bucket exists
        if client.bucket_exists(MINIO_BUCKET_NAME):
            print(f"Successfully connected to S3 bucket: {MINIO_BUCKET_NAME}")
            # List objects to test full access
            objects = list(client.list_objects(MINIO_BUCKET_NAME))
            print(f"Found {len(objects)} objects in bucket")
            return True
        else:
            print(f"Bucket {MINIO_BUCKET_NAME} does not exist")
            return False
    except S3Error as e:
        print(f"Error connecting to S3: {e}")
        return False