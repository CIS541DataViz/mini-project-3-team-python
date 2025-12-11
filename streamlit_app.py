
import streamlit as st

st.title("Mini Project 3 – Parking Visualization")

st.write("If you can see this, the Streamlit app is running 🎉")

# ---- Example: run your existing code if you have a function ----
try:
    import visualize_parking

    if hasattr(visualize_parking, "main"):
        st.write("Running visualize_parking.main()...")
        visualize_parking.main()
    else:
        st.write("Found visualize_parking.py but no main() function.")
except Exception as e:
    st.error(f"Error importing or running visualize_parking: {e}")
