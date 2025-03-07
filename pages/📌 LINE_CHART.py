import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from DB_Conn import db_conn  # Assuming your db_conn function is correct

# Set up the title and header
st.header('Energy over Time')

# Fetch data from SQL
conn = db_conn()
cursor = conn.cursor()

# SQL query to fetch data from your table
query = """
    SELECT [DateAndTime], [TagIndex], [Val]
    FROM [MDR].[dbo].[FloatTable]
    WHERE [DateAndTime] BETWEEN ? AND ?
"""
# Set the default start and end date as yesterday and today
start_date = datetime.now() - timedelta(days=1)
end_date = datetime.now()

# Allow the user to select a start and end date
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input('Start Date', start_date)
with col2:
    end_date = st.date_input('End Date', end_date)

# Convert the start and end dates to datetime objects
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

# Execute SQL query with date parameters using '?' as placeholders
cursor.execute(query, (start_date, end_date))
data = cursor.fetchall()

# Debugging: Print the raw fetched data
st.write("Raw Fetched Data:", data)  # Add this line to inspect the fetched data

# Convert fetched rows to a DataFrame
data = []
for row in data:
    datetime_val, tag_index, val = row
    st.write(f"Processing row: {row}")  # Debugging: Show each row before processing
    
    # Check the data types of the fields
    st.write(f"DateTime: {datetime_val}, TagIndex: {tag_index}, Val: {val}")  # Debugging: Show data types

    try:
        val = round(float(val), 2)
    except ValueError as e:
        st.write(f"ValueError for row: {row}, Error: {e}")  # Debugging: If conversion fails, print error
        val = np.nan  # If conversion fails, set to NaN (could also handle differently)
    
    # Append the processed data to the list
    data.append([datetime_val, tag_index, val])



# Create DataFrame from the fetched data
df = pd.DataFrame(data, columns=['DateAndTime', 'TagIndex', 'Val'])

# Debugging: Check the DataFrame structure
st.write("DataFrame after processing:", df.head())  # Display DataFrame for inspection

# Ensure 'DateAndTime' is in datetime format
df['DateAndTime'] = pd.to_datetime(df['DateAndTime'])

# Check if DataFrame is empty after processing
if df.empty:
    st.warning("No data available after processing.")
else:
    # Select box for TagIndex selection
    selected_tag = st.selectbox('Select TagIndex', df['TagIndex'].unique())

    # Debugging: Print unique TagIndexes
    st.write("Available TagIndexes:", df['TagIndex'].unique())  # Add this line to inspect TagIndexes

    # Filter the data based on selected TagIndex
    filtered_df = df[df['TagIndex'] == selected_tag]

    # Further filter by selected date range
    filtered_df = filtered_df[(filtered_df['DateAndTime'] >= start_date) & (filtered_df['DateAndTime'] <= end_date)]

    # Debugging: Check the filtered data
    st.write("Filtered Data:", filtered_df)  # Add this line to inspect filtered data

    # Check if there is any data after filtering
    if filtered_df.empty:
        st.warning(f"No data available for TagIndex {selected_tag} in the selected date range ({start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}).")
    else:
        # Create an interactive line chart using Plotly
        fig = px.line(filtered_df, x='DateAndTime', y='Val', title=f'TagIndex {selected_tag} - Energy Over Time ({start_date.strftime("%d-%m-%Y")} to {end_date.strftime("%d-%m-%Y")})')

        # Ensure the x-axis treats the DateAndTime as a date-time type and display the correct range
        fig.update_layout(
            xaxis=dict(
                tickformat="%d-%m-%Y %H:%M:%S",  # Format to show date and time
                type="date",  # Ensure the x-axis treats the DateAndTime as a date type
                range=[start_date, end_date]  # Ensure the range matches the selected date range
            )
        )

        # Display the Plotly chart
        st.plotly_chart(fig)
