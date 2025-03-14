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
from database import insert_patient_data, get_patient_data, get_unique_cohorts, get_patient_count, clear_collection
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

def fetch_and_store_data(use_sample_data=False, max_datasets=1, use_local_files=False, local_files_dir="data_test"):
    """
    Fetch data from Xena Browser and store in MiniO.
    
    Args:
        use_sample_data (bool): Whether to use sample data instead of downloading
        max_datasets (int): Maximum number of datasets to download
        use_local_files (bool): Whether to use already downloaded files
        local_files_dir (str): Directory containing already downloaded files
        
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
    elif use_local_files:
        # Use locally downloaded files
        with st.spinner(f"Processing locally downloaded files from {local_files_dir}..."):
            if os.path.exists(local_files_dir):
                for filename in os.listdir(local_files_dir):
                    if filename.endswith('.gz'):
                        # Extract cohort code from filename (assuming format like "LAML_gene_expression.gz")
                        code = filename.split('_')[0]
                        file_path = os.path.join(local_files_dir, filename)
                        
                        files.append({
                            'path': file_path,
                            'cohort': f'TCGA {code}',
                            'code': code,
                            'name': 'Gene Expression'
                        })
                
                st.info(f"Found {len(files)} local files to process")
            else:
                st.error(f"Local directory {local_files_dir} does not exist")
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
        
        st.success(f"Successfully processed and stored {len(files)} files.")
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
    """Main application logic."""
    
    # Application header
    st.title("TCGA Gene Expression Analyzer")
    st.write("Analyze gene expression data from The Cancer Genome Atlas (TCGA)")
    
    # Sidebar options
    st.sidebar.title("Data Options")
    
    # Database info or setup
    db_status = st.sidebar.container()
    patient_count = get_patient_count()
    
    if patient_count > 0:
        db_status.success(f"MongoDB: {patient_count} patient records")
    else:
        db_status.warning("MongoDB: No data loaded")
    
    # Data processing section
    st.sidebar.header("Data Processing")
    
    # Option to use sample data instead of real data
    use_sample = st.sidebar.checkbox("Use sample data instead of real data", False)
    
    # Option to limit the number of datasets to process
    process_all = st.sidebar.checkbox("Process all available datasets", True)
    max_cohorts = None if process_all else st.sidebar.slider(
        "Maximum number of cohorts to process", 
        min_value=1, 
        max_value=20, 
        value=5
    )
    
    # Option to include clinical data
    include_clinical = st.sidebar.checkbox("Include clinical data", True)
    
    # Option to use locally downloaded files
    use_local_files = st.sidebar.checkbox("Use locally downloaded files", True)
    local_files_dir = st.sidebar.text_input(
        "Local files directory", 
        value="data_test_subset"
    )
    
    # Option to use MongoDB
    use_mongodb = st.sidebar.checkbox("Store data in MongoDB", True)
    
    # Process & Import button
    if st.sidebar.button("Process & Import Data"):
        # Clear the current data if requested
        clear_mongo = st.sidebar.checkbox("Clear existing MongoDB data before import", False)
        if clear_mongo:
            with st.spinner("Clearing existing data from MongoDB..."):
                clear_collection()
                st.success("Existing data cleared from MongoDB")
        
        # Step 1: Get the data files
        files = fetch_and_store_data(
            use_sample_data=use_sample, 
            max_datasets=max_cohorts if not process_all else None, 
            use_local_files=use_local_files, 
            local_files_dir=local_files_dir
        )
        
        # Limit number of files to process if needed
        if use_local_files and not process_all and max_cohorts is not None and len(files) > max_cohorts:
            st.info(f"Limiting processing to {max_cohorts} cohorts out of {len(files)} available")
            files = files[:max_cohorts]
        
        # Step 2: Process and store in MongoDB
        if files and use_mongodb:
            process_and_store_data(files, include_clinical)
        elif files:
            # If not using MongoDB, just process the files
            all_patients = []
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
            
            st.success(f"Successfully processed {len(all_patients)} patient records (not stored in MongoDB)")
    
    # Main content area
    tab1, tab2 = st.tabs(["Data Overview", "Visualizations"])
    
    with tab1:
        display_data_info()
        
        # Display target genes information
        st.subheader("Target Genes (Cancer-Related Genes)")
        gene_data = []
        for gene in TARGET_GENES:
            gene_data.append({"Gene": gene, "Function": "Cancer-related gene"})
        
        st.table(pd.DataFrame(gene_data))
    
    with tab2:
        display_visualizations()

if __name__ == "__main__":
    main()