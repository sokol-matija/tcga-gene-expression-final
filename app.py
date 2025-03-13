"""
Main application for TCGA gene expression data collection and analysis.
"""

import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
import base64
from io import BytesIO

# Import our modules
from scraper import download_all_datasets, download_clinical_data, get_sample_dataset
from storage import ensure_bucket_exists, upload_file, download_file, list_objects
from processor import process_tsv_file, merge_with_clinical_data, calculate_pathway_score
from database import insert_patient_data, get_patient_data, get_unique_cohorts, get_patient_count
from visualizer import (
    plot_gene_expressions_by_cohort, 
    plot_heatmap, 
    plot_gene_correlation,
    plot_pathway_scores,
    get_figure_as_base64
)
from config import TARGET_GENES

# Set page configuration
st.set_page_config(
    page_title="TCGA Gene Expression Analyzer",
    page_icon="🧬",
    layout="wide"
)

# Create directories if they don't exist
os.makedirs("data", exist_ok=True)

def fetch_and_store_data(use_sample_data=False, max_datasets=1):
    """
    Fetch data from Xena Browser and store in MiniO.
    
    Args:
        use_sample_data (bool): Whether to use sample data instead of downloading
        max_datasets (int): Maximum number of datasets to download
        
    Returns:
        list: Paths to downloaded files
    """
    # Ensure MiniO bucket exists
    with st.spinner("Setting up MiniO storage..."):
        bucket_exists = ensure_bucket_exists()
        if not bucket_exists:
            st.error("Failed to set up MiniO storage. Please check your configuration.")
            return []
    
    # Get files
    files = []
    
    if use_sample_data:
        with st.spinner("Generating sample data..."):
            sample_path = get_sample_dataset()
            if sample_path:
                files.append({
                    'path': sample_path, 
                    'cohort': 'Sample', 
                    'code': 'SAMPLE',
                    'name': 'Gene Expression'
                })
    else:
        # Download files from Xena Browser
        with st.spinner("Downloading gene expression files from Xena Browser..."):
            files = download_all_datasets(limit=max_datasets)
            
            if not files:
                st.warning("No files were downloaded. Using sample data instead.")
                sample_path = get_sample_dataset()
                if sample_path:
                    files.append({
                        'path': sample_path, 
                        'cohort': 'Sample', 
                        'code': 'SAMPLE',
                        'name': 'Gene Expression'
                    })
    
    # Upload to MiniO
    if files:
        with st.spinner("Uploading files to MiniO..."):
            for file_info in files:
                file_path = file_info['path']
                object_name = os.path.basename(file_path)
                upload_file(file_path, object_name)
        
        st.success(f"Successfully downloaded and stored {len(files)} files.")
    else:
        st.error("Failed to obtain any data files.")
    
    return files

def process_and_store_data(files, include_clinical=False):
    """
    Process TSV files and store in MongoDB.
    
    Args:
        files (list): List of file information dictionaries
        include_clinical (bool): Whether to include clinical data
        
    Returns:
        list: List of patient records
    """
    all_patients = []
    
    # Process each file
    for file_info in files:
        file_path = file_info['path']
        with st.spinner(f"Processing {os.path.basename(file_path)}..."):
            patients = process_tsv_file(file_path)
            
            if patients:
                st.info(f"Extracted data for {len(patients)} patients from {os.path.basename(file_path)}")
                all_patients.extend(patients)
            else:
                st.warning(f"No patient data extracted from {os.path.basename(file_path)}")
    
    # Merge with clinical data if requested
    if include_clinical and all_patients:
        with st.spinner("Downloading and processing clinical data..."):
            clinical_path = download_clinical_data()
            
            if clinical_path:
                all_patients = merge_with_clinical_data(all_patients, clinical_path)
                st.info("Clinical data merged with gene expression data")
            else:
                st.warning("Failed to download clinical data")
    
    # Calculate pathway scores
    if all_patients:
        with st.spinner("Calculating pathway scores..."):
            all_patients = calculate_pathway_score(all_patients)
            st.info("Pathway scores calculated")
    
    # Store in MongoDB
    if all_patients:
        with st.spinner(f"Storing {len(all_patients)} patient records in MongoDB..."):
            success = insert_patient_data(all_patients)
            
            if success:
                st.success(f"Successfully stored {len(all_patients)} patient records in MongoDB")
            else:
                st.error("Failed to store data in MongoDB")
    else:
        st.warning("No patient data to store")
    
    return all_patients

def display_data_info():
    """Display information about the data in the database."""
    
    # Get patient count
    patient_count = get_patient_count()
    cohorts = get_unique_cohorts()
    
    # Display info
    st.subheader("Database Information")
    st.write(f"Total patients: {patient_count}")
    
    if cohorts:
        st.write("Cancer cohorts:")
        for cohort in cohorts:
            cohort_patients = get_patient_data({"cancer_cohort": cohort})
            st.write(f"- {cohort}: {len(cohort_patients)} patients")
    else:
        st.write("No cancer cohorts found in the database")

