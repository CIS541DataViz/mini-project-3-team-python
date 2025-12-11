import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Parking Dashboard", layout="wide")

st.title("Mini Project 3 – Parking Visualization Dashboard")

# Load the data
@st.cache_data
def load_data():
    df = pd.read_excel('ride_hailing.xlsx')
    df['current_time'] = pd.to_datetime(df['current_time'])
    df['status'] = df['reservation_id'].apply(
        lambda x: 'occupied' if pd.notna(x) and str(x).strip() != '' else 'vacant'
    )
    return df

df = load_data()

# Get unique parking spots (by x, y coordinates) and assign spot numbers
unique_spots = df[['x', 'y']].drop_duplicates().sort_values(['y', 'x']).reset_index(drop=True)
unique_spots['spot_number'] = range(1, len(unique_spots) + 1)

# Get the latest timestamp
latest_timestamp = df['current_time'].max()

# Create two columns layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Parking Animation")
    try:
        # Display the animated GIF - Streamlit should handle animation automatically
        # If it's not animating, try refreshing the browser or clearing cache
        st.image("parking_animation.gif", use_container_width=True)
    except FileNotFoundError:
        st.error("parking_animation.gif not found. Please run visualize_parking.py first to generate it.")
    except Exception as e:
        st.error(f"Error loading GIF: {e}")
        st.info("Make sure parking_animation.gif exists in the current directory")

