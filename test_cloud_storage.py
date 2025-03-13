"""
Test script to verify cloud storage connections.
This script tests both AWS S3 and MongoDB connections to ensure data is being stored correctly.
"""

import os
from storage import ensure_bucket_exists, upload_data, download_file, list_objects
from database import get_mongo_client, get_collection, get_patient_count

def test_s3_connection():
    """
    Test the connection to AWS S3 and basic operations.
    """
    print("\n=== Testing S3 Connection ===")
    
    # Test bucket existence
    print("\nTesting bucket existence...")
    bucket_exists = ensure_bucket_exists()
    print(f"Bucket exists or was created: {'SUCCESS' if bucket_exists else 'FAILED'}")
    
    if bucket_exists:
        # Test upload
        print("\nTesting file upload...")
        test_data = "This is a test file for S3 storage"
        object_name = "test_file.txt"
        upload_success = upload_data(test_data, object_name)
        print(f"Test upload: {'SUCCESS' if upload_success else 'FAILED'}")
        
        # List objects
        print("\nListing objects in bucket...")
        objects = list_objects()
        print(f"Objects in bucket: {objects}")
        
        # Test download
        if object_name in objects:
            print("\nTesting file download...")
            downloaded = download_file(object_name)
            if downloaded:
                print("Test download: SUCCESS")
                if isinstance(downloaded, bytes):
                    print(f"Content: {downloaded.decode('utf-8')}")
                else:
                    print(f"Content type: {type(downloaded)}")
            else:
                print("Test download: FAILED")

def test_mongodb_connection():
    """
    Test the connection to MongoDB Atlas and basic operations.
    """
    print("\n=== Testing MongoDB Connection ===")
    
    try:
        # Test connection
        client = get_mongo_client()
        print("MongoDB connection: SUCCESS")
        
        # List available databases
        print("\nAvailable databases:")
        databases = client.list_database_names()
        for db in databases:
            print(f"- {db}")
        
        # Get collection and count documents
        collection = get_collection()
        print(f"\nCollection name: {collection.name}")
        
        count = get_patient_count()
        print(f"Documents in collection: {count}")
        
        # Get sample document if available
        if count > 0:
            print("\nSample document:")
            sample = collection.find_one()
            print(f"Document ID: {sample.get('_id')}")
            print(f"Document keys: {list(sample.keys())}")
            
            # Show some gene expression data if available
            if 'gene_expressions' in sample and isinstance(sample['gene_expressions'], dict):
                print("\nSample gene expressions:")
                genes = list(sample['gene_expressions'].keys())[:5]  # Show first 5 genes
                for gene in genes:
                    print(f"- {gene}: {sample['gene_expressions'][gene]}")
        
    except Exception as e:
        print(f"MongoDB test failed: {e}")

if __name__ == "__main__":
    print("=== Cloud Storage Test ===")
    print("This script tests connections to AWS S3 and MongoDB Atlas")
    
    # Run tests
    test_s3_connection()
    test_mongodb_connection()
    
    print("\n=== Test Complete ===") 