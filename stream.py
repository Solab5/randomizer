import streamlit as st
from pathlib import Path

from common_functions.utils import read_file, prepare_data
from sampling.sampling_functions import *


def get_final_df(df, village_counts, male_prop=0.6, female_prop=0.2, youth_prop=0.2, threshold=100):
    df_sampled = sample_village(df.copy(), village_counts, male_prop, female_prop, youth_prop, threshold)
    return df_sampled


st.title("RTV AHS/BHS random sample generator")

 # Print a note ensuring required columns are included
columns_to_keep = [
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
    # 'Household_Head_Gender',
    'Spouse_Name',
    'Telephone_Contact',
    'hhid',
]
st.info(f"**Note:** Ensure your DATASET includes the following columns for successful processing: {',  '.join(columns_to_keep)}")


uploaded_file = st.file_uploader("Upload your data file (CSV or Excel)")

if uploaded_file is not None:
    # Get the filename and extension
    filename = uploaded_file.name
    file_extension = Path(filename).suffix.lower()

    if file_extension in ('.csv', '.xls', '.xlsx'):
        data = read_file(uploaded_file)
        df = prepare_data(data.copy())
        village_counts = df['village'].value_counts()

        # Print a note ensuring required columns are included
        columns_to_keep = [
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
            'HHHeadship',
            'Spouse_Name',
            'Telephone_Contact',
            'hhid',
        ]
        st.info(f"**Note:** Ensure your DataFrame includes the following columns for successful processing: {', '.join(columns_to_keep)}")

        # Optional: Allow configuration of sampling parameters
        # st.subheader("Sampling Parameters (Optional)")
        # st.info("Note that this proportion is only for villages with samples more than 100, those with less are already defaulted to 50%, 25% 25% ie Male Female and Youth respectively, Reach out to Analystics team in case these proportions change")
        # male_prop = st.slider("Male Proportion", min_value=0.0, max_value=1.0, step=0.05, value=0.6)
        # female_prop = st.slider("Female Proportion", min_value=0.0, max_value=1.0, step=0.05, value=0.2)
        # youth_prop = st.slider("Youth Proportion", min_value=0.0, max_value=1.0, step=0.05, value=0.2)
        
        FINAL = get_final_df(df.copy(), village_counts)

        st.write(f"Number of villages: {len(village_counts)}")
        st.dataframe(FINAL.head(10))  # Display a preview of the sampled data

        st.download_button(
            label="Download Sampled Data",
            data=FINAL.to_csv(index=False),
            file_name="sampled_data.csv",
            mime="text/csv"
        )
    else:
        st.error("Unsupported file format. Only CSV and Excel files are supported.")

st.info("**Instructions:**")
st.write("- Upload your data file in CSV or Excel format.")
st.write("- The app will automatically process and prepare the data.")
st.write("- Optionally, you can adjust the sampling proportions for males, females, and youth.")
st.write("- Click the 'Download Sampled Data' button to download the results.")