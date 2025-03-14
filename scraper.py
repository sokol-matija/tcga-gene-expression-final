"""
Script to extract TCGA cohort names and abbreviation codes from the Xena Browser,
and download gene expression data for each cohort.
"""

from playwright.sync_api import sync_playwright
import argparse
import time
import re
import os
import requests
import pandas as pd
import numpy as np
import gzip
import random
from bs4 import BeautifulSoup

def scrape_tcga_cohorts():
    """
    Extract TCGA cohort names and abbreviation codes from Xena Browser using Playwright.
    
    Returns:
        list: List of dictionaries with cohort information
    """
    # Setup Playwright browser
    print("Starting Playwright browser...")
    with sync_playwright() as p:
        # Launch the browser (headless by default)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to the Xena Browser page
        print("Navigating to Xena Browser...")
        page.goto("https://xenabrowser.net/datapages/?hub=https://tcga.xenahubs.net:443")
        
        # Wait for the page to load - first try waiting for the specific list element
        print("Waiting for page content to load...")
        try:
            # Wait for the specific cohort list container to appear
            # First try with the exact class name from the HTML you provided
            page.wait_for_selector('ul.Datapages-module__list___2yM9o', timeout=15000)
            print("Found cohort list with specific class.")
        except:
            # If we can't find that specific class, try a more general approach
            print("Specific list class not found, trying more general approach...")
            # Wait for any UL element with many LI elements
            page.wait_for_selector('ul li a:has-text("TCGA")', timeout=15000)
        
        # Take a screenshot for debugging
        page.screenshot(path="xena_browser.png")
        print("Saved screenshot to xena_browser.png")
        
        # Extract cohort names and codes
        cohort_data = []
        
        # Try with the specific class first
        specific_list = page.query_selector('ul.Datapages-module__list___2yM9o')
        if specific_list:
            # Use the specific list we found
            links = specific_list.query_selector_all('li a')
            for link in links:
                text = link.inner_text()
                if 'TCGA' in text:
                    name = text.strip()
                    # Extract the code in parentheses using regex
                    code_match = re.search(r'\(([A-Z]+)\)', name)
                    code = code_match.group(1) if code_match else None
                    if code:
                        url = link.get_attribute('href')
                        cohort_data.append({
                            'name': name,
                            'code': code,
                            'url': f"https://xenabrowser.net{url}" if url.startswith('/') else url
                        })
        else:
            # Use a more general approach - find all links containing 'TCGA'
            all_links = page.query_selector_all('a')
            for link in all_links:
                text = link.inner_text()
                if 'TCGA' in text and '(' in text and ')' in text:  # Look for "TCGA Name (CODE)" pattern
                    name = text.strip()
                    # Extract the code in parentheses using regex
                    code_match = re.search(r'\(([A-Z]+)\)', name)
                    code = code_match.group(1) if code_match else None
                    if code:
                        url = link.get_attribute('href')
                        cohort_data.append({
                            'name': name,
                            'code': code,
                            'url': f"https://xenabrowser.net{url}" if url.startswith('/') else url
                        })
        
        # Close browser
        browser.close()
        
        return cohort_data

def download_gene_expression_data(cohort_data, output_dir="data"):
    """
    Download gene expression data for each TCGA cohort.
    
    Args:
        cohort_data (list): List of dictionaries with cohort information
        output_dir (str): Directory to save downloaded files
    
    Returns:
        list: List of successfully downloaded files
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    downloaded_files = []
    
    # Loop through each cohort
    for cohort in cohort_data:
        code = cohort['code']
        name = cohort['name']
        
        # Construct the download URL
        url = f"https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/TCGA.{code}.sampleMap%2FHiSeqV2_PANCAN.gz"
        
        # Define the output file path
        output_file = os.path.join(output_dir, f"{code}_gene_expression.gz")
        
        print(f"Downloading dataset IlluminaHiSeq pancan normalized for {code}...")
        
        try:
            # Send a request to download the file
            response = requests.get(url, stream=True)
            
            # Check if the request was successful
            if response.status_code == 200:
                # Save the file
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✓ Successfully downloaded: {output_file}")
                downloaded_files.append(output_file)
            else:
                print(f"× Download failed for {code}: Status code {response.status_code}")
        
        except Exception as e:
            print(f"× Error downloading data for {code}: {e}")
    
    return downloaded_files

def get_all_cohort_urls():
    """
    Get all TCGA cohort URLs from Xena Browser.
    
    Returns:
        list: List of dictionaries with cohort information
    """
    return scrape_tcga_cohorts()

def get_illuminahiseq_pancan_url(cohort_url, cohort_code):
    """
    Get the URL for the IlluminaHiSeq pancan normalized dataset for a specific cohort.
    
    Args:
        cohort_url (str): URL of the cohort page
        cohort_code (str): TCGA cohort code
        
    Returns:
        str: URL of the dataset, or None if not found
    """
    # Construct the direct S3 URL
    return f"https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/TCGA.{cohort_code}.sampleMap%2FHiSeqV2_PANCAN.gz"

def download_file(url, output_dir, output_filename):
    """
    Download a file from a URL.
    
    Args:
        url (str): URL of the file to download
        output_dir (str): Directory to save the file
        output_filename (str): Name to save the file as
        
    Returns:
        str: Path to the downloaded file, or None if download failed
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, output_filename)
    
    try:
        # Send a request to download the file
        response = requests.get(url, stream=True)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Save the file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✓ Successfully downloaded: {output_path}")
            return output_path
        else:
            print(f"× Download failed: Status code {response.status_code}")
            return None
    
    except Exception as e:
        print(f"× Error downloading file: {e}")
        return None

