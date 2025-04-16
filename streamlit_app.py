import streamlit as st
from utils import get_product_info

st.title("📦 Food Risk Checker")

barcode = st.text_input("Enter Product Barcode:")

if barcode:
    st.write(f"Looking up barcode: {barcode}")
    product = get_product_info(barcode)
    st.json(product)
