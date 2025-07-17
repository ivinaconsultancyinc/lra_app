# VAT rates by country
VAT_RATES = {
    'US': 0.07,
    'UK': 0.20,
    'DE': 0.19,
    'FR': 0.20,
    'IN': 0.18,
    'CA': 0.05
}

# Tax calculation function
def calculate_tax(country_code, amount):
    rate = VAT_RATES.get(country_code.upper(), 0)
    return round(amount * rate, 2)

# Flask route to calculate tax
@app.route('/calculate_tax', methods=['GET'])
def tax_calculation():
    country = request.args.get('country')
    amount = request.args.get('amount', type=float)
    if not country or amount is None:
        return jsonify({'error': 'Missing country or amount'}), 400
    tax = calculate_tax(country, amount)
    return jsonify({
        'country': country.upper(),
        'amount': amount,
        'tax': tax,
        'total': round(amount + tax, 2)
    })
