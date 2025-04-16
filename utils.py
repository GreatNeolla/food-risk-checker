# utils.py

def get_product_info(barcode):
    # Real logic will connect to DB or cleaned data
    return {
        'barcode': barcode,
        'product_name': 'Sample Cereal',
        'ingredients': ['sugar', 'peanut oil', 'wheat'],
        'risk_score': 8
    }
