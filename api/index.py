from flask import Flask, jsonify, request
import requests
import json
import random
import string
import os

app = Flask(__name__)

def generate_guest_payload(prefix, region):
    # Random ID and Account Details Generation
    uid = "".join(random.choices(string.digits, k=10))
    password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
    name = f"{prefix}_{random.randint(100, 999)}"
    
    return {
        "uid": uid,
        "password": password,
        "name": name,
        "region": region,
        "status": "Active & Registered"
    }

@app.route('/api/generate', methods=['POST', 'GET'])
def generate_account():
    # CORS Headers Handling
    if request.method == 'OPTIONS':
        return jsonify({'status': 'OK'}), 200

    if request.method == 'GET':
        return jsonify({
            "status": "online",
            "message": "DURJOYS MOD API is active!"
        }), 200

    try:
        data = request.get_json(force=True, silent=True) or {}
        region = data.get('region', 'BD')
        prefix = data.get('prefix', 'DURJOY')

        if not prefix.strip():
            prefix = "DURJOY"

        # Account Processing Logic
        account_data = generate_guest_payload(prefix, region)

        return jsonify({
            "success": True,
            "data": account_data,
            "message": "Account generated successfully!"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
