"""
Functions for processing gene expression data.
"""

import pandas as pd
import numpy as np
import os
import gzip
from config import TARGET_GENES

# Add a new constant for batch size
BATCH_SIZE = 1000  # Process 1000 patients at a time

def read_tsv_file(file_path, nrows=None):
    """
    Read a TSV file into a pandas DataFrame with optional row limit.
    
    Args:
        file_path (str): Path to the TSV file
        nrows (int, optional): Number of rows to read, None for all rows
        
    Returns:
        pandas.DataFrame: The loaded data
    """
    try:
        # Check if the file is gzipped
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rt') as f:
                return pd.read_csv(f, sep='\t', nrows=nrows)
        else:
            return pd.read_csv(file_path, sep='\t', nrows=nrows)
    except Exception as e:
        print(f"Error reading TSV file {file_path}: {e}")
        return None

def extract_gene_expressions(df, target_genes=TARGET_GENES):
    """
    Extract expression values for target genes from a DataFrame.
    
    Args:
        df (pandas.DataFrame): DataFrame containing gene expression data
        target_genes (list): List of target gene names
        
    Returns:
        pandas.DataFrame: DataFrame with expression values for target genes only
    """
    # Determine the structure of the DataFrame
    if df is None or df.empty:
        print("Empty DataFrame provided")
        return pd.DataFrame()
    
    # Debug information
    print(f"DataFrame has shape: {df.shape}")
    print(f"First 5 columns: {df.columns[:5].tolist()}")
    print(f"First column values (first 5): {df.iloc[:5, 0].tolist()}")
    
    # Check if the first column contains gene names (common format)
    gene_column = df.columns[0]  # Usually 'Gene' or similar
    
    try:
        # First approach: Check if the first column contains gene names
        # Convert to string to handle any non-string types
        df[gene_column] = df[gene_column].astype(str)
        
        # Try exact matching
        filtered_df = df[df[gene_column].isin(target_genes)]
        
        # If we didn't find any matches, try case-insensitive matching
        if filtered_df.empty:
            print("No exact matches found, trying case-insensitive matching...")
            filtered_df = df[df[gene_column].str.upper().isin([g.upper() for g in target_genes])]
        
        # If we still don't have matches, try partial matching (gene might be part of a longer string)
        if filtered_df.empty:
            print("No case-insensitive matches found, trying partial matching...")
            matches = []
            for gene in target_genes:
                pattern = rf".*{gene}.*"
                matches.extend(df[df[gene_column].str.contains(pattern, case=False, regex=True)].index.tolist())
            if matches:
                filtered_df = df.loc[matches]
        
        # Second approach: If genes are in the index
        if filtered_df.empty:
            print("Checking if genes are in the index...")
            if hasattr(df.index, 'str'):  # Make sure index has string methods
                matches = []
                for gene in target_genes:
                    if gene in df.index.tolist():
                        matches.append(gene)
                    else:
                        # Try case-insensitive
                        for idx in df.index:
                            if str(gene).upper() == str(idx).upper():
                                matches.append(idx)
                if matches:
                    filtered_df = df.loc[matches]
        
        # Third approach: Maybe each gene is a column
        if filtered_df.empty:
            print("Checking if genes are columns...")
            gene_cols = []
            for gene in target_genes:
                # Check for exact match in column names
                if gene in df.columns:
                    gene_cols.append(gene)
                else:
                    # Try case-insensitive
                    for col in df.columns:
                        if str(gene).upper() == str(col).upper():
                            gene_cols.append(col)
            
            if gene_cols:
                # Create a new DataFrame with gene names as the first column
                new_df = pd.DataFrame({"Gene": gene_cols})
                # For each patient (row in original df), add their values for these genes
                for patient in df.index:
                    patient_values = []
                    for gene in gene_cols:
                        patient_values.append(df.loc[patient, gene])
                    new_df[patient] = patient_values
                filtered_df = new_df
                
        if not filtered_df.empty:
            print(f"Found {len(filtered_df)} genes out of {len(target_genes)} target genes")
            return filtered_df
        
        # If we still couldn't find the genes, print more diagnostic info
        print(f"Could not identify target genes in the dataset.")
        print(f"DataFrame columns: {df.columns.tolist()[:10]}")
        print(f"Looking for genes: {target_genes}")
        
        # Return an empty DataFrame
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Error extracting gene expressions: {e}")
        return pd.DataFrame()

