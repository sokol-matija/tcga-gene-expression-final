# TCGA Gene Expression Analyzer

A system for collecting, storing, processing, and visualizing gene expression data from The Cancer Genome Atlas (TCGA) project, with a focus on the cGAS-STING pathway.

## Project Overview

This application:

1. Downloads TSV files containing gene expression data from the TCGA project
2. Stores these files in AWS S3 bucket (cloud storage)
3. Processes the data to extract specific gene expressions for the cGAS-STING pathway
4. Stores the processed data in MongoDB Atlas (cloud database)
5. Creates visualizations of the gene expression data
6. Optionally merges this data with clinical patient data

## System Requirements

- Python 3.11.9 (tested and working)
- AWS S3 bucket access
- MongoDB Atlas access

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
playwright install
```

### 4. Configure Environment Variables

Create a `.env` file in the project root with your cloud service credentials:

```env
# AWS S3 credentials
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# MongoDB credentials
MONGO_CONNECTION_STRING=your_mongodb_atlas_connection_string
```

### 5. Run the application

```bash
# Note: Lower ports might be restricted on corporate laptops
streamlit run app.py --server.port 17002
```

The application will be available at http://localhost:17002

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

- `app.py` - Main Streamlit application
- `config.py` - Configuration variables
- `scraper.py` - Web scraping functionality (using Playwright)
- `storage.py` - AWS S3 storage functions
- `processor.py` - Data processing functions
- `database.py` - MongoDB Atlas functions
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

## Troubleshooting

1. **Port Access Issues**: If you get a socket permission error with the default Streamlit port, use a higher port number:
   ```bash
   streamlit run app.py --server.port 17002
   ```

2. **Browser Issues**: If you encounter browser-related errors, ensure Playwright is properly installed:
   ```bash
   playwright install
   ```

## License

[Include license information here] 