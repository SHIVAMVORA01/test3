import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="PMO",
    layout="wide",
)

# Function to load the data
def load_data():
    excel_file_path = 'PBC_Test Project1.xlsm'  
    sheet_name = 'TP Import'
    df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
    return df

# Function to save the data
def save_data(df):
    excel_file_path = 'PBC_Test Project1.xlsm'  
    with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='TP Import')

# Function to send data to Targetprocess
def send_to_targetprocess(data_payload):
    webhook_url = 'https://tpdev.gad.local/svc/hooks/in/103989ec-2c86-4452-ab76-5236760299e4'
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(webhook_url, json=data_payload, verify='./Belden-Global-Root-CA.crt', headers=headers)
    return response

# Load and display data
original_df = load_data()

# Ensure 'Portfolio Epic' is the first column
columns = list(original_df.columns)
if 'Portfolio Epic' in columns:
    columns.insert(0, columns.pop(columns.index('Portfolio Epic')))
    original_df = original_df[columns]

# Create a container for the buttons
button_container = st.container()

# Place buttons in a row at the top-right corner
with button_container:
    col1, col2, col3 = st.columns([4, 1, 1])
    with col2:
        save_button = st.button("Save Changes")
    with col3:
        send_button = st.button("Send to Targetprocess")

# Display the editable DataFrame
edited_df = st.data_editor(original_df, num_rows="dynamic", use_container_width=True)

# Handle button clicks
if save_button:
    save_data(edited_df)
    st.success("Changes saved successfully!")

if send_button:
    # Identify the edited rows
    edited_rows = original_df.compare(edited_df)
    if not edited_rows.empty:
        edited_indices = edited_rows.index.unique()
        data_payload = edited_df.loc[edited_indices].to_dict(orient='records')
        with st.expander("View Data Sent"):
            st.info(data_payload)
        response = send_to_targetprocess(data_payload)
        if response.status_code == 200:
            st.success("Successfully sent data to Targetprocess.")
        else:
            st.error(f"Failed to send data to Targetprocess. Status code: {response.status_code}, Response: {response.text}")
    else:
        st.info("No changes detected to send.")
