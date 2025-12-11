import streamlit as st
import os

st.title("Mini Project 3 – Parking Visualization")
st.write("If you can see this, the Streamlit app is running 🎉")

try:
    import visualize_parking
    if hasattr(visualize_parking, "main"):
        # Only generate if GIF doesn't exist yet
        if not os.path.exists('parking_animation.gif'):
            st.write("Generating animation...")
            visualize_parking.main()
        st.image("parking_animation.gif")
    else:
        st.write("Found visualize_parking.py but no main() function.")
except Exception as e:
    st.error(f"Error importing or running visualize_parking: {e}")
