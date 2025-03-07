import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from DB_Conn import db_conn
from datetime import datetime, timedelta

# Set up the page configuration
st.set_page_config(page_title="Report", page_icon=":table", layout="wide")

st.subheader("Technical Parameters Report")

# Logo
st.sidebar.image("data/C_logo.jpeg")

# Read data from MS SQL Server
conn = db_conn()
cursor = conn.cursor()

# Example to fetch data from MS SQL server
cursor.execute("Select DateAndTime, TagIndex, Val from [MDR].[dbo].[FloatTable] order by DateAndtime Desc")

# Fetch all rows
rows = cursor.fetchall()

# Convert fetched rows to a DataFrame
data = []
for row in rows:
    datetime_val, tag_index, val = row
    try:
        val = round(float(val),2)
    except ValueError:
        val = np.nan  # If conversion fails, set to NaN (could also handle differently)
    
    data.append([datetime_val, tag_index, val])

# Convert the data to a pandas DataFrame
df = pd.DataFrame(data, columns=["DateAndTime", "TagIndex", "Val"])

# Optional: Format DateAndTime for display (if needed)
df["DateAndTime"] = pd.to_datetime(df["DateAndTime"])

# Date and Time filters (default to current datetime - 1 day for start, current datetime for end)
current_time = datetime.now()
start_datetime_default = current_time - timedelta(days=1)
end_datetime_default = current_time

# Create columns for displaying widgets side  by side
col1, col2,col3,col4 = st.columns([1, 1,1,1]) # You can adjust the width ratio

#Create date and time input widgets inside the column
with col1:
    start_date = st.date_input("Satrt Date", value=start_datetime_default.date())
with col2:
    start_time = st.time_input("Start Time", value=start_datetime_default.time())    
with col3:
    end_date = st.date_input("End Date", value=end_datetime_default.date())
with col4:
    end_time = st.time_input("End Time", value=end_datetime_default.time())   


# Combine the selected date and time to form datetime objects
start_datetime = datetime.combine(start_date, start_time)
end_datetime = datetime.combine(end_date, end_time)

# Filter the DataFrame based on the selected date range
filtered_df = df[(df["DateAndTime"] >= start_datetime) & (df["DateAndTime"] <= end_datetime)]

# Use Plotly to create a table with customizable column width and properties
table = go.Figure(data=[go.Table(
    header=dict(values=["DateAndTime", "TagIndex", "Val"],
                fill_color='paleturquoise',
                align='center'),
    cells=dict(values=[filtered_df['DateAndTime'].dt.strftime('%Y-%m-%d %H:%M:%S'), filtered_df['TagIndex'], filtered_df['Val']],
               fill_color='lavender',
               align='center',
               height=25,  # Set row height
               font=dict(size=12),
               line_color='darkslategray'),
)])

# Customizing the column width
table.update_layout(
    autosize=True,  # Automatically adjust the table size
    margin=dict(t=25, b=10),  # Margins around the table
    width=1000,  # Set width for the entire table
    height=550,  # Set height for the table (you can adjust this value as needed)
    
)

# Customizing individual column widths
table.update_traces(
    columnwidth=[30, 20, 20]  # Define specific column widths (values are in relative percentage, e.g., 30% for DateAndTime)
)

# Display the Plotly table
st.plotly_chart(table)
# Add a CSV download button
# Convert the filtered dataframe to CSV format
csv = filtered_df.to_csv(index=False)

# Create a download button for the CSV file
st.download_button(
    label="Download Filtered CSV",
    data=csv,
    file_name="filtered_technical_parameters.csv",
    mime="text/csv"
)

