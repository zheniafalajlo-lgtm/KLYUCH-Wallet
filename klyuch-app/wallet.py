from flask import Flask, render_template, request, jsonify, session
from eth_account import Account
import json, os
from blockchain import get_crypto_data, buy_kly_with_bnb, swap_kly_for_bnb, send_kly_tokens


app = Flask(__name__)
app.secret_key = "elite_klyuch_secret"
WALLET_FILE = "my_encrypted_wallet.json"

@app.route('/')
def index(): return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    p = request.json.get('p')
    try:
        with open(WALLET_FILE, "r") as f: data = json.load(f)
        key = Account.decrypt(data, p)
        session['pk'] = key.hex()
        session['addr'] = Account.from_key(key).address
        return jsonify({"s": True, "a": session['addr']})
    except: return jsonify({"s": False, "m": "Wrong PIN"})

@app.route('/data', methods=['POST'])
def data():
    if 'addr' not in session: return jsonify({"s": False})
    bnb, kly, usd, gas, hist = get_crypto_data(session['addr'])
    return jsonify({"s": True, "bnb": bnb, "kly": kly, "usd": usd, "gas": gas})

@app.route('/trade', methods=['POST'])
def trade():
    if 'pk' not in session: return jsonify({"s": False})
    try:
        t, amt = request.json['type'], request.json['amt']
        tx = buy_kly_with_bnb(session['pk'], amt) if t == 'buy' else swap_kly_for_bnb(session['pk'], amt)
        return jsonify({"s": True, "h": tx})
    except Exception as e: return jsonify({"s": False, "m": str(e)})
@app.route('/send', methods=['POST'])
def send_tokens_route():
    if 'pk' not in session: return jsonify({"s": False, "m": "Сесія вичерпана"})
    data = request.json
    try:
        # Виклик функції, яку ми щойно додали в blockchain.py
        tx_hash = send_kly_tokens(session['pk'], data['to'], data['amount'])
        return jsonify({"s": True, "h": tx_hash})
    except Exception as e:
        return jsonify({"s": False, "m": str(e)})

if __name__ == '__main__': app.run(debug=True)
