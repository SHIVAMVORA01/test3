import streamlit as st
import pandas as pd
import sqlite3
import requests
from datetime import datetime

st.set_page_config(
    page_title="PMO",
    layout="wide",
)

# Function to load data from SQLite
def load_data():
    conn = sqlite3.connect('pmo_data.db')
    df = pd.read_sql_query("SELECT * FROM tp_import", conn)
    conn.close()
    return df

# Function to save data to SQLite
def save_data(df):
    conn = sqlite3.connect('pmo_data.db')
    df.to_sql('tp_import', conn, if_exists='replace', index=False)
    conn.close()

# Function to send data to Targetprocess
def send_to_targetprocess(data_payload):
    webhook_url = 'https://tpdev.gad.local/svc/hooks/in/103989ec-2c86-4452-ab76-5236760299e4'
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(webhook_url, json=data_payload, verify='Belden-Global-Root-CA.crt', headers=headers)
    return response

# Load initial data
original_df = load_data()

# Ensure 'Portfolio Epic' is the first column
columns = list(original_df.columns)
if 'Portfolio Epic ID' in columns:
    columns.insert(0, columns.pop(columns.index('Portfolio Epic ID')))
    original_df = original_df[columns]

# Display the last refresh time
if 'last_refresh_time' not in st.session_state:
    st.session_state.last_refresh_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Create a container for the buttons
button_container = st.container()

# Place buttons in a row at the top-right corner
with button_container:
    col1, col2, col3 = st.columns([4, 1, 2])
    with col2:
        refresh_button = st.button("Refresh Data")
    with col3:
        st.write(f"Last refreshed: {st.session_state.last_refresh_time}")

# Display the editable DataFrame
edited_df = st.data_editor(original_df, num_rows="dynamic", use_container_width=True)

# Handle refresh button click
if refresh_button:
    original_df = load_data()
    st.session_state.last_refresh_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Automatically detect and send updated rows
if not edited_df.equals(original_df):
    edited_rows = original_df.compare(edited_df)
    if not edited_rows.empty:
        edited_indices = edited_rows.index.unique()
        data_payload = edited_df.loc[edited_indices].to_dict(orient='records')
        
        changes = []
        for index in edited_indices:
            for column in edited_df.columns:
                if original_df.at[index, column] != edited_df.at[index, column]:
                    changes.append(
                        f"The value of column '{column}' changed from '{original_df.at[index, column]}' to '{edited_df.at[index, column]}'"
                    )
        
        with st.expander("View Data Sent"):
            for change in changes:
                st.write(change)
        
        response = send_to_targetprocess(data_payload)
        if response.status_code == 200:
            st.success("Successfully sent data to Targetprocess.")
        else:
            st.error(f"Failed to send data to Targetprocess. Status code: {response.status_code}, Response: {response.text}")

    # Save the edited data
    save_data(edited_df)
