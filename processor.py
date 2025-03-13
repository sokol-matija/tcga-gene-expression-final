"""
Functions for processing gene expression data.
"""

import pandas as pd
import numpy as np
import os
import gzip
from config import TARGET_GENES

def read_tsv_file(file_path):
    """
    Read a TSV file into a pandas DataFrame.
    
    Args:
        file_path (str): Path to the TSV file
        
    Returns:
        pandas.DataFrame: The loaded data
    """
    try:
        # Check if the file is gzipped
        if file_path.endswith('.gz'):
            with gzip.open(file_path, 'rt') as f:
                return pd.read_csv(f, sep='\t')
        else:
            return pd.read_csv(file_path, sep='\t')
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
    
    # Check if the first column contains gene names (common format)
    gene_column = df.columns[0]  # Usually 'Gene' or similar
    
    try:
        # Check if DataFrame has genes as first column
        if any(gene in str(df[gene_column]) for gene in target_genes):
            # Filter rows where the gene is in our target list
            filtered_df = df[df[gene_column].isin(target_genes)]
            
            # If we didn't find any matches, try case-insensitive matching
            if filtered_df.empty:
                filtered_df = df[df[gene_column].str.upper().isin([g.upper() for g in target_genes])]
                
            return filtered_df
        
        # If genes are not in the first column, check if they are in the index
        elif any(gene in str(df.index) for gene in target_genes):
            # Filter rows where the index is in our target list
            filtered_df = df[df.index.isin(target_genes)]
            
            # If we didn't find any matches, try case-insensitive matching
            if filtered_df.empty and hasattr(df.index, 'str'):
                filtered_df = df[df.index.str.upper().isin([g.upper() for g in target_genes])]
                
            return filtered_df
        
        # If we can't find the genes in either place, print a warning
        print(f"Could not identify target genes in the dataset. First column: {gene_column}")
        
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
    
    Args:
        file_path (str): Path to the TSV file
        
    Returns:
        list: List of patient dictionaries with gene expression data
    """
    # Extract cohort name from filename
    cohort_name = os.path.basename(file_path).split('_')[0]
    
    # Read the file
    print(f"Reading file: {file_path}")
    df = read_tsv_file(file_path)
    if df is None:
        return []
    
    # Print info about the DataFrame
    print(f"DataFrame shape: {df.shape}")
    print(f"DataFrame columns (first 5): {df.columns[:5]}")
    
    # Extract target gene expressions
    print(f"Extracting expressions for {len(TARGET_GENES)} target genes")
    gene_df = extract_gene_expressions(df)
    
    if gene_df.empty:
        print(f"No target genes found in {file_path}")
        return []
    
    print(f"Found {len(gene_df)} matching genes")
    
    # Transform to patient-centric format
    print("Transforming to patient-centric format")
    patients = transform_to_patient_centric(gene_df, cohort_name)
    
    print(f"Generated {len(patients)} patient records")
    return patients

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