def transform_to_patient_centric(df, cohort_name):
    """
    Transform gene-centric data to patient-centric format.
    
    Args:
        df (pandas.DataFrame): DataFrame containing gene expression data
        cohort_name (str): Name of the cancer cohort
        
    Returns:
        list: List of dictionaries, one per patient
    """
    if df is None or df.empty:
        return []
    
    # Determine the structure of the DataFrame
    gene_column = df.columns[0]  # Usually 'Gene' or similar
    patient_columns = df.columns[1:]  # Remaining columns are patient IDs
    
    patients = []
    
    for patient_id in patient_columns:
        # Create a dictionary for this patient
        patient_data = {
            "patient_id": patient_id,
            "cancer_cohort": cohort_name,
            "gene_expressions": {}
        }
        
        # Add expression values for each target gene
        for _, row in df.iterrows():
            gene = row[gene_column]
            expression = row[patient_id]
            
            # Convert to float if possible, otherwise use as is
            try:
                expression_value = float(expression)
            except (ValueError, TypeError):
                expression_value = str(expression)
                
            patient_data["gene_expressions"][gene] = expression_value
        
        patients.append(patient_data)
    
    return patients

def process_tsv_file(file_path):
    """
    Process a TSV file to extract gene expressions for target genes.
    Optimized to handle large files with batching.
    
    Args:
        file_path (str): Path to the TSV file
        
    Returns:
        list: List of patient dictionaries with gene expression data
    """
    # Extract cohort name from filename
    cohort_name = os.path.basename(file_path).split('_')[0]
    
    print(f"Processing file: {file_path} for cohort: {cohort_name}")
    
    # First, try to determine the file structure by reading a small sample
    print("Reading sample of the file to determine structure...")
    sample_df = read_tsv_file(file_path, nrows=10)
    if sample_df is None:
        print(f"Failed to read sample from file: {file_path}")
        return []
    
    # Print info about the DataFrame
    print(f"Sample DataFrame shape: {sample_df.shape}")
    print(f"Sample DataFrame columns (first 5): {sample_df.columns[:5]}")
    
    # Check if we're dealing with the special TCGA format
    # The first column is often 'sample' and the gene symbols are in the row index
    is_tcga_format = 'sample' in sample_df.columns or sample_df.shape[1] > 100
    
    # Process the file in batches if it's large
    if is_tcga_format:
        print("Detected TCGA format with genes as rows, processing in batches...")
        return process_tcga_format_file(file_path, cohort_name)
    else:
        print("Processing standard format file...")
        return process_standard_format_file(file_path, cohort_name)

def process_tcga_format_file(file_path, cohort_name):
    """
    Process a TCGA format file where genes are rows and patients are columns.
    Uses chunking to handle large files efficiently.
    
    Args:
        file_path (str): Path to the TSV file
        cohort_name (str): Name of the cancer cohort
        
    Returns:
        list: List of patient dictionaries with gene expression data
    """
    try:
        # Read the file
        df = read_tsv_file(file_path)
        if df is None:
            print(f"Failed to read file: {file_path}")
            return []
        
        print(f"DataFrame shape: {df.shape}")
        
        # Set the first column as index if needed
        if df.columns[0] != 'sample' and 'sample' in df.columns:
            df = df.set_index('sample')
        
        # Find which columns contain our target genes
        selected_genes = []
        for gene in TARGET_GENES:
            if gene in df.index:
                selected_genes.append(gene)
            else:
                # Case-insensitive search
                for idx in df.index:
                    if isinstance(idx, str) and gene.upper() == idx.upper():
                        selected_genes.append(idx)
                        break
        
        if not selected_genes:
            print(f"None of the target genes found in dataset {file_path}")
            # Try a fallback - look for similar gene names
            for idx in df.index:
                for gene in TARGET_GENES:
                    if isinstance(idx, str) and gene.upper() in idx.upper():
                        print(f"Found potential match: {idx} for {gene}")
                        selected_genes.append(idx)
        
        if not selected_genes:
            print(f"Still couldn't find any target genes in {file_path}")
            return []
        
        # Extract just the expression data for selected genes
        gene_df = df.loc[selected_genes]
        
        # Process patients in batches
        all_patients = []
        
        # Get column batches
        for i in range(0, len(gene_df.columns), BATCH_SIZE):
            print(f"Processing batch {i//BATCH_SIZE + 1}")
            batch_columns = gene_df.columns[i:i+BATCH_SIZE]
            
            # Create patient records for this batch
            batch_patients = []
            for patient_id in batch_columns:
                patient_data = {
                    "patient_id": patient_id,
                    "cancer_cohort": cohort_name,
                    "gene_expressions": {}
                }
                
                # Add expression values for each gene
                for gene in selected_genes:
                    try:
                        expression_value = float(gene_df.loc[gene, patient_id])
                        
                        # Skip invalid values
                        if not np.isnan(expression_value):
                            patient_data["gene_expressions"][gene] = expression_value
                    except (ValueError, TypeError):
                        # Skip non-numeric values
                        pass
                
                # Only add patients with at least one valid gene expression
                if patient_data["gene_expressions"]:
                    batch_patients.append(patient_data)
            
            # Add this batch to all patients
            all_patients.extend(batch_patients)
            print(f"Processed {len(batch_patients)} patients in batch {i//BATCH_SIZE + 1}")
        
        print(f"Total patients processed: {len(all_patients)}")
        return all_patients
        
    except Exception as e:
        print(f"Error processing TCGA format file: {e}")
        return []

