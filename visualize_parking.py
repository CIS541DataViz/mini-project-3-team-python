import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import matplotlib.offsetbox as offsetbox
import imageio
import os
import numpy as np
from io import BytesIO

def main():
    # Load Data: Read the excel file into a pandas dataframe
    df = pd.read_excel('ride_hailing.xlsx')

    # Basic Processing
    # Create a new column called status
    # If reservation_id has any text or numbers, status should be 'occupied', otherwise 'vacant'
    df['status'] = df['reservation_id'].apply(
        lambda x: 'occupied' if pd.notna(x) and str(x).strip() != '' else 'vacant'
    )

    # Make sure current_time column is understood as a date and time
    df['current_time'] = pd.to_datetime(df['current_time'])

    # Load background image
    bg_image = Image.open('map.png')
    img_width, img_height = bg_image.size

    # Get unique timestamps sorted
    unique_timestamps = sorted(df['current_time'].unique())

    print(f"Creating animation with {len(unique_timestamps)} frames...")

    # Create function to draw a frame for a given timestamp
    def create_frame(timestamp):
        # Filter data for the specific timestamp
        plot_data = df[df['current_time'] == timestamp]
        
        # Generate scatterplot with larger figure size
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Set background image - display image as-is without flipping
        ax.imshow(bg_image, extent=[0, img_width, 0, img_height], 
                  aspect='equal', alpha=1.0, zorder=0)
        
        # Set axis limits to show the entire image
        ax.set_xlim(0, img_width)
        ax.set_ylim(0, img_height)
        
        # Plot vacant spots as gray dots
        vacant_data = plot_data[plot_data['status'] == 'vacant']
        if len(vacant_data) > 0:
            ax.scatter(
                vacant_data['x'],
                vacant_data['y'],
                c='gray',
                label='Vacant',
                alpha=0.8,
                s=100,
                zorder=2,
                edgecolors='black',
                linewidths=1.5
            )
        
        # Plot occupied spots using license plate images
        occupied_data = plot_data[plot_data['status'] == 'occupied']
        for idx, row in occupied_data.iterrows():
            plate_number = row['plate_number']
            x_coord = row['x']
            y_coord = row['y']
            
            # Load license plate image if it exists
            plate_path = f'plates/{plate_number}.png'
            if os.path.exists(plate_path):
                try:
                    plate_img = Image.open(plate_path)
                    # Resize the plate image to appropriate size
                    # Adjust the resize factor as needed to fit nicely on the map
                    plate_img.thumbnail((80, 40), Image.Resampling.LANCZOS)
                    
                    # Create offset box with the license plate image
                    imagebox = offsetbox.OffsetImage(plate_img, zoom=1.0)
                    ab = offsetbox.AnnotationBbox(imagebox, (x_coord, y_coord), 
                                                 frameon=False, pad=0)
                    ax.add_artist(ab)
                except Exception as e:
                    # If image can't be loaded, fall back to red dot
                    print(f"Warning: Could not load {plate_path}: {e}")
                    ax.scatter(x_coord, y_coord, c='red', s=100, zorder=2, 
                              edgecolors='darkred', linewidths=1.5)
            else:
                # If plate image doesn't exist, use red dot
                ax.scatter(x_coord, y_coord, c='red', s=100, zorder=2, 
                          edgecolors='darkred', linewidths=1.5)
        
        # Remove white background
        ax.set_facecolor('none')
        fig.patch.set_facecolor('none')
        
        # Hide x and y axis numbers and ticks
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # Remove grid lines
        ax.grid(False)
        
        # Add title showing date and time
        title_text = f'Parking Status - {timestamp.strftime("%B %d, %Y at %I:%M %p")}'
        ax.set_title(title_text, fontsize=18, fontweight='bold', pad=20, color='black')
        
        # Create a simple legend
        ax.legend(loc='upper right', fontsize=14, framealpha=0.9, edgecolor='black', 
                  title='Parking Status', title_fontsize=14)
        
        plt.tight_layout()
        
        # Convert figure to image array for GIF creation
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', 
                    facecolor='white', transparent=False)
        buf.seek(0)
        image_array = np.array(Image.open(buf))
        buf.close()
        
        plt.close(fig)
        
        return image_array

    # Create frames for all timestamps
    frames = []
    for i, timestamp in enumerate(unique_timestamps):
        print(f"Creating frame {i+1}/{len(unique_timestamps)}: {timestamp}")
        frame = create_frame(timestamp)
        frames.append(frame)

    # Create animated GIF
    # Each frame displays for 2 seconds (duration = 2.0)
    print("Creating animated GIF...")
    imageio.mimsave('parking_animation.gif', frames, duration=2.0, loop=0)

    print(f"Animation saved as 'parking_animation.gif'")
    print(f"Total frames: {len(frames)}")
    print(f"Duration per frame: 2 seconds")

if __name__ == "__main__":
    main()
