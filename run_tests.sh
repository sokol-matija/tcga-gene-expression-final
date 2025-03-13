#!/bin/bash
echo "Setting up virtual environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating new virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the cloud storage test
echo "Running cloud storage tests..."
python test_cloud_storage.py

# Run the Streamlit app
echo ""
echo "To run the Streamlit app, use the following command:"
echo "streamlit run app.py"

# Keep the terminal open
echo ""
echo "Press Enter to exit..."
read 