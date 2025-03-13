"""
Functions for visualizing gene expression data.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from config import TARGET_GENES
import io
import base64

# Set up styling for plots
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")

def prepare_data_for_visualization(patient_data):
    """
    Prepare patient data for visualization.
    
    Args:
        patient_data (list): List of patient dictionaries
        
    Returns:
        pandas.DataFrame: DataFrame suitable for visualization
    """
    # Create a list to hold the flattened data
    flattened_data = []
    
    for patient in patient_data:
        patient_id = patient['patient_id']
        cohort = patient['cancer_cohort']
        
        # Add each gene expression as a row
        for gene, expression in patient['gene_expressions'].items():
            # Skip non-numeric values
            if not isinstance(expression, (int, float)) or np.isnan(expression):
                continue
                
            flattened_data.append({
                'patient_id': patient_id,
                'cancer_cohort': cohort,
                'gene': gene,
                'expression': expression
            })
    
    return pd.DataFrame(flattened_data)

def plot_gene_expressions_by_cohort(patient_data, figsize=(15, 10)):
    """
    Create a boxplot of gene expressions by cancer cohort.
    
    Args:
        patient_data (list): List of patient dictionaries
        figsize (tuple): Figure size
        
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Prepare data
    df = prepare_data_for_visualization(patient_data)
    
    if df.empty:
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No data available for visualization", 
                 ha='center', va='center', fontsize=14)
        plt.gca().set_axis_off()
        return plt.gcf()
    
    # Create the figure
    plt.figure(figsize=figsize)
    
    # Create the boxplot
    ax = sns.boxplot(x='gene', y='expression', hue='cancer_cohort', data=df)
    
    # Customize the plot
    plt.title('Gene Expression by Cancer Cohort', fontsize=16)
    plt.xlabel('Gene', fontsize=12)
    plt.ylabel('Expression Level', fontsize=12)
    plt.xticks(rotation=45)
    
    # Add median labels
    # Group by gene and cohort, and calculate median
    medians = df.groupby(['gene', 'cancer_cohort'])['expression'].median().reset_index()
    
    # Add legend outside the plot
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    
    return plt.gcf()

def plot_heatmap(patient_data, max_patients=50, figsize=(12, 10)):
    """
    Create a heatmap of gene expressions for patients.
    
    Args:
        patient_data (list): List of patient dictionaries
        max_patients (int): Maximum number of patients to include
        figsize (tuple): Figure size
        
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Limit to max_patients
    if len(patient_data) > max_patients:
        patient_data = patient_data[:max_patients]
    
    # Create a DataFrame with genes as columns and patients as rows
    data = []
    
    for patient in patient_data:
        patient_row = {
            'patient_id': patient['patient_id'],
            'cancer_cohort': patient['cancer_cohort']
        }
        
        # Add gene expressions
        for gene, expression in patient['gene_expressions'].items():
            # Convert to float if possible
            if isinstance(expression, (int, float)) and not np.isnan(expression):
                patient_row[gene] = expression
            else:
                patient_row[gene] = np.nan
        
        data.append(patient_row)
    
    df = pd.DataFrame(data)
    
    # Check if we have data to visualize
    if len(df) == 0 or all(col in ['patient_id', 'cancer_cohort'] for col in df.columns):
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No gene expression data available for heatmap", 
                 ha='center', va='center', fontsize=14)
        plt.gca().set_axis_off()
        return plt.gcf()
    
    # Set patient_id as index
    df.set_index('patient_id', inplace=True)
    
    # Extract just the gene expression columns
    gene_df = df.drop(columns=['cancer_cohort'], errors='ignore')
    
    # Create the figure
    plt.figure(figsize=figsize)
    
    # Create the heatmap
    cmap = sns.diverging_palette(220, 20, as_cmap=True)
    sns.heatmap(gene_df, cmap=cmap, linewidths=0.5, 
                cbar_kws={'label': 'Expression Level'})
    
    # Customize the plot
    plt.title('Gene Expression Heatmap', fontsize=16)
    plt.ylabel('Patient ID', fontsize=12)
    plt.xlabel('Gene', fontsize=12)
    plt.tight_layout()
    
    return plt.gcf()

def plot_gene_correlation(patient_data, figsize=(12, 10)):
    """
    Create a correlation heatmap of gene expressions.
    
    Args:
        patient_data (list): List of patient dictionaries
        figsize (tuple): Figure size
        
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Prepare data for correlation analysis
    df = prepare_data_for_visualization(patient_data)
    
    if df.empty:
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No data available for correlation analysis", 
                 ha='center', va='center', fontsize=14)
        plt.gca().set_axis_off()
        return plt.gcf()
    
    # Pivot the data to get gene-gene correlation matrix
    pivot_df = df.pivot_table(
        index='patient_id',
        columns='gene',
        values='expression'
    )
    
    # Calculate correlation
    corr = pivot_df.corr()
    
    # Create the figure
    plt.figure(figsize=figsize)
    
    # Create the heatmap
    mask = np.triu(np.ones_like(corr, dtype=bool))
    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    
    sns.heatmap(
        corr, 
        mask=mask, 
        cmap=cmap, 
        vmax=1, 
        vmin=-1, 
        center=0,
        square=True, 
        linewidths=.5, 
        cbar_kws={"shrink": .5, "label": "Correlation Coefficient"}
    )
    
    # Customize the plot
    plt.title('Gene Expression Correlation', fontsize=16)
    plt.tight_layout()
    
    return plt.gcf()

