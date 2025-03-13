# TCGA Gene Expression Analyzer

A system for collecting, storing, processing, and visualizing gene expression data from The Cancer Genome Atlas (TCGA) project, with a focus on the cGAS-STING pathway.

## Project Overview

This application:

1. Downloads TSV files containing gene expression data from the TCGA project
2. Stores these files in MiniO (an unstructured cloud storage solution)
3. Processes the data to extract specific gene expressions for the cGAS-STING pathway
4. Stores the processed data in MongoDB (a NoSQL database)
5. Creates visualizations of the gene expression data
6. Optionally merges this data with clinical patient data

## System Requirements

- Python 3.8 or higher
- Docker (for running MiniO and MongoDB)

## Setup Instructions

### 1. Clone the repository

```bash
git clone [repository-url]
cd tcga-gene-expression
```

### 2. Set up a virtual environment

```bash
# Create virtual environment
python -m venv venv

# Activate the environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run MiniO and MongoDB with Docker

```bash
# Start MiniO
docker run -p 9000:9000 -p 9001:9001 --name minio -d \
    -e "MINIO_ROOT_USER=minioadmin" \
    -e "MINIO_ROOT_PASSWORD=minioadmin" \
    minio/minio server /data --console-address ":9001"

# Start MongoDB
docker run -p 27017:27017 --name mongodb -d mongo:latest
```

### 5. Run the application

```bash
streamlit run app.py
```

The application will be available at http://localhost:8501

## Using the Application

1. **Data Collection**: Use the sidebar to select data collection options:
   - Use sample data (for testing)
   - Include clinical data
   - Set the maximum number of datasets to download

2. **Click "Fetch and Process Data"** to download, process, and store the data

3. **View visualizations** in the "Visualizations" tab:
   - Gene Expression Boxplot
   - Gene Expression Heatmap
   - Gene Correlation
   - Pathway Scores

## Project Structure

- `app.py` - Main application
- `config.py` - Configuration variables
- `scraper.py` - Web scraping functionality
- `storage.py` - MiniO storage functions
- `processor.py` - Data processing functions
- `database.py` - MongoDB functions
- `visualizer.py` - Data visualization

## Target Genes

The application focuses on the following genes in the cGAS-STING pathway:

- C6orf150 (cGAS)
- TMEM173 (STING)
- CCL5
- CXCL10
- CXCL9
- CXCL11
- NFKB1
- IKBKE
- IRF3
- TREX1
- ATM
- IL6
- CXCL8 (IL8)

## License

[Include license information here] 