def process_standard_format_file(file_path, cohort_name):
    """
    Process a standard format file where genes are in the first column.
    
    Args:
        file_path (str): Path to the TSV file
        cohort_name (str): Name of the cancer cohort
        
    Returns:
        list: List of patient dictionaries with gene expression data
    """
    try:
        # Read the file
        df = read_tsv_file(file_path)
        if df is None:
            print(f"Failed to read file: {file_path}")
            return []
        
        # Extract the gene expression data
        filtered_df = extract_gene_expressions(df)
        
        if filtered_df.empty:
            print(f"No gene expressions extracted from {file_path}")
            return []
        
        # Transform to patient-centric format
        patients = transform_to_patient_centric(filtered_df, cohort_name)
        
        print(f"Extracted data for {len(patients)} patients")
        return patients
        
    except Exception as e:
        print(f"Error processing standard format file: {e}")
        return []

def merge_with_clinical_data(gene_data, clinical_file_path):
    """
    Merge gene expression data with clinical data.
    
    Args:
        gene_data (list): List of patient dictionaries with gene expression data
        clinical_file_path (str): Path to clinical data TSV file
        
    Returns:
        list: List of patient dictionaries with gene and clinical data
    """
    # Read clinical data
    clinical_df = read_tsv_file(clinical_file_path)
    if clinical_df is None:
        return gene_data  # Return original data if clinical data can't be read
    
    # Create a dictionary to map patient IDs to clinical data
    clinical_dict = {}
    
    # Determine which column contains patient IDs
    id_column = None
    possible_id_columns = ['patient_id', 'sample', 'bcr_patient_barcode', '_PATIENT', 'PATIENT_ID']
    
    for col in possible_id_columns:
        if col in clinical_df.columns:
            id_column = col
            break
    
    if id_column is None:
        print("Could not identify patient ID column in clinical data")
        return gene_data
    
    # Create mapping from patient ID to clinical data
    for _, row in clinical_df.iterrows():
        patient_id = row[id_column]
        clinical_dict[patient_id] = row.to_dict()
    
    # Merge clinical data into gene expression data
    merged_data = []
    
    for patient in gene_data:
        patient_id = patient['patient_id']
        
        # Create a copy of the patient data
        merged_patient = patient.copy()
        
        # Try to find a matching clinical record
        clinical_record = None
        
        # Try exact match first
        if patient_id in clinical_dict:
            clinical_record = clinical_dict[patient_id]
        else:
            # Try to find a partial match (some TCGA IDs have different formats)
            for clin_id in clinical_dict:
                if (patient_id in clin_id) or (clin_id in patient_id):
                    clinical_record = clinical_dict[clin_id]
                    break
        
        # Add clinical data if found
        if clinical_record:
            merged_patient['clinical_data'] = clinical_record
            
        merged_data.append(merged_patient)
    
    return merged_data

def calculate_pathway_score(patient_data):
    """
    Calculate a simplified pathway score for each patient based on cGAS-STING pathway genes.
    
    Args:
        patient_data (list): List of patient dictionaries with gene expression data
        
    Returns:
        list: Patient data with added pathway scores
    """
    # Define gene groupings for pathway scoring
    pathway_genes = {
        'cGAS_activation': ['C6orf150', 'TMEM173'],  # cGAS and STING
        'inflammatory_response': ['CCL5', 'CXCL10', 'CXCL9', 'CXCL11', 'IL6', 'CXCL8'],
        'signaling': ['NFKB1', 'IKBKE', 'IRF3', 'TREX1', 'ATM']
    }
    
    # Create a copy of patient data to modify
    scored_patients = []
    
    for patient in patient_data:
        # Create a copy of the patient data
        scored_patient = patient.copy()
        gene_expressions = patient['gene_expressions']
        
        # Initialize pathway scores
        pathway_scores = {}
        
        # Calculate scores for each pathway group
        for pathway, genes in pathway_genes.items():
            # Get expression values for genes in this pathway
            values = []
            for gene in genes:
                if gene in gene_expressions:
                    value = gene_expressions[gene]
                    # Check if value is numeric
                    if isinstance(value, (int, float)) and not np.isnan(value):
                        values.append(value)
            
            # Calculate score if we have values
            if values:
                pathway_scores[pathway] = np.mean(values)
            else:
                pathway_scores[pathway] = None
        
        # Calculate overall pathway score if all component scores exist
        if all(score is not None for score in pathway_scores.values()):
            # Simple weighted average
            pathway_scores['overall'] = (
                pathway_scores['cGAS_activation'] * 0.4 + 
                pathway_scores['inflammatory_response'] * 0.4 + 
                pathway_scores['signaling'] * 0.2
            )
        else:
            pathway_scores['overall'] = None
            
        # Add scores to patient data
        scored_patient['pathway_scores'] = pathway_scores
        scored_patients.append(scored_patient)
    
    return scored_patients 