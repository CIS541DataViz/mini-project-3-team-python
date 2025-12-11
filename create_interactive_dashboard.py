"""
Create an interactive HTML dashboard with animated GIF and live-updating table
"""
import pandas as pd
from datetime import timedelta
import json

def load_data():
    """Load and process parking data"""
    df = pd.read_excel('ride_hailing.xlsx')
    df['current_time'] = pd.to_datetime(df['current_time'])
    df['status'] = df['reservation_id'].apply(
        lambda x: 'occupied' if pd.notna(x) and str(x).strip() != '' else 'vacant'
    )
    return df

def calculate_duration(df, spot_x, spot_y, plate_number, current_timestamp):
    """Calculate how long a plate has been continuously in a spot"""
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

def create_interactive_dashboard():
    """Create interactive HTML dashboard"""
    print("Loading data...")
    df = load_data()
    
    # Get unique parking spots
    unique_spots = df[['x', 'y']].drop_duplicates().sort_values(['y', 'x']).reset_index(drop=True)
    unique_spots['spot_number'] = range(1, len(unique_spots) + 1)
    
    # Get all timestamps
    all_timestamps = sorted(df['current_time'].unique())
    
    print(f"Processing {len(unique_spots)} parking spots across {len(all_timestamps)} timestamps...")
    
    # Create data for each timestamp
    timestamp_data = {}
    
    for timestamp in all_timestamps:
        current_data = df[df['current_time'] == timestamp].copy()
        current_data = current_data.merge(unique_spots, on=['x', 'y'], how='left')
        
        spots_data = []
        for _, spot in unique_spots.iterrows():
            spot_number = int(spot['spot_number'])
            spot_x = spot['x']
            spot_y = spot['y']
            
            spot_info = current_data[
                (current_data['x'] == spot_x) & 
                (current_data['y'] == spot_y)
            ]
            
            spot_data = {
                'spot_number': spot_number,
                'status': 'vacant',
                'license_plate': None,
                'duration': '00:00:00'
            }
            
            if len(spot_info) > 0:
                spot_row = spot_info.iloc[0]
                
                if spot_row['status'] == 'occupied':
                    plate_number = spot_row['plate_number']
                    duration = calculate_duration(df, spot_x, spot_y, plate_number, timestamp)
                    
                    total_seconds = int(duration.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    
                    spot_data = {
                        'spot_number': spot_number,
                        'status': 'occupied',
                        'license_plate': str(plate_number),
                        'duration': duration_str
                    }
            
            spots_data.append(spot_data)
        
        timestamp_data[timestamp.isoformat()] = spots_data
    
    # Get latest timestamp data for initial display
    latest_timestamp = all_timestamps[-1]
    latest_data = timestamp_data[latest_timestamp.isoformat()]
    
    # Calculate summary stats for latest
    occupied_count = sum(1 for s in latest_data if s['status'] == 'occupied')
    total_count = len(latest_data)
    
    # Create sorted list of timestamp ISO strings for synchronization
    sorted_timestamps = [ts.isoformat() for ts in all_timestamps]
    
    print(f"Creating interactive HTML dashboard...")
    
    # Create HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parking Dashboard - Interactive</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
        }}
        
        .dashboard-container {{
            max-width: 1600px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
        }}
        
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 20px;
            font-size: 28px;
        }}
        
        .dashboard-content {{
            display: flex;
            gap: 20px;
            align-items: flex-start;
        }}
        
        .left-panel {{
            flex: 2;
        }}
        
        .right-panel {{
            flex: 1;
            background-color: #fafafa;
            border-radius: 8px;
            padding: 15px;
        }}
        
        .gif-container {{
            text-align: center;
            background-color: #fff;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .gif-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 5px;
        }}
        
        .table-container {{
            max-height: 700px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: white;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        
        thead {{
            position: sticky;
            top: 0;
            background-color: #4a86e8;
            color: white;
            z-index: 10;
        }}
        
        th {{
            padding: 12px 8px;
            text-align: left;
            font-weight: bold;
            border-bottom: 2px solid #ddd;
        }}
        
        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #eee;
        }}
        
        tbody tr:hover {{
            background-color: #f5f5f5;
        }}
        
        .spot-number {{
            font-weight: bold;
            padding: 5px 10px;
            border-radius: 4px;
            display: inline-block;
        }}
        
        .spot-number.occupied {{
            background-color: #ffcccc;
            color: #cc0000;
        }}
        
        .spot-number.vacant {{
            background-color: #ccffcc;
            color: #006600;
        }}
        
        .license-plate {{
            font-family: 'Courier New', monospace;
            font-weight: bold;
        }}
        
        .status-badge {{
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            display: inline-block;
        }}
        
        .status-badge.occupied {{
            background-color: #ffcccc;
            color: #cc0000;
        }}
        
        .status-badge.vacant {{
            background-color: #ccffcc;
            color: #006600;
        }}
        
        .summary-stats {{
            margin-bottom: 15px;
            padding: 15px;
            background-color: #e3f2fd;
            border-radius: 5px;
        }}
        
        .summary-stats h3 {{
            margin-bottom: 10px;
            color: #1976d2;
        }}
        
        .stat-item {{
            margin: 5px 0;
            font-size: 14px;
        }}
        
        .stat-value {{
            font-weight: bold;
            font-size: 18px;
            color: #1976d2;
        }}
        
        .timestamp {{
            text-align: center;
            margin-top: 10px;
            color: #666;
            font-size: 12px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <h1>Parking Dashboard - Mini Project 3</h1>
        
        <div class="dashboard-content">
            <div class="left-panel">
                <div class="gif-container">
                    <img src="parking_animation.gif" alt="Parking Animation" id="parkingGif">
                    <div class="timestamp" id="timestamp">Time: {all_timestamps[0].strftime('%B %d, %Y at %I:%M %p')}</div>
                </div>
            </div>
            
            <div class="right-panel">
                <div class="summary-stats">
                    <h3>Parking Status Summary</h3>
                    <div class="stat-item">Total Spots: <span class="stat-value">{total_count}</span></div>
                    <div class="stat-item">Occupied: <span class="stat-value" id="occupiedCount">{occupied_count}</span></div>
                    <div class="stat-item">Vacant: <span class="stat-value" id="vacantCount">{total_count - occupied_count}</span></div>
                    <div class="stat-item">Occupancy Rate: <span class="stat-value" id="occupancyRate">{int(occupied_count/total_count*100)}%</span></div>
                </div>
                
                <h3 style="margin-bottom: 10px;">Parking Spots Table</h3>
                <div class="table-container">
                    <table id="spotsTable">
                        <thead>
                            <tr>
                                <th>Spot #</th>
                                <th>License Plate</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="spotsTableBody">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Parking data for all timestamps
        const timestampData = {json.dumps(timestamp_data, indent=8)};
        
        // Sorted list of all timestamps (matches GIF frame order)
        const sortedTimestamps = {json.dumps(sorted_timestamps, indent=8)};
        
        // GIF frame duration in milliseconds (4 seconds per frame)
        const FRAME_DURATION = 4000;
        
        // Current timestamp index (starts at 0)
        let currentTimestampIndex = 0;
        
        // Function to update table with data for a specific timestamp
        function updateTable(timestamp) {{
            const data = timestampData[timestamp];
            if (!data) return;
            
            const tbody = document.getElementById('spotsTableBody');
            tbody.innerHTML = '';
            
            let occupiedCount = 0;
            let vacantCount = 0;
            
            data.forEach(spot => {{
                const row = document.createElement('tr');
                
                // Spot number with color coding
                const spotNumberCell = document.createElement('td');
                const spotNumberSpan = document.createElement('span');
                spotNumberSpan.className = 'spot-number ' + spot.status;
                spotNumberSpan.textContent = spot.spot_number;
                spotNumberCell.appendChild(spotNumberSpan);
                
                // License plate
                const plateCell = document.createElement('td');
                if (spot.license_plate && spot.license_plate !== 'None') {{
                    const plateSpan = document.createElement('span');
                    plateSpan.className = 'license-plate';
                    plateSpan.textContent = spot.license_plate;
                    plateCell.appendChild(plateSpan);
                }} else {{
                    plateCell.textContent = '-';
                    plateCell.style.color = '#999';
                }}
                
                // Status badge
                const statusCell = document.createElement('td');
                const statusBadge = document.createElement('span');
                statusBadge.className = 'status-badge ' + spot.status;
                statusBadge.textContent = spot.status.charAt(0).toUpperCase() + spot.status.slice(1);
                statusCell.appendChild(statusBadge);
                
                row.appendChild(spotNumberCell);
                row.appendChild(plateCell);
                row.appendChild(statusCell);
                tbody.appendChild(row);
                
                if (spot.status === 'occupied') {{
                    occupiedCount++;
                }} else {{
                    vacantCount++;
                }}
            }});
            
            // Update summary stats
            const totalCount = data.length;
            document.getElementById('occupiedCount').textContent = occupiedCount;
            document.getElementById('vacantCount').textContent = vacantCount;
            document.getElementById('occupancyRate').textContent = Math.round((occupiedCount / totalCount) * 100) + '%';
            
            // Update timestamp
            const timestampDate = new Date(timestamp);
            const timestampStr = timestampDate.toLocaleDateString('en-US', {{ 
                month: 'long', 
                day: 'numeric', 
                year: 'numeric' 
            }}) + ' at ' + timestampDate.toLocaleTimeString('en-US', {{ 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: true 
            }});
            document.getElementById('timestamp').textContent = 'Time: ' + timestampStr;
        }}
        
        // Initialize table with first timestamp (matches GIF start)
        updateTable(sortedTimestamps[0]);
        
        // Synchronize table updates with GIF animation
        // Update table every 4 seconds to match GIF frame rate
        setInterval(() => {{
            // Move to next timestamp (loop back to start when reaching end)
            currentTimestampIndex = (currentTimestampIndex + 1) % sortedTimestamps.length;
            const currentTimestamp = sortedTimestamps[currentTimestampIndex];
            updateTable(currentTimestamp);
        }}, FRAME_DURATION);
        
        // Reset to first frame when GIF loops (GIF loop detection is tricky, so we'll sync manually)
        // The GIF loops, so we reset our index to match
        const gifElement = document.getElementById('parkingGif');
        if (gifElement) {{
            // Reset to first frame every GIF loop cycle (60 frames * 4 seconds = 240 seconds)
            const gifLoopDuration = sortedTimestamps.length * FRAME_DURATION;
            setInterval(() => {{
                currentTimestampIndex = 0;
                updateTable(sortedTimestamps[0]);
            }}, gifLoopDuration);
        }}
    </script>
</body>
</html>
"""
    
    # Save HTML file
    output_file = 'parking_dashboard.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✓ Interactive dashboard created: {output_file}")
    print(f"  - Opens the animated GIF")
    print(f"  - Shows live-updating table with color-coded spots")
    print(f"  - Red for occupied spots, green for vacant spots")
    print(f"  - License plates displayed when occupied")
    print(f"\nOpen {output_file} in your web browser to view the dashboard!")
    
    return output_file

if __name__ == "__main__":
    try:
        create_interactive_dashboard()
    except Exception as e:
        print(f"\n✗ Error creating dashboard: {e}")
        import traceback
        traceback.print_exc()

