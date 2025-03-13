@echo off
echo Setting up virtual environment...

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating new virtual environment...
    py -3.11 -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

:: Run the cloud storage test
echo Running cloud storage tests...
python test_cloud_storage.py

:: Run the Streamlit app
echo.
echo To run the Streamlit app, use the following command:
echo streamlit run app.py

:: Keep the window open
echo.
echo Press any key to exit...
pause > nul 