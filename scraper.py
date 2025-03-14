"""
Script to extract TCGA cohort names and abbreviation codes from the Xena Browser using Playwright,
and download gene expression data for each cohort.
"""

from playwright.sync_api import sync_playwright
import argparse
import time
import re
import os
import requests

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
                        cohort_data.append({
                            'name': name,
                            'code': code
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
                        cohort_data.append({
                            'name': name,
                            'code': code
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