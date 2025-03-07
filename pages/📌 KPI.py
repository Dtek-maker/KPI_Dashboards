import streamlit as st
import pandas as pd
import pyodbc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from DB_Conn import db_conn
import warnings

# Suppress the warning
warnings.simplefilter("ignore", category=UserWarning)

# Set up the page configuration
st.set_page_config(page_title="Historical Trend", page_icon=":trend", layout="wide")

# Custom CSS for the app (if needed)
with open('style.css') as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
# Connect to the database
conn = db_conn()

# Define a function to fetch data from the database based on Date and Hour
def fetch_data(startdate, enddate, hour, tag_index_list):
    query = f"""
        WITH newtbl_mdrRep1 AS (
            SELECT 
                Date, 
                DateAndTime, 
                Hour,       
                TagIndex, 
                Round(Val, 2) as Val,
                ROW_NUMBER() OVER (PARTITION BY Date, TagIndex ORDER BY DateAndTime DESC) AS rn
            FROM MDR.dbo.FloatTable 
            WHERE Date BETWEEN '{startdate}' AND '{enddate}'  
              AND Hour={hour}
              AND TagIndex IN ({','.join(map(str, tag_index_list))})
        )
        SELECT Date, DateAndTime, TagIndex, Val
        FROM newtbl_mdrRep1
        WHERE rn = 1;
    """
    # Read the query result into a DataFrame
    df = pd.read_sql(query, conn)
    
    # Close the database connection
    conn.close()
    
    return df

# TagIndex to Name mapping (for visualization purpose)
tag_index_mapping = {
    0:'Set V', 1:'Work V', 2:'Avg. V', 3:'Noise', 4:'ALF. Q', 5:'AE. Frq', 6:'ALO. Q', 7:'Act. Tap', 8:'Ex. ALF3', 9:'Bath. T', 10:'Bath. L', 11:'AL. L', 12:'Fe', 13:'Si', 14:'AE. Max V'
}

# Reverse mapping for the backend (for the query)
reverse_tag_index_mapping = {v:k for k, v in tag_index_mapping.items()}

# Get the current date
current_date = datetime.today()

# Calculate the start date as 15 days before the current date
start_date_default = current_date - timedelta(days=15)

# Streamlit UI elements to input date range
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input('Start Date', start_date_default)
with col2:
    end_date = st.date_input('End Date', current_date)

# TagIndex list (all parameters) to fetch all parameters by default
tag_index_list = list(reverse_tag_index_mapping.values())
hour = 6  # Hour can be a fixed value or you can allow the user to select it.

# Fetch the data based on the input parameters
trend_data = fetch_data(start_date, end_date, hour, tag_index_list)

# Check if the data is empty
if not trend_data.empty:
    # Convert DateAndTime to datetime
    trend_data['DateAndTime'] = pd.to_datetime(trend_data['DateAndTime'], errors='coerce')
    
    # Convert Val to numeric
    trend_data['Val'] = pd.to_numeric(trend_data['Val'], errors='coerce')
    
    # Check for missing values after conversion
    trend_data.dropna(subset=['DateAndTime', 'Val'], inplace=True)
    
    # Ensure that data is sorted by DateAndTime
    trend_data.sort_values(by='DateAndTime', inplace=True)
    
    # Map TagIndex back to names for visualization purposes
    trend_data['Parameter'] = trend_data['TagIndex'].map(tag_index_mapping)

    # Plotting each parameter separately
    for parameter in tag_index_mapping.values():
        # Filter the data for the specific parameter
        param_data = trend_data[trend_data['Parameter'] == parameter]
        
        # Calculate min and max for the y-axis based on the data
        y_min = param_data['Val'].min()
        y_max = param_data['Val'].max()
        
        # Add some padding for the y-axis range to make the plot more readable
        y_padding = (y_max - y_min)
        y_range = [y_min - y_padding, y_max + y_padding]

        # Create the matplotlib plot
        fig, ax = plt.subplots(figsize=(10, 2))
        
        ax.plot(param_data['DateAndTime'], param_data['Val'], marker='o', linestyle='-', color='b', label=parameter)
         # Annotate each data point with its value
        for i, row in param_data.iterrows():
            ax.annotate(f'{row["Val"]}', 
                        (row['DateAndTime'], row['Val']),
                        textcoords="offset points", 
                        xytext=(0, 5), 
                        ha='center', fontsize=9, color='black')
        
        # Add labels
        ax.set_title(f"{parameter}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        
        # Formatting the x-axis
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d'))
        ax.xaxis.set_minor_locator(mdates.DayLocator())
        plt.xticks(rotation=45)

        # Set y-axis range with padding
        ax.set_ylim(y_range)

        # Add gridlines
        ax.grid(True)

        # Display the plot in Streamlit
        st.pyplot(fig)
else:
    st.write("No data found for the selected filters.")
