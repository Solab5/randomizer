from fastapi import FastAPI, Request, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
import pandas as pd
from pathlib import Path
import os
import tempfile
import json
import shutil
from typing import Dict, List, Optional
import numpy as np
from io import BytesIO
import random
from datetime import datetime

from common_functions.utils import read_file, prepare_data
from sampling.sampling_functions import *

# Constants
REQUIRED_COLUMNS = [
    'district', 'subcounty', 'parish_t', 'cluster_t', 'village',
    'lat_x', 'long_y', 'hhh_full_name', 'Household_Head_Age',
    'Household_Head_Contact', 'Spouse_Name', 'Telephone_Contact', 'hhid'
]

SUPPORTED_FILE_TYPES = ('.csv', '.xls', '.xlsx')

# Required columns for contractor assignment
REQUIRED_CONTRACTOR_COLUMNS = ['village', 'status', 'HHHeadship']

# Initialize FastAPI app
app = FastAPI(
    title="RTV AHS/BHS Random Sample Generator",
    description="A tool for generating random samples from household data",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# In-memory data store (replace with database in production)
processed_data: Dict = {}
processed_contractors = None

class DataProcessor:
    @staticmethod
    def validate_columns(df: pd.DataFrame) -> Optional[str]:
        """Validate that all required columns are present in the dataframe."""
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            return f"Missing required columns: {', '.join(missing_columns)}"
        return None

    @staticmethod
    def process_data(df: pd.DataFrame) -> Dict:
        """Process the dataframe and return the results."""
        village_counts = df['village'].value_counts()
        final_df = get_final_df(df.copy(), village_counts)
        
        return {
            'data': final_df.to_dict(orient='records'),
            'village_count': len(village_counts),
            'sample_count': len(final_df),
            'preview': final_df.head(5).to_dict(orient='records')
        }

class FileHandler:
    @staticmethod
    async def save_uploaded_file(file: UploadFile) -> str:
        """Save uploaded file to temporary location and return path."""
        if not file.filename.endswith(SUPPORTED_FILE_TYPES):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Only CSV and Excel files are supported."
            )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp.seek(0)
            return tmp.name

    @staticmethod
    def create_download_file(data: List[Dict], background_tasks: BackgroundTasks) -> FileResponse:
        """Create a temporary file for download and return FileResponse."""
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, "sampled_data.csv")
        
        df = pd.DataFrame(data)
        df.to_csv(temp_file_path, index=False)
        
        background_tasks.add_task(shutil.rmtree, temp_dir)
        
        return FileResponse(
            path=temp_file_path,
            filename="sampled_data.csv",
            media_type='text/csv'
        )

def check_required_contractor_columns(df: pd.DataFrame) -> bool:
    missing_columns = [col for col in REQUIRED_CONTRACTOR_COLUMNS if col not in df.columns]
    if missing_columns:
        error_message = f"Missing columns: {', '.join(missing_columns)}. Please include the following columns in your dataset: {', '.join(REQUIRED_CONTRACTOR_COLUMNS)}"
        raise HTTPException(status_code=400, detail=error_message)
    return True

def assign_contractors_with_gender(df: pd.DataFrame, village_name: str) -> pd.DataFrame:
    distribution = [(4, 2, 2)] * 3 + [(4, 2, 1)]
    reserve_distribution = [(2, 1, 1)] * 4
    combined_df = pd.DataFrame()
    
    # Check for required HHHeadship categories
    required_categories = ["Male Headed", "Female Headed", "Youth Headed"]
    missing_categories = [cat for cat in required_categories if cat not in df["HHHeadship"].unique()]
    
    if missing_categories:
        print(f"Warning: Missing HHHeadship categories: {', '.join(missing_categories)}")

    for status in df["status"].unique():
        status_df = df[(df["village"] == village_name) & (df["status"] == status)].copy()
        status_df['Contractor'] = None

        # Choose the distribution based on the status
        if status == "target":
            distribution = distribution
        elif status == "reserve":
            distribution = reserve_distribution
        else:
            continue

        for contractor_num, (men, women, youths) in enumerate(distribution, start=1):
            contractor = f"Contractor {contractor_num}"
            for category, count in zip(required_categories, [men, women, youths]):
                rows = status_df[(status_df["HHHeadship"] == category) & (status_df["Contractor"].isna())][:count]
                status_df.loc[rows.index, "Contractor"] = contractor

        combined_df = pd.concat([combined_df, status_df])

    return combined_df

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload and processing."""
    temp_file_path = None
    try:
        # Save uploaded file
        temp_file_path = await FileHandler.save_uploaded_file(file)
        
        # Read and process the file
        data = read_file(temp_file_path)
        df = prepare_data(data.copy())
        
        # Validate columns
        if error := DataProcessor.validate_columns(df):
            raise HTTPException(status_code=400, detail=error)
        
        # Process data
        result = DataProcessor.process_data(df)
        
        # Store processed data
        processed_data['current'] = result
        
        return JSONResponse({
            "status": "success",
            "message": "File processed successfully",
            "village_count": result['village_count'],
            "sample_count": result['sample_count'],
            "preview": result['preview']
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        # Clean up temporary files
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@app.get("/download")
async def download_file(background_tasks: BackgroundTasks):
    """Handle file download."""
    if 'current' not in processed_data:
        raise HTTPException(
            status_code=400,
            detail="No processed data available. Please upload a file first."
        )
    
    try:
        return FileHandler.create_download_file(
            processed_data['current']['data'],
            background_tasks
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating download file: {str(e)}"
        )

@app.get("/contractors", response_class=HTMLResponse)
async def contractors_page(request: Request):
    return templates.TemplateResponse("contractors.html", {"request": request})

@app.post("/assign_contractors")
async def assign_contractors(file: UploadFile = File(...)):
    try:
        # Read the uploaded file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)

        # Check required columns
        check_required_contractor_columns(df)

        # Process the data
        processed_df = df.groupby('village').apply(lambda x: assign_contractors_with_gender(x, x.name)).reset_index(drop=True)
        
        # Store the processed data
        global processed_contractors
        processed_contractors = processed_df

        # Prepare preview data
        preview_data = processed_df.head(10).to_dict('records')
        
        return {
            "village_count": len(processed_df['village'].unique()),
            "contractor_count": len(processed_df['Contractor'].unique()),
            "preview": preview_data
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/download_contractors")
async def download_contractors():
    if processed_contractors is None:
        raise HTTPException(status_code=400, detail="No data available for download")
    
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            # Write the Excel file to the temporary file
            with pd.ExcelWriter(tmp.name, engine='openpyxl') as writer:
                processed_contractors.to_excel(writer, index=False)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"assigned_contractors_{timestamp}.xlsx"
            
            # Return the file response
            return FileResponse(
                path=tmp.name,
                filename=filename,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                background=BackgroundTasks([lambda: os.unlink(tmp.name)])
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper function
def get_final_df(df: pd.DataFrame, village_counts: pd.Series, 
                male_prop: float = 0.6, female_prop: float = 0.2, 
                youth_prop: float = 0.2, threshold: int = 100) -> pd.DataFrame:
    """Generate the final sampled dataframe."""
    return sample_village(df.copy(), village_counts, male_prop, female_prop, youth_prop, threshold) 