def plot_pathway_scores(patient_data, figsize=(12, 8)):
    """
    Create a violin plot of pathway scores.
    
    Args:
        patient_data (list): List of patient dictionaries with pathway scores
        figsize (tuple): Figure size
        
    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Check if pathway scores exist
    if not patient_data or 'pathway_scores' not in patient_data[0]:
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No pathway scores available", 
                 ha='center', va='center', fontsize=14)
        plt.gca().set_axis_off()
        return plt.gcf()
    
    # Prepare data for visualization
    pathway_data = []
    
    for patient in patient_data:
        patient_id = patient['patient_id']
        cohort = patient['cancer_cohort']
        
        for pathway, score in patient['pathway_scores'].items():
            # Skip non-numeric or None values
            if score is None or not isinstance(score, (int, float)) or np.isnan(score):
                continue
                
            pathway_data.append({
                'patient_id': patient_id,
                'cancer_cohort': cohort,
                'pathway': pathway,
                'score': score
            })
    
    df = pd.DataFrame(pathway_data)
    
    if df.empty:
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, "No valid pathway scores available for visualization", 
                 ha='center', va='center', fontsize=14)
        plt.gca().set_axis_off()
        return plt.gcf()
    
    # Create the figure
    plt.figure(figsize=figsize)
    
    # Check how many unique cohorts we have
    num_cohorts = df['cancer_cohort'].nunique()
    
    # Create the violin plot - only use split=True if we have exactly 2 cohorts
    if num_cohorts == 2:
        ax = sns.violinplot(x='pathway', y='score', hue='cancer_cohort', data=df, split=True)
    else:
        # For other cases (1 or more than 2 cohorts), don't use split
        ax = sns.violinplot(x='pathway', y='score', hue='cancer_cohort', data=df)
    
    # Customize the plot
    plt.title('Pathway Scores by Cancer Cohort', fontsize=16)
    plt.xlabel('Pathway', fontsize=12)
    plt.ylabel('Score', fontsize=12)
    
    # Add legend outside the plot
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    
    return plt.gcf()

def get_figure_as_base64(fig):
    """
    Convert a matplotlib figure to a base64 encoded string.
    
    Args:
        fig (matplotlib.figure.Figure): The figure to convert
        
    Returns:
        str: Base64 encoded string
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return img_str