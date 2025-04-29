#To run, in terminal: streamlit run streamlit_app.py




import streamlit as st
from utils import get_product_info

st.set_page_config(page_title="Food Risk Checker", page_icon="🍽️")
st.title("🍽️ Food Risk Checker")
st.subheader("Scan product barcodes and check risk levels based on ingredients.")

barcode = st.text_input("🔍 Enter Product Barcode")

if barcode:
    with st.spinner("Looking up product..."):
        product = get_product_info(barcode)
        if product:
            st.success("Product found!")
            st.markdown(f"**Product Name:** {product['product_name']}")
            st.markdown(f"**Ingredients:** {', '.join(product['ingredients'])}")
            st.markdown(f"**Risk Score:** `{product['risk_score']}/10`")

            # Optional: visualize risk score
            st.progress(min(product['risk_score'] / 10, 1.0))
        else:
            st.error("❌ Product not found.")
else:
    st.info("Enter a barcode above to begin.")

