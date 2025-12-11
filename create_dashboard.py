"""
Create a static dashboard visualization showing parking status
This generates a single image/PDF file with the dashboard
"""
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
import numpy as np
from datetime import timedelta
import matplotlib.gridspec as gridspec
from matplotlib.table import Table
import matplotlib.offsetbox as offsetbox
import os

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

def create_dashboard():
    """Create the dashboard visualization"""
    print("Loading data...")
    df = load_data()
    
    # Get unique parking spots
    unique_spots = df[['x', 'y']].drop_duplicates().sort_values(['y', 'x']).reset_index(drop=True)
    unique_spots['spot_number'] = range(1, len(unique_spots) + 1)
    
    # Get latest timestamp
    latest_timestamp = df['current_time'].max()
    current_data = df[df['current_time'] == latest_timestamp].copy()
    current_data = current_data.merge(unique_spots, on=['x', 'y'], how='left')
    
    print(f"Processing {len(unique_spots)} parking spots...")
    
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
                duration = calculate_duration(df, spot_x, spot_y, plate_number, latest_timestamp)
                
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
    
    table_df = pd.DataFrame(table_data)
    table_df = table_df.sort_values('Spot #')
    
    # Calculate summary stats
    occupied_count = len(table_df[table_df['Status'] == 'Occupied'])
    vacant_count = len(table_df[table_df['Status'] == 'Vacant'])
    total_count = len(table_df)
    
    print(f"Occupied: {occupied_count}/{total_count} ({int(occupied_count/total_count*100)}%)")
    print("Creating dashboard visualization...")
    
    # Create figure with custom layout
    fig = plt.figure(figsize=(20, 12))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3,
                          height_ratios=[1, 1], width_ratios=[2, 1])
    
    # Main title
    fig.suptitle('Parking Dashboard - Mini Project 3', fontsize=24, fontweight='bold', y=0.98)
    
    # Left side: Parking animation (latest frame)
    ax1 = fig.add_subplot(gs[:, 0])
    
    # Load and display the parking map
    try:
        bg_image = Image.open('map.png')
        img_width, img_height = bg_image.size
        ax1.imshow(bg_image, extent=[0, img_width, 0, img_height], aspect='equal', alpha=1.0, zorder=0)
        
        # Plot current state
        plot_data = current_data
        
        # Plot vacant spots
        vacant_data = plot_data[plot_data['status'] == 'vacant']
        if len(vacant_data) > 0:
            ax1.scatter(vacant_data['x'], vacant_data['y'], c='gray', 
                       label='Vacant', alpha=0.8, s=100, zorder=2, 
                       edgecolors='black', linewidths=1.5)
        
        # Plot occupied spots using license plate images (like original visualization)
        occupied_data = plot_data[plot_data['status'] == 'occupied']
        has_occupied = len(occupied_data) > 0
        used_images = False
        used_dots = False
        
        if has_occupied:
            for idx, row in occupied_data.iterrows():
                plate_number = row['plate_number']
                x_coord = row['x']
                y_coord = row['y']
                
                # Try to load license plate image
                plate_path = f'plates/{plate_number}.png'
                if os.path.exists(plate_path):
                    try:
                        plate_img = Image.open(plate_path)
                        plate_img.thumbnail((80, 40), Image.Resampling.LANCZOS)
                        
                        imagebox = offsetbox.OffsetImage(plate_img, zoom=1.0)
                        ab = offsetbox.AnnotationBbox(imagebox, (x_coord, y_coord), 
                                                     frameon=False, pad=0)
                        ax1.add_artist(ab)
                        used_images = True
                    except Exception as e:
                        # Fallback to red dot if image can't be loaded
                        ax1.scatter(x_coord, y_coord, c='red', s=100, zorder=2, 
                                  edgecolors='darkred', linewidths=1.5)
                        used_dots = True
                else:
                    # Fallback to red dot if image doesn't exist
                    ax1.scatter(x_coord, y_coord, c='red', s=100, zorder=2, 
                              edgecolors='darkred', linewidths=1.5)
                    used_dots = True
        
        # Add legend entry for occupied
        if has_occupied and used_dots:
            ax1.scatter([], [], c='red', s=100, label='Occupied', 
                       edgecolors='darkred', linewidths=1.5)
        
        ax1.set_xlim(0, img_width)
        ax1.set_ylim(0, img_height)
        ax1.set_title(f'Parking Status - {latest_timestamp.strftime("%B %d, %Y at %I:%M %p")}', 
                     fontsize=16, fontweight='bold', pad=15)
        ax1.legend(loc='upper right', fontsize=12, framealpha=0.9)
        ax1.set_xticks([])
        ax1.set_yticks([])
        ax1.set_facecolor('white')
    except Exception as e:
        ax1.text(0.5, 0.5, f'Error loading map: {e}', 
                ha='center', va='center', transform=ax1.transAxes)
        ax1.set_facecolor('lightgray')
    
    # Right side: Summary metrics
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis('off')
    
    # Summary text
    summary_text = f"""
    PARKING STATUS SUMMARY
    
    Total Spots: {total_count}
    Occupied: {occupied_count}
    Vacant: {vacant_count}
    
    Occupancy Rate: {int(occupied_count/total_count*100)}%
    
    Last Updated:
    {latest_timestamp.strftime("%B %d, %Y")}
    {latest_timestamp.strftime("%I:%M %p")}
    """
    
    ax2.text(0.1, 0.5, summary_text, fontsize=14, 
            verticalalignment='center', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    # Right side: Parking spots table
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.axis('off')
    ax3.set_title('Parking Spots Table', fontsize=16, fontweight='bold', pad=10)
    
    # Create table
    table_vals = []
    colors = []
    
    # Limit rows for display (show first 30 spots or all if less)
    display_df = table_df.head(30).copy()
    
    # Add header
    table_vals.append(['Spot #', 'License Plate', 'Duration', 'Status'])
    colors.append(['lightgray', 'lightgray', 'lightgray', 'lightgray'])
    
    for _, row in display_df.iterrows():
        spot_num = str(int(row['Spot #']))
        plate = str(row['License Plate'])
        duration = str(row['Duration'])
        status = row['Status']
        
        table_vals.append([spot_num, plate, duration, status])
        
        # Color code status
        if status == 'Occupied':
            colors.append(['white', 'white', 'white', '#ffcccc'])  # Red for occupied
        else:
            colors.append(['white', 'white', 'white', '#ccffcc'])  # Green for vacant
    
    # Create table
    table = ax3.table(cellText=table_vals, cellLoc='left', loc='center',
                     colWidths=[0.15, 0.35, 0.25, 0.25],
                     cellColours=colors)
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    
    # Style header
    for i in range(4):
        cell = table[(0, i)]
        cell.set_text_props(weight='bold', fontsize=10)
        cell.set_facecolor('#4a86e8')
        cell.set_text_props(color='white')
    
    # Add note if more spots exist
    if len(table_df) > 30:
        ax3.text(0.5, -0.05, f'Showing 30 of {len(table_df)} spots', 
                ha='center', transform=ax3.transAxes, fontsize=10, style='italic')
    
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    
    # Save dashboard
    output_file = 'parking_dashboard.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\n✓ Dashboard saved as: {output_file}")
    
    # Also save as PDF for better quality
    output_pdf = 'parking_dashboard.pdf'
    plt.savefig(output_pdf, bbox_inches='tight', facecolor='white')
    print(f"✓ Dashboard saved as: {output_pdf}")
    
    plt.close()
    
    return output_file, table_df

if __name__ == "__main__":
    try:
        output_file, table_df = create_dashboard()
        print(f"\n{'='*60}")
        print("Dashboard created successfully!")
        print(f"{'='*60}")
        print(f"\nView the dashboard by opening: {output_file}")
        print(f"\nTable preview (first 10 spots):")
        print(table_df.head(10).to_string(index=False))
    except Exception as e:
        print(f"\n✗ Error creating dashboard: {e}")
        import traceback
        traceback.print_exc()