def download_all_datasets(limit=None):
    """
    Download all available gene expression datasets, up to the specified limit.
    
    Args:
        limit (int, optional): Maximum number of datasets to download
        
    Returns:
        list: List of dictionaries with information about downloaded files
    """
    # Get cohort information
    cohorts = scrape_tcga_cohorts()
    
    # Limit the number of cohorts if specified
    if limit and limit > 0:
        cohorts = cohorts[:limit]
    
    # Create output directory
    output_dir = "data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Download files
    downloaded_files_info = []
    
    for cohort in cohorts:
        code = cohort['code']
        name = cohort['name']
        
        # Construct download URL
        url = f"https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/TCGA.{code}.sampleMap%2FHiSeqV2_PANCAN.gz"
        
        # Define output file path
        output_file = os.path.join(output_dir, f"{code}_gene_expression.gz")
        
        print(f"Downloading dataset for {code}...")
        
        try:
            # Send request to download file
            response = requests.get(url, stream=True)
            
            # Check if request was successful
            if response.status_code == 200:
                # Save file
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✓ Successfully downloaded: {output_file}")
                
                # Add file info to result list
                downloaded_files_info.append({
                    'path': output_file,
                    'cohort': name,
                    'code': code,
                    'name': 'Gene Expression'
                })
            else:
                print(f"× Download failed for {code}: Status code {response.status_code}")
        
        except Exception as e:
            print(f"× Error downloading data for {code}: {e}")
    
    return downloaded_files_info

def download_clinical_data():
    """
    Download clinical data for TCGA patients.
    
    Returns:
        str: Path to the downloaded clinical data file, or None if download failed
    """
    # Clinical data URL
    url = "https://xena.treehouse.gi.ucsc.edu/download/TCGA_clinical_survival_data.tsv"
    
    # Output file path
    output_dir = "data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, "TCGA_clinical_survival_data.tsv")
    
    print("Downloading clinical data...")
    
    try:
        # Send request to download file
        response = requests.get(url, stream=True)
        
        # Check if request was successful
        if response.status_code == 200:
            # Save file
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✓ Successfully downloaded clinical data: {output_file}")
            return output_file
        else:
            print(f"× Download failed for clinical data: Status code {response.status_code}")
            return None
    
    except Exception as e:
        print(f"× Error downloading clinical data: {e}")
        return None

def get_sample_dataset():
    """
    Generate a sample dataset for testing.
    
    Returns:
        str: Path to the generated sample file
    """
    output_dir = "data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, "sample_gene_expression.tsv")
    
    # Define sample genes
    genes = [
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
    
    # Create sample data
    num_patients = 20
    patient_ids = [f"TCGA-SAMPLE-{i:04d}" for i in range(1, num_patients + 1)]
    
    # Create a DataFrame
    data = {'Gene': genes}
    
    # Add random expression values for each patient
    for patient_id in patient_ids:
        # Generate random expression values (somewhat realistic range)
        data[patient_id] = np.random.uniform(4.0, 12.0, size=len(genes))
    
    # Create DataFrame and save to TSV
    df = pd.DataFrame(data)
    df.to_csv(output_file, sep='\t', index=False)
    
    print(f"✓ Generated sample dataset: {output_file}")
    return output_file

def main():
    """Main function to run the scraper."""
    parser = argparse.ArgumentParser(description='Extract TCGA cohort names and codes from Xena Browser and download gene expression data')
    parser.add_argument('--save-html', help='Save the rendered HTML to this file')
    parser.add_argument('--download', action='store_true', help='Download gene expression data for each cohort')
    parser.add_argument('--output-dir', default='data', help='Directory to save downloaded files')
    args = parser.parse_args()
    
    try:
        # Run the scraper
        cohort_data = scrape_tcga_cohorts()
        
        # Print results
        print("\nTCGA Cohorts with Abbreviation Codes:")
        print("-------------------------------------")
        for cohort in cohort_data:
            print(f"{cohort['name']} → Code: {cohort['code']}")
        
        print(f"\nFound {len(cohort_data)} TCGA cohorts")
        
        # Download data if requested
        if args.download:
            print("\nDownloading gene expression data...")
            downloaded_files = download_gene_expression_data(cohort_data, args.output_dir)
            print(f"\nDownloaded {len(downloaded_files)} out of {len(cohort_data)} datasets")
        else:
            print("\nTo download gene expression data, run with the --download flag")
            print("Example: python scraper.py --download --output-dir ./data")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use this script, you need to install Playwright first:")
        print("1. pip install playwright")
        print("2. playwright install chromium")

if __name__ == "__main__":
    main()  