from flask import Flask, jsonify, request, render_template


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


# Mock product route
@app.route('/product/<barcode>', methods=['GET'])
def get_product(barcode):
    # Mock data for now (you’ll connect real logic later)
    mock_data = {
        'barcode': barcode,
        'product_name': 'Sample Cereal',
        'ingredients': ['sugar', 'peanut oil', 'wheat'],
        'risk_score': 8
    }
    return jsonify(mock_data)

if __name__ == '__main__':
    app.run(debug=True)

