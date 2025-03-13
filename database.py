"""
Functions for interacting with MongoDB.
"""

from pymongo import MongoClient
from config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME

def get_mongo_client():
    """
    Create and return a MongoDB client.
    
    Returns:
        MongoClient: Configured MongoDB client
    """
    return MongoClient(MONGO_URI)

def get_collection():
    """
    Get the MongoDB collection for patient expressions.
    
    Returns:
        Collection: MongoDB collection for patient expressions
    """
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    return db[MONGO_COLLECTION_NAME]

def insert_patient_data(patient_data):
    """
    Insert patient gene expression data into MongoDB.
    
    Args:
        patient_data (dict or list): Patient data to insert
        
    Returns:
        bool: True if successful, False otherwise
    """
    collection = get_collection()
    
    try:
        # Insert one document or many
        if isinstance(patient_data, list):
            result = collection.insert_many(patient_data)
            print(f"Inserted {len(result.inserted_ids)} documents")
        else:
            result = collection.insert_one(patient_data)
            print(f"Inserted document with ID: {result.inserted_id}")
        return True
    except Exception as e:
        print(f"Error inserting data: {e}")
        return False

def get_patient_data(query=None, limit=None):
    """
    Retrieve patient data from MongoDB.
    
    Args:
        query (dict, optional): Query to filter results. If None, get all documents.
        limit (int, optional): Maximum number of documents to retrieve.
        
    Returns:
        list: List of matching documents
    """
    collection = get_collection()
    
    if query is None:
        query = {}
        
    try:
        cursor = collection.find(query)
        
        if limit is not None:
            cursor = cursor.limit(limit)
            
        return list(cursor)
    except Exception as e:
        print(f"Error retrieving data: {e}")
        return []

def get_unique_cohorts():
    """
    Get a list of unique cancer cohorts in the database.
    
    Returns:
        list: List of unique cancer cohort names
    """
    collection = get_collection()
    
    try:
        cohorts = collection.distinct("cancer_cohort")
        return cohorts
    except Exception as e:
        print(f"Error retrieving cohorts: {e}")
        return []

def get_patient_count():
    """
    Get the total number of patient records in the database.
    
    Returns:
        int: Number of patient records
    """
    collection = get_collection()
    
    try:
        return collection.count_documents({})
    except Exception as e:
        print(f"Error counting documents: {e}")
        return 0

def clear_collection():
    """
    Clear all documents from the collection.
    
    Returns:
        bool: True if successful, False otherwise
    """
    collection = get_collection()
    
    try:
        collection.delete_many({})
        print(f"Cleared all documents from {MONGO_COLLECTION_NAME}")
        return True
    except Exception as e:
        print(f"Error clearing collection: {e}")
        return False 