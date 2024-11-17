import streamlit as st

st.title('Importer')

# Create a dropdown menu
importer = st.selectbox('Select an importer', ['Amazon', 'eBay', 'PayPal'])

# Create a file picker
file = st.file_uploader('Upload a file', type=['csv'], accept_multiple_files=True)

if file:
    pass