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

# List of target genes to analyze
TARGET_GENES = [
    'TP53',    # Tumor protein p53
    'BRCA1',   # Breast cancer type 1 susceptibility protein
    'BRCA2',   # Breast cancer type 2 susceptibility protein
    'EGFR',    # Epidermal growth factor receptor
    'KRAS',    # KRAS proto-oncogene
    'PTEN',    # Phosphatase and tensin homolog
    'PIK3CA',  # Phosphatidylinositol-4,5-bisphosphate 3-kinase catalytic subunit alpha
    'AKT1',    # AKT serine/threonine kinase 1
    'MYC',     # MYC proto-oncogene
    'BRAF'     # B-Raf proto-oncogene
] 