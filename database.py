"""
Functions for interacting with MongoDB.
"""

from pymongo import MongoClient, ASCENDING
from config import MONGO_URI, MONGO_DB_NAME, MONGO_COLLECTION_NAME

def get_mongo_client():
    """
    Create and return a MongoDB client.
    
    Returns:
        MongoClient: Configured MongoDB client
    """
    return MongoClient(MONGO_URI)

def create_indexes(collection):
    """
    Create indexes on the MongoDB collection for better query performance.
    
    Args:
        collection: MongoDB collection to create indexes on
    """
    # Check if indexes already exist
    existing_indexes = collection.index_information()
    
    # Create index on cancer_cohort for faster cohort-based queries
    if 'cancer_cohort_1' not in existing_indexes:
        collection.create_index([('cancer_cohort', ASCENDING)], 
                                 background=True, 
                                 name='cancer_cohort_idx')
        print("Created index on cancer_cohort field")
    
    # Create index on patient_id for faster patient lookup
    if 'patient_id_1' not in existing_indexes:
        collection.create_index([('patient_id', ASCENDING)], 
                                 background=True, 
                                 name='patient_id_idx')
        print("Created index on patient_id field")

def get_collection():
    """
    Get the MongoDB collection for patient expressions.
    
    Returns:
        Collection: MongoDB collection for patient expressions
    """
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]
    
    # Create indexes if they don't exist
    create_indexes(collection)
    
    return collection

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

def get_cohort_counts():
    """
    Get counts of patients by cohort using MongoDB's aggregation framework.
    This is much faster than retrieving all patients and counting them.
    
    Returns:
        dict: Dictionary with cohort names as keys and patient counts as values
    """
    collection = get_collection()
    
    try:
        pipeline = [
            {"$group": {"_id": "$cancer_cohort", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        result = collection.aggregate(pipeline)
        return {doc["_id"]: doc["count"] for doc in result}
    except Exception as e:
        print(f"Error getting cohort counts: {e}")
        return {}

def get_gene_expression_stats(cohort, gene=None):
    """
    Get statistics for gene expressions by cohort using MongoDB's aggregation framework.
    
    Args:
        cohort (str): Cancer cohort name
        gene (str, optional): Specific gene to get statistics for. If None, get for all genes.
        
    Returns:
        list: List of dictionaries with gene statistics
    """
    collection = get_collection()
    
    try:
        # Build the match stage
        match_stage = {"cancer_cohort": cohort}
        
        # Build the pipeline
        pipeline = [
            {"$match": match_stage},
            {"$project": {
                "cancer_cohort": 1,
                "gene_expressions": 1
            }}
        ]
        
        # Get results and process them
        results = list(collection.aggregate(pipeline))
        
        # Process the results into a format suitable for visualization
        stats = []
        for doc in results:
            expressions = doc.get("gene_expressions", {})
            for gene_name, value in expressions.items():
                if gene is not None and gene_name != gene:
                    continue
                    
                if isinstance(value, (int, float)):
                    stats.append({
                        "gene": gene_name,
                        "expression": value,
                        "cancer_cohort": doc["cancer_cohort"]
                    })
        
        return stats
    except Exception as e:
        print(f"Error getting gene expression stats: {e}")
        return []

def get_patient_sample(cohort, limit=100):
    """
    Get a sample of patients from a specific cohort, limiting the fields returned.
    
    Args:
        cohort (str): Cancer cohort name
        limit (int): Maximum number of patients to retrieve
        
    Returns:
        list: List of patient documents
    """
    collection = get_collection()
    
    try:
        # Get a sample of patients from the cohort
        cursor = collection.find(
            {"cancer_cohort": cohort},
            # Only include the fields we need
            {"patient_id": 1, "cancer_cohort": 1, "gene_expressions": 1, "pathway_scores": 1, "_id": 0}
        ).limit(limit)
        
        return list(cursor)
    except Exception as e:
        print(f"Error getting patient sample: {e}")
        return [] 