with col2:
    st.subheader("Parking Spots Status")
    
    # Debug info (can be removed later)
    with st.expander("Debug Info", expanded=False):
        st.write(f"Total unique spots: {len(unique_spots)}")
        st.write(f"Latest timestamp: {latest_timestamp}")
        st.write(f"Data shape: {df.shape}")
    
    # Add a search/filter option
    search_plate = st.text_input("Search by License Plate", key="search_plate", placeholder="Enter plate number...")
    
    # Get current state (latest timestamp)
    current_data = df[df['current_time'] == latest_timestamp].copy()
    
    # Merge with spot numbers
    current_data = current_data.merge(unique_spots, on=['x', 'y'], how='left')
    
    # Calculate parking durations for occupied spots
    def calculate_duration(spot_x, spot_y, plate_number, current_timestamp):
        """Calculate how long a plate has been continuously in a spot"""
        if pd.isna(plate_number):
            return timedelta(0)
        
        # Get all timestamps up to current, sorted in descending order
        all_timestamps = sorted(
            [ts for ts in df['current_time'].unique() if ts <= current_timestamp],
            reverse=True
        )
        
        # Work backwards from current timestamp to find when this continuous period started
        first_arrival = None
        
        for timestamp in all_timestamps:
            # Check if this plate is at this spot at this timestamp
            spot_at_time = df[
                (df['x'] == spot_x) & 
                (df['y'] == spot_y) &
                (df['current_time'] == timestamp)
            ]
            
            if len(spot_at_time) == 0:
                # No data for this timestamp at this spot, break continuity
                if first_arrival is not None:
                    break
                continue
                
            spot_status = spot_at_time.iloc[0]
            
            # Check if this plate is occupying the spot
            if spot_status['status'] == 'occupied' and spot_status['plate_number'] == plate_number:
                first_arrival = timestamp
            else:
                # Plate is not at this spot, we've found when the continuous period started
                if first_arrival is not None:
                    break
        
        if first_arrival is None:
            # Plate just arrived or not found in history
            return timedelta(0)
            
        duration = current_timestamp - first_arrival
        return duration
    
    # Prepare table data - include ALL spots
    table_data = []
    for _, spot in unique_spots.iterrows():
        spot_number = int(spot['spot_number'])
        spot_x = spot['x']
        spot_y = spot['y']
        
        # Find spot info at latest timestamp
        spot_info = current_data[
            (current_data['x'] == spot_x) & 
            (current_data['y'] == spot_y)
        ]
        
        if len(spot_info) > 0:
            spot_row = spot_info.iloc[0]
            
            if spot_row['status'] == 'occupied':
                plate_number = spot_row['plate_number']
                duration = calculate_duration(spot_x, spot_y, plate_number, latest_timestamp)
                
                # Format duration as HH:MM:SS
                total_seconds = int(duration.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                table_data.append({
                    'Spot #': spot_number,
                    'License Plate': plate_number,
                    'Duration': duration_str,
                    'Status': 'Occupied'
                })
            else:
                # Vacant spot
                table_data.append({
                    'Spot #': spot_number,
                    'License Plate': '-',
                    'Duration': '-',
                    'Status': 'Vacant'
                })
        else:
            # Spot exists but no data at latest timestamp - assume vacant
            table_data.append({
                'Spot #': spot_number,
                'License Plate': '-',
                'Duration': '-',
                'Status': 'Vacant'
            })
    
    # Create DataFrame for table
    if len(table_data) > 0:
        table_df = pd.DataFrame(table_data)
        if 'Spot #' in table_df.columns:
            table_df = table_df.sort_values('Spot #')
    else:
        # Fallback: create empty DataFrame with correct columns
        table_df = pd.DataFrame(columns=['Spot #', 'License Plate', 'Duration', 'Status'])
    
    # Calculate summary stats BEFORE filtering
    all_spots_df = table_df.copy() if len(table_df) > 0 else pd.DataFrame(columns=['Spot #', 'License Plate', 'Duration', 'Status'])
    if len(all_spots_df) > 0 and 'Status' in all_spots_df.columns:
        occupied_count_all = len(all_spots_df[all_spots_df['Status'] == 'Occupied'])
        total_count_all = len(all_spots_df)
        st.metric("Occupied Spots", f"{occupied_count_all} / {total_count_all}", 
                 delta=f"{int(occupied_count_all/total_count_all*100)}% occupancy" if total_count_all > 0 else "0%")
    
    # Filter by search if provided
    if len(table_df) > 0 and search_plate and search_plate.strip():
        search_term = search_plate.strip().upper()
        try:
            table_df = table_df[
                table_df['License Plate'].astype(str).str.upper().str.contains(search_term, na=False)
            ]
        except Exception as e:
            st.warning(f"Search error: {e}")
    
    # Display table with styling
    if len(table_df) == 0:
        if search_plate and search_plate.strip():
            st.info("No spots match your search criteria. Try a different search term.")
        else:
            st.warning("No parking spot data available. Please check your data file.")
    elif 'Spot #' in table_df.columns:
        # Create HTML table with colored status indicators
        html_table = """
        <style>
        .table-container {
            max-height: 550px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .parking-table {
            width: 100%;
            border-collapse: collapse;
            font-family: Arial, sans-serif;
            font-size: 13px;
        }
        .parking-table th {
            background-color: #f0f0f0;
            padding: 10px 8px;
            text-align: left;
            border-bottom: 2px solid #ddd;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .parking-table td {
            padding: 8px;
            border-bottom: 1px solid #eee;
        }
        .parking-table tr:hover {
            background-color: #f5f5f5;
        }
        .status-occupied {
            background-color: #ffcccc !important;
            color: #cc0000;
            font-weight: bold;
            text-align: center;
        }
        .status-vacant {
            background-color: #ccffcc !important;
            color: #006600;
            font-weight: bold;
            text-align: center;
        }
        </style>
        <div class="table-container">
        <table class="parking-table">
        <thead>
            <tr>
                <th>Spot #</th>
                <th>License Plate</th>
                <th>Duration</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
        """
        
        for _, row in table_df.iterrows():
            status_class = "status-occupied" if row['Status'] == 'Occupied' else "status-vacant"
            html_table += f"""
            <tr>
                <td>{int(row['Spot #'])}</td>
                <td>{row['License Plate']}</td>
                <td>{row['Duration']}</td>
                <td class="{status_class}">{row['Status']}</td>
            </tr>
            """
        
        html_table += """
        </tbody>
        </table>
        </div>
        """
        
        st.markdown(html_table, unsafe_allow_html=True)
        
        # Display timestamp
        st.caption(f"Last updated: {latest_timestamp.strftime('%B %d, %Y at %I:%M %p')}")
    else:
        st.info("No parking data available")
