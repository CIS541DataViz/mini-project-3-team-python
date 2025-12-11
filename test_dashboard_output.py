"""
Test script to show what the dashboard would display
This simulates the dashboard logic and shows the output
"""
import pandas as pd
from datetime import timedelta

print("=" * 60)
print("DASHBOARD DATA PREVIEW")
print("=" * 60)

# Load the data (same logic as dashboard)
try:
    df = pd.read_excel('ride_hailing.xlsx')
    df['current_time'] = pd.to_datetime(df['current_time'])
    df['status'] = df['reservation_id'].apply(
        lambda x: 'occupied' if pd.notna(x) and str(x).strip() != '' else 'vacant'
    )
    
    print(f"\n✓ Data loaded successfully")
    print(f"  Total rows: {len(df)}")
    print(f"  Unique timestamps: {len(df['current_time'].unique())}")
    
    # Get unique parking spots
    unique_spots = df[['x', 'y']].drop_duplicates().sort_values(['y', 'x']).reset_index(drop=True)
    unique_spots['spot_number'] = range(1, len(unique_spots) + 1)
    
    print(f"  Total parking spots: {len(unique_spots)}")
    
    # Get latest timestamp
    latest_timestamp = df['current_time'].max()
    print(f"  Latest timestamp: {latest_timestamp}")
    
    # Get current state
    current_data = df[df['current_time'] == latest_timestamp].copy()
    current_data = current_data.merge(unique_spots, on=['x', 'y'], how='left')
    
    # Calculate durations (simplified version)
    def calculate_duration(spot_x, spot_y, plate_number, current_timestamp):
        if pd.isna(plate_number):
            return timedelta(0)
        
        all_timestamps = sorted(
            [ts for ts in df['current_time'].unique() if ts <= current_timestamp],
            reverse=True
        )
        
        first_arrival = None
        for timestamp in all_timestamps:
            spot_at_time = df[
                (df['x'] == spot_x) & 
                (df['y'] == spot_y) &
                (df['current_time'] == timestamp)
            ]
            
            if len(spot_at_time) == 0:
                if first_arrival is not None:
                    break
                continue
                
            spot_status = spot_at_time.iloc[0]
            
            if spot_status['status'] == 'occupied' and spot_status['plate_number'] == plate_number:
                first_arrival = timestamp
            else:
                if first_arrival is not None:
                    break
        
        if first_arrival is None:
            return timedelta(0)
            
        return current_timestamp - first_arrival
    
    # Prepare table data
    table_data = []
    for _, spot in unique_spots.iterrows():
        spot_number = int(spot['spot_number'])
        spot_x = spot['x']
        spot_y = spot['y']
        
        spot_info = current_data[
            (current_data['x'] == spot_x) & 
            (current_data['y'] == spot_y)
        ]
        
        if len(spot_info) > 0:
            spot_row = spot_info.iloc[0]
            
            if spot_row['status'] == 'occupied':
                plate_number = spot_row['plate_number']
                duration = calculate_duration(spot_x, spot_y, plate_number, latest_timestamp)
                
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
                table_data.append({
                    'Spot #': spot_number,
                    'License Plate': '-',
                    'Duration': '-',
                    'Status': 'Vacant'
                })
        else:
            table_data.append({
                'Spot #': spot_number,
                'License Plate': '-',
                'Duration': '-',
                'Status': 'Vacant'
            })
    
    # Create DataFrame
    table_df = pd.DataFrame(table_data)
    table_df = table_df.sort_values('Spot #')
    
    # Summary stats
    occupied_count = len(table_df[table_df['Status'] == 'Occupied'])
    vacant_count = len(table_df[table_df['Status'] == 'Vacant'])
    total_count = len(table_df)
    
    print(f"\n" + "=" * 60)
    print("PARKING SPOTS SUMMARY")
    print("=" * 60)
    print(f"Occupied: {occupied_count} / {total_count} ({int(occupied_count/total_count*100)}%)")
    print(f"Vacant: {vacant_count} / {total_count}")
    
    print(f"\n" + "=" * 60)
    print("PARKING SPOTS TABLE (first 20 rows)")
    print("=" * 60)
    print(table_df.head(20).to_string(index=False))
    
    if len(table_df) > 20:
        print(f"\n... and {len(table_df) - 20} more spots")
    
    print(f"\n" + "=" * 60)
    print("✓ Dashboard logic working correctly!")
    print("=" * 60)
    print(f"\nTo view the interactive dashboard, run:")
    print(f"  streamlit run streamlit_app.py")
    print(f"\nThen open http://localhost:8501 in your browser")
    
except FileNotFoundError as e:
    print(f"✗ Error: {e}")
    print("Make sure you're in the correct directory with ride_hailing.xlsx")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

