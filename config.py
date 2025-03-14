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