def display_visualizations():
    """Display visualizations of the gene expression data."""
    
    # Get data from MongoDB
    cohorts = get_unique_cohorts()
    
    if not cohorts:
        st.warning("No data found in the database. Please fetch and process data first.")
        return
    
    # Create tabs for different visualization types
    tab1, tab2, tab3, tab4 = st.tabs([
        "Gene Expression Boxplot", 
        "Gene Expression Heatmap", 
        "Gene Correlation", 
        "Pathway Scores"
    ])
    
    # For boxplot tab
    with tab1:
        st.subheader("Gene Expression by Cancer Cohort")
        
        selected_cohort = st.selectbox(
            "Select Cancer Cohort for Boxplot", 
            options=cohorts,
            key="boxplot_cohort"
        )
        
        # Filter patients by cohort
        filtered_patients = get_patient_data({"cancer_cohort": selected_cohort})
        
        if filtered_patients:
            st.write(f"Showing data for {len(filtered_patients)} patients in {selected_cohort}")
            fig = plot_gene_expressions_by_cohort(filtered_patients)
            st.pyplot(fig)
        else:
            st.warning(f"No patients found for cohort: {selected_cohort}")
    
    # For heatmap tab
    with tab2:
        st.subheader("Gene Expression Heatmap")
        
        selected_cohort = st.selectbox(
            "Select Cancer Cohort for Heatmap", 
            options=cohorts,
            key="heatmap_cohort"
        )
        
        max_patients = st.slider(
            "Maximum number of patients to display", 
            min_value=5, 
            max_value=100, 
            value=30
        )
        
        # Filter patients by cohort
        filtered_patients = get_patient_data({"cancer_cohort": selected_cohort}, limit=max_patients)
        
        if filtered_patients:
            st.write(f"Showing data for {len(filtered_patients)} patients in {selected_cohort}")
            fig = plot_heatmap(filtered_patients, max_patients)
            st.pyplot(fig)
        else:
            st.warning(f"No patients found for cohort: {selected_cohort}")
    
    # For correlation tab
    with tab3:
        st.subheader("Gene Correlation Analysis")
        
        selected_cohort = st.selectbox(
            "Select Cancer Cohort for Correlation Analysis", 
            options=cohorts,
            key="correlation_cohort"
        )
        
        # Filter patients by cohort
        filtered_patients = get_patient_data({"cancer_cohort": selected_cohort})
        
        if filtered_patients:
            st.write(f"Showing correlation for {len(filtered_patients)} patients in {selected_cohort}")
            fig = plot_gene_correlation(filtered_patients)
            st.pyplot(fig)
        else:
            st.warning(f"No patients found for cohort: {selected_cohort}")
    
    # For pathway scores tab
    with tab4:
        st.subheader("Pathway Scores Analysis")
        
        selected_cohort = st.selectbox(
            "Select Cancer Cohort for Pathway Analysis", 
            options=cohorts,
            key="pathway_cohort"
        )
        
        # Filter patients by cohort
        filtered_patients = get_patient_data({"cancer_cohort": selected_cohort})
        
        if filtered_patients:
            st.write(f"Showing pathway scores for {len(filtered_patients)} patients in {selected_cohort}")
            fig = plot_pathway_scores(filtered_patients)
            st.pyplot(fig)
        else:
            st.warning(f"No patients found for cohort: {selected_cohort}")

def main():
    """Main function for the Streamlit app."""
    
    st.title("TCGA Gene Expression Analyzer")
    
    st.markdown("""
    This application collects and analyzes gene expression data from The Cancer Genome Atlas (TCGA).
    It focuses on genes in the cGAS-STING pathway, which plays a crucial role in immune response.
    """)
    
    # Sidebar for data collection
    st.sidebar.title("Data Collection")
    
    use_sample = st.sidebar.checkbox("Use sample data (for testing)", value=True)
    include_clinical = st.sidebar.checkbox("Include clinical data", value=False)
    
    if not use_sample:
        max_datasets = st.sidebar.slider(
            "Maximum datasets to download", 
            min_value=1, 
            max_value=10, 
            value=1
        )
    else:
        max_datasets = 1
    
    if st.sidebar.button("Fetch and Process Data"):
        # Step 1: Fetch and store data
        files = fetch_and_store_data(use_sample, max_datasets)
        
        # Step 2: Process and store in MongoDB
        if files:
            process_and_store_data(files, include_clinical)
    
    # Main content area
    tab1, tab2 = st.tabs(["Data Overview", "Visualizations"])
    
    with tab1:
        display_data_info()
        
        # Display target genes information
        st.subheader("Target Genes (cGAS-STING Pathway)")
        gene_data = []
        for gene in TARGET_GENES:
            if gene == "C6orf150":
                gene_data.append({"Gene": gene, "Alternative Name": "cGAS", "Function": "Cytosolic DNA sensor"})
            elif gene == "TMEM173":
                gene_data.append({"Gene": gene, "Alternative Name": "STING", "Function": "Adaptor protein for cGAS"})
            elif gene == "CXCL8":
                gene_data.append({"Gene": gene, "Alternative Name": "IL8", "Function": "Proinflammatory chemokine"})
            else:
                gene_data.append({"Gene": gene, "Alternative Name": "", "Function": "Pathway component"})
        
        st.table(pd.DataFrame(gene_data))
    
    with tab2:
        display_visualizations()

if __name__ == "__main__":
    main() 