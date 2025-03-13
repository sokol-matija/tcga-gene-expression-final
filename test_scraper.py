"""
Test script for validating the web scraper functionality.
"""

from scraper import get_all_cohort_urls, get_illuminahiseq_pancan_url, download_file, download_all_datasets, download_clinical_data

def test_cohort_urls():
    """Test getting all TCGA cohort URLs."""
    cohorts = get_all_cohort_urls()
    print(f"Found {len(cohorts)} cohorts")
    
    if cohorts:
        print("Sample cohorts:")
        for i, cohort in enumerate(cohorts[:3]):
            print(f"{i+1}. {cohort['name']} ({cohort['code']}): {cohort['url']}")

def test_dataset_url():
    """Test getting a dataset URL for a specific cohort."""
    # LAML cohort URL
    laml_url = "https://xenabrowser.net/datapages/?cohort=TCGA%20Acute%20Myeloid%20Leukemia%20(LAML)&removeHub=https%3A%2F%2Fxena.treehouse.gi.ucsc.edu%3A443"
    
    dataset_url = get_illuminahiseq_pancan_url(laml_url, "LAML")
    print(f"LAML dataset URL: {dataset_url}")

def test_download_single():
    """Test downloading a single dataset."""
    # LAML cohort
    laml = {
        'name': 'TCGA Acute Myeloid Leukemia (LAML)',
        'code': 'LAML',
        'url': "https://xenabrowser.net/datapages/?cohort=TCGA%20Acute%20Myeloid%20Leukemia%20(LAML)&removeHub=https%3A%2F%2Fxena.treehouse.gi.ucsc.edu%3A443"
    }
    
    dataset_url = get_illuminahiseq_pancan_url(laml['url'], laml['code'])
    
    if dataset_url:
        print(f"Downloading LAML dataset from {dataset_url}...")
        file_path = download_file(dataset_url, "data", f"{laml['code']}_gene_expression_IlluminaHiSeq_pancan.tsv.gz")
        if file_path:
            print(f"Successfully downloaded to {file_path}")
    else:
        print("Failed to get dataset URL")

def test_download_clinical():
    """Test downloading clinical data."""
    clinical_path = download_clinical_data()
    if clinical_path:
        print(f"Successfully downloaded clinical data to {clinical_path}")
    else:
        print("Failed to download clinical data")

def test_download_all(limit=1):
    """Test downloading multiple datasets."""
    print(f"Testing download of up to {limit} datasets...")
    files = download_all_datasets(limit=limit)
    if files:
        print(f"Successfully downloaded {len(files)} files:")
        for file_info in files:
            print(f"- {file_info['code']}: {file_info['path']}")
    else:
        print("No files were downloaded")

if __name__ == "__main__":
    print("=== Testing cohort URLs ===")
    test_cohort_urls()
    
    print("\n=== Testing dataset URL ===")
    test_dataset_url()
    
    print("\n=== Testing single download ===")
    test_download_single()
    
    print("\n=== Testing clinical data download ===")
    test_download_clinical()
    
    print("\n=== Testing multiple downloads ===")
    test_download_all(limit=2) 