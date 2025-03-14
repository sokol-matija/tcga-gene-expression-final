"""
Configuration settings for the TCGA Gene Expression project.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MiniO configuration
# MINIO_ENDPOINT = "localhost:9000"
# MINIO_ACCESS_KEY = "minioadmin"
# MINIO_SECRET_KEY = "minioadmin"
# MINIO_BUCKET_NAME = "tcga-data"
# MINIO_SECURE = False  # Set to True if using HTTPS

# S3 configuration
MINIO_ENDPOINT = "s3.amazonaws.com"
MINIO_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
MINIO_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
MINIO_BUCKET_NAME = "tcga-gene-expression-data"  # Or your chosen bucket name
MINIO_SECURE = True

# MongoDB configuration
MONGO_URI = os.environ.get("MONGO_CONNECTION_STRING")
MONGO_DB_NAME = "tcga_gene_expression"
MONGO_COLLECTION_NAME = "patient_expressions"
# MONGO_URI = "mongodb://localhost:27017/"
# MONGO_DB_NAME = "tcga_gene_expression"
# MONGO_COLLECTION_NAME = "patient_expressions"

# Xena Browser settings
XENA_BASE_URL = "https://xenabrowser.net/datapages/"

# List of target genes to analyze - cGAS-STING pathway genes as specified in the requirements
TARGET_GENES = [
    'C6orf150',  # cGAS
    'TMEM173',   # STING
    'CCL5',      # Chemokine
    'CXCL10',    # Chemokine
    'CXCL9',     # Chemokine
    'CXCL11',    # Chemokine
    'NFKB1',     # Transcription factor
    'IKBKE',     # Kinase
    'IRF3',      # Transcription factor
    'TREX1',     # Exonuclease
    'ATM',       # Kinase
    'IL6',       # Interleukin
    'CXCL8'      # IL8 (Interleukin 8)
]

# Pathway scoring weights
PATHWAY_WEIGHTS = {
    "cGAS-STING": {
        "C6orf150": 0.3,  # cGAS
        "TMEM173": 0.3,   # STING
        "NFKB1": 0.1,
        "IKBKE": 0.1,
        "IRF3": 0.1,
        "TREX1": 0.1
    },
    "Chemokines": {
        "CCL5": 0.25,
        "CXCL10": 0.25,
        "CXCL9": 0.25,
        "CXCL11": 0.25
    },
    "Inflammation": {
        "IL6": 0.5,
        "CXCL8": 0.5  # IL8
    }
}

# Performance optimization settings
# --------------------------------

# Cache settings
CACHE_TTL = 600  # Cache time-to-live in seconds (10 minutes)

# Batch processing settings
BATCH_SIZE = 1000  # Number of items to process in a batch

# Sampling limits for visualizations
MAX_VISUALIZATION_SAMPLES = 100  # Maximum number of patients to use for visualizations
MAX_HEATMAP_PATIENTS = 50  # Maximum number of patients to show in heatmap

# Database query optimization
USE_AGGREGATION = True  # Whether to use MongoDB aggregation for queries
QUERY_TIMEOUT = 30000  # MongoDB query timeout in milliseconds (30 seconds) 