"""
Functions for scraping gene expression data from Xena Browser.
"""

import os
import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import numpy as np
from config import TARGET_GENES

def get_all_cohort_urls():
    """
    Get URLs for all TCGA cohorts from the Xena Browser.
    
    Returns:
        list: List of dictionaries with cohort information
    """
    # The main hub page for TCGA data
    base_url = "https://xenabrowser.net/datapages/?hub=https://tcga.xenahubs.net:443"
    
    try:
        print(f"Fetching TCGA cohorts from {base_url}...")
        response = requests.get(base_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        cohorts = []
        
        # Look for the list of cohorts which is in a ul element with a specific class
        cohort_list = soup.find('ul', class_='Datapages-module__list___2yM9o')
        
        if not cohort_list:
            print("Could not find cohort list on the page. The page structure might have changed.")
            print("Trying alternative selectors...")
            # Try a more general approach
            cohort_list = soup.find_all('ul')
            for ul in cohort_list:
                if len(ul.find_all('a')) > 20:  # A list with many links is likely the cohort list
                    cohort_list = ul
                    break
        
        if cohort_list:
            print(f"Found cohort list with {len(cohort_list.find_all('li'))} items")
            
            # Extract cohort links from list items
            for li in cohort_list.find_all('li'):
                link = li.find('a')
                if link and 'TCGA' in link.text:
                    href = link.get('href')
                    text = link.text.strip()
                    
                    # Extract cohort code from the text (e.g., "TCGA Acute Myeloid Leukemia (LAML)")
                    match = re.search(r'\(([A-Z]+)\)', text)
                    code = match.group(1) if match else None
                    
                    if code:
                        # Construct full URL
                        full_url = f"https://xenabrowser.net{href}" if href.startswith('/') else f"https://xenabrowser.net/{href}"
                        cohorts.append({
                            'name': text,
                            'code': code,
                            'url': full_url
                        })
                        print(f"Added cohort: {text} ({code})")
        
        # If we could not find any cohorts with the standard approach, add LAML as a fallback
        if not cohorts:
            print("No cohorts found with standard approach. Using direct URLs as fallback...")
            laml_url = "https://xenabrowser.net/datapages/?cohort=TCGA%20Acute%20Myeloid%20Leukemia%20(LAML)&removeHub=https%3A%2F%2Fxena.treehouse.gi.ucsc.edu%3A443"
            cohorts.append({
                'name': 'TCGA Acute Myeloid Leukemia (LAML)',
                'code': 'LAML',
                'url': laml_url
            })
            print("Added fallback cohort: TCGA Acute Myeloid Leukemia (LAML)")
            
            # Add other common TCGA cohorts that might be useful
            common_cohorts = [
                ('BRCA', 'Breast Cancer'),
                ('LUAD', 'Lung Adenocarcinoma'),
                ('LUSC', 'Lung Squamous Cell Carcinoma'),
                ('COAD', 'Colon Cancer'),
                ('GBM', 'Glioblastoma')
            ]
            
            for code, name in common_cohorts:
                url = f"https://xenabrowser.net/datapages/?cohort=TCGA%20{name.replace(' ', '%20')}%20({code})&removeHub=https%3A%2F%2Fxena.treehouse.gi.ucsc.edu%3A443"
                cohorts.append({
                    'name': f'TCGA {name} ({code})',
                    'code': code,
                    'url': url
                })
                print(f"Added fallback cohort: TCGA {name} ({code})")
        
        print(f"Found {len(cohorts)} TCGA cohorts")
        return cohorts
    except Exception as e:
        print(f"Error fetching cohort URLs: {e}")
        # Return a minimal list with just LAML as an absolute fallback
        return [{
            'name': 'TCGA Acute Myeloid Leukemia (LAML)',
            'code': 'LAML',
            'url': "https://xenabrowser.net/datapages/?cohort=TCGA%20Acute%20Myeloid%20Leukemia%20(LAML)&removeHub=https%3A%2F%2Fxena.treehouse.gi.ucsc.edu%3A443"
        }]

def get_illuminahiseq_pancan_url(cohort_url, cohort_code):
    """
    Find the IlluminaHiSeq pancan normalized dataset URL for a specific cohort.
    
    Args:
        cohort_url (str): URL of the cohort page
        cohort_code (str): Cohort code (e.g., LAML)
        
    Returns:
        str: Download URL for the dataset, or None if not found
    """
    try:
        print(f"Fetching dataset page for {cohort_code} from {cohort_url}")
        response = requests.get(cohort_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the section for gene expression RNAseq
        gene_expr_heading = None
        for heading in soup.find_all('h3'):
            if 'gene expression RNAseq' in heading.text.lower():
                gene_expr_heading = heading
                print(f"Found gene expression RNAseq section")
                break
                
        if gene_expr_heading:
            # Find the parent div containing the dataset list
            parent_div = gene_expr_heading.find_parent('div')
            
            if parent_div:
                # Look for the dataset link with "IlluminaHiSeq pancan normalized"
                dataset_links = []
                for link in parent_div.find_all('a'):
                    link_text = link.text.strip().lower()
                    if 'illuminahiseq pancan normalized' in link_text:
                        dataset_url = link.get('href')
                        print(f"Found IlluminaHiSeq pancan normalized dataset link: {dataset_url}")
                        
                        # Construct the complete dataset URL
                        full_url = f"https://xenabrowser.net{dataset_url}" if dataset_url.startswith('/') else f"https://xenabrowser.net/{dataset_url}"
                        
                        # Get the download URL from the dataset page
                        return get_download_url(full_url, cohort_code)
                    
                # If we couldn't find the exact "pancan normalized" link, try to find any IlluminaHiSeq link
                for link in parent_div.find_all('a'):
                    link_text = link.text.strip().lower()
                    if 'illuminahiseq' in link_text:
                        print(f"Could not find pancan normalized dataset, using alternative: {link_text}")
                        dataset_url = link.get('href')
                        full_url = f"https://xenabrowser.net{dataset_url}" if dataset_url.startswith('/') else f"https://xenabrowser.net/{dataset_url}"
                        return get_download_url(full_url, cohort_code)
        
        # If we couldn't find the dataset through normal navigation, try direct URLs
        print(f"Could not find gene expression RNAseq section or dataset links for {cohort_code}")
        
        # Construct direct download URLs based on known patterns
        if cohort_code == 'LAML':
            direct_url = "https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/TCGA.LAML.sampleMap%2FHiSeqV2_PANCAN.gz"
            print(f"Using direct download URL for LAML: {direct_url}")
            return direct_url
        else:
            # Try to construct a URL following the pattern for other cohorts
            constructed_url = f"https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/TCGA.{cohort_code}.sampleMap%2FHiSeqV2_PANCAN.gz"
            print(f"Using constructed download URL for {cohort_code}: {constructed_url}")
            return constructed_url
            
    except Exception as e:
        print(f"Error finding dataset URL for {cohort_code}: {e}")
        
        # As a last resort, return a constructed URL based on the pattern
        fallback_url = f"https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/TCGA.{cohort_code}.sampleMap%2FHiSeqV2_PANCAN.gz"
        print(f"Using fallback URL due to error: {fallback_url}")
        return fallback_url

def get_download_url(dataset_page_url, cohort_code):
    """
    Extract the direct download URL from a dataset page.
    
    Args:
        dataset_page_url (str): URL of the dataset page
        cohort_code (str): Cohort code (e.g., LAML)
        
    Returns:
        str: Direct download URL for the dataset
    """
    try:
        print(f"Fetching dataset page to get download URL: {dataset_page_url}")
        response = requests.get(dataset_page_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the download section - look for the key/value pair
        download_key = None
        for span in soup.find_all('span', class_='Datapages-module__key___2kd01'):
            if 'download' in span.text.lower():
                download_key = span
                print("Found download section")
                break
        
        if download_key:
            # The download URL is in the next span (value span)
            value_span = download_key.find_next('span', class_='Datapages-module__value___3k05o')
            if value_span:
                # The direct download link should be the first link in this span
                download_link = value_span.find('a')
                if download_link:
                    download_url = download_link.get('href')
                    print(f"Found direct download URL: {download_url}")
                    return download_url
        
        # If we can't find the download URL through the spans, try another approach
        download_link = soup.find('a', href=re.compile(r'download.*\.gz'))
        if download_link:
            download_url = download_link.get('href')
            print(f"Found direct download URL through regex match: {download_url}")
            return download_url
            
        # If we still can't find it, construct a URL based on the dataset ID
        print("Could not find download URL on the page. Trying to construct URL from dataset ID...")
        
        # Try to find the dataset ID
        dataset_id = None
        for span in soup.find_all('span', class_='Datapages-module__key___2kd01'):
            if 'dataset id' in span.text.lower():
                id_span = span.find_next('span', class_='Datapages-module__value___3k05o')
                if id_span:
                    dataset_id = id_span.text.strip()
                    print(f"Found dataset ID: {dataset_id}")
                    break
        
        if dataset_id:
            # Construct URL from the dataset ID
            encoded_id = dataset_id.replace('/', '%2F')
            constructed_url = f"https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/{encoded_id}.gz"
            print(f"Constructed download URL from dataset ID: {constructed_url}")
            return constructed_url
            
        # Last resort fallback
        print("Could not construct URL from dataset ID. Using fallback pattern.")
        fallback_url = f"https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/TCGA.{cohort_code}.sampleMap%2FHiSeqV2_PANCAN.gz"
        print(f"Using fallback URL: {fallback_url}")
        return fallback_url
        
    except Exception as e:
        print(f"Error extracting download URL: {e}")
        # Final fallback for error cases
        fallback_url = f"https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/TCGA.{cohort_code}.sampleMap%2FHiSeqV2_PANCAN.gz"
        print(f"Error occurred, using fallback URL: {fallback_url}")
        return fallback_url

def download_file(url, save_dir="data", filename=None):
    """
    Download a file from a URL.
    
    Args:
        url (str): URL of the file to download
        save_dir (str): Directory to save the file
        filename (str, optional): Name to save the file as. If None, extract from URL.
        
    Returns:
        str: Path to the downloaded file, or None if download failed
    """
    try:
        # Create save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Extract filename from URL if not provided
        if filename is None:
            filename = url.split('/')[-1]
            
        # Generate full save path
        save_path = os.path.join(save_dir, filename)
        
        # Download the file
        print(f"Downloading {url} to {save_path}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"Download complete: {save_path}")
        return save_path
    except Exception as e:
        print(f"Error downloading file from {url}: {e}")
        return None

def download_all_datasets(save_dir="data", limit=None):
    """
    Download IlluminaHiSeq pancan normalized datasets for all TCGA cohorts.
    
    Args:
        save_dir (str): Directory to save downloaded files
        limit (int, optional): Maximum number of datasets to download
        
    Returns:
        list: Paths to successfully downloaded files
    """
    # Create save directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    # Get all cohort URLs
    cohorts = get_all_cohort_urls()
    
    # Apply limit if specified
    if limit is not None:
        cohorts = cohorts[:limit]
    
    downloaded_files = []
    
    for cohort in cohorts:
        # Add a delay to avoid overwhelming the server
        time.sleep(1)
        
        print(f"Processing cohort: {cohort['name']} ({cohort['code']})")
        
        # Get the dataset URL
        dataset_url = get_illuminahiseq_pancan_url(cohort['url'], cohort['code'])
        
        if dataset_url:
            # Generate a filename
            filename = f"{cohort['code']}_gene_expression_IlluminaHiSeq_pancan.tsv.gz"
            
            # Download the file
            file_path = download_file(dataset_url, save_dir, filename)
            
            if file_path:
                downloaded_files.append({
                    'path': file_path,
                    'cohort': cohort['name'],
                    'code': cohort['code']
                })
        
    return downloaded_files

def download_clinical_data(save_dir="data"):
    """
    Download clinical data (survival information) for TCGA samples.
    
    Args:
        save_dir (str): Directory to save the data
        
    Returns:
        str: Path to the downloaded file, or None if download failed
    """
    try:
        # Create the save directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # The URL for TCGA clinical/survival data
        # Using the URL directly from the HTML you shared for survival data
        clinical_url = "https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/survival/TCGA_survival_data_2.tsv"
        
        print(f"Downloading clinical data from {clinical_url}...")
        
        # Try alternative URLs if the first one fails
        clinical_urls = [
            clinical_url,
            "https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/TCGA.survival.tsv",
            "https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/survival%2FLAML_survival.txt"
        ]
        
        for url in clinical_urls:
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()  # Raise an exception for 4XX/5XX responses
                
                # Get the filename from the URL or use 'clinical_data.tsv'
                filename = os.path.basename(url) or "clinical_data.tsv"
                filename = filename.replace("%2F", "_").replace("%2C", "_")
                save_path = os.path.join(save_dir, filename)
                
                # Save the file
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"Clinical data downloaded successfully to {save_path}")
                return save_path
                
            except Exception as e:
                print(f"Failed to download from {url}: {e}")
                continue
        
        print("All attempts to download clinical data failed.")
        return None
        
    except Exception as e:
        print(f"Error downloading clinical data: {e}")
        return None

def get_sample_dataset(save_dir="data"):
    """
    For testing purposes only: create a small sample dataset with random data.
    
    Args:
        save_dir (str): Directory to save the file
        
    Returns:
        str: Path to the created file
    """
    # Create save directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)
    
    # Create a sample filename
    filename = "sample_TCGA_gene_expression.tsv"
    save_path = os.path.join(save_dir, filename)
    
    # Generate random data with target genes and sample patients
    np.random.seed(42)  # For reproducibility
    
    # Create gene list (including target genes)
    all_genes = TARGET_GENES + [f"Gene_{i}" for i in range(1, 21)]
    
    # Create patient IDs
    patient_ids = [f"TCGA-PATIENT-{i:04d}" for i in range(1, 31)]
    
    # Create DataFrame with random expression values
    df = pd.DataFrame(index=all_genes, columns=patient_ids)
    
    # Fill with random expression values (between 0 and 15)
    for gene in all_genes:
        for patient in patient_ids:
            df.loc[gene, patient] = np.random.uniform(0, 15)
    
    # Add gene names as a column
    df.index.name = "Gene"
    df = df.reset_index()
    
    # Save to TSV
    df.to_csv(save_path, sep='\t', index=False)
    print(f"Created sample dataset at {save_path}")
    
    return save_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download TCGA gene expression data from Xena Browser')
    parser.add_argument('--all', action='store_true', help='Download all available TCGA cohorts')
    parser.add_argument('--save-dir', default='data', help='Directory to save downloaded files (default: data)')
    
    args = parser.parse_args()
    
    if args.all:
        print("Starting download of all TCGA cohorts...")
        os.makedirs(args.save_dir, exist_ok=True)
        download_all_datasets(save_dir=args.save_dir)
        print("\nDownloading clinical data...")
        download_clinical_data(save_dir=args.save_dir)
    else:
        print("Please specify --all to download all TCGA cohorts")
        print("Example: python scraper.py --all") 