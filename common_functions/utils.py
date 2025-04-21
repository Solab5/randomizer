## This file contains the common files used in the notebooks
import pandas as pd
from pathlib import Path

def gender_age_processing(df: pd.DataFrame):
    """
    Takes a dataframe and returns a preprocessed dataframe
    """
    # Create a new variable Gender
    df['Gender'] = df['Household_Head_Gender']
    
    if 'Gender' in df.columns and 'Household_Head_Age' in df.columns:
        df['Household_Head_Gender'] = df.apply(lambda row: 
            'Youth Headed' if row['Household_Head_Age'] <= 30 
            else (str(row['Household_Head_Gender']) + ' Headed') if not row['Household_Head_Gender'].endswith(' Headed') 
            else row['Household_Head_Gender'], axis=1)
        
        # Drop the unnecessary columns
        # df.drop(columns=['Gender'], inplace=True)
        df['HHHeadship'] = df['Household_Head_Gender']
    return df


def read_file(file_input):
    """
    Takes either a Streamlit uploaded_file object or a file path and returns a dataframe
    """
    # Check if input is a string (file path) or has a name attribute (Streamlit file object)
    if isinstance(file_input, str):
        file_extension = Path(file_input).suffix.lower()
        file_path = file_input
    else:
        # Handle Streamlit file object
        file_extension = Path(file_input.name).suffix.lower()
        file_path = file_input

    if file_extension in ('.csv', '.xls', '.xlsx'):
        if file_extension == '.csv':
            return pd.read_csv(file_path)
        elif file_extension in ('.xls', '.xlsx'):
            return pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Only CSV and Excel files are supported.")
    else:
        raise ValueError("Unsupported file format. Only CSV and Excel files are supported.")
        
def prepare_data(df):
    """
    Takes a dataframe and returns only the required columns
    """
    columns = [
        'district',
        'subcounty',
        'parish_t',
        'cluster_t',
        'village',
        'lat_x',
        'long_y',
        'hhh_full_name',
        'Household_Head_Age',
        'Household_Head_Contact',
        'Gender',
        'HHHeadship',
        'Spouse_Name',
        'Telephone_Contact',
        'hhid',
     ]
    # df = df[columns]
    df_prepared = gender_age_processing(df.copy())
    df_prepared = df_prepared[columns]
    return df_prepared