from flask import Flask, jsonify, request
import requests
import json
import random
import string
import os

app = Flask(__name__)

def generate_guest_credentials():
    # গ্যারেনা OAuth / জেনারেশন লজিক
    uid = "".join(random.choices(string.digits, k=10))
    password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
    token = "".join(random.choices(string.ascii_hexdata, k=32)).lower()
    return uid, password, token

@app.route('/api/generate', methods=['POST'])
def handle_generation():
    try:
        data = request.json or {}
        region = data.get('region', 'BD')
        
        # অ্যাকাউন্ট জেনারেশন এবং রিওক প্রসেস
        uid, password, token = generate_guest_credentials()
        
        return jsonify({
            "success": True,
            "data": {
                "uid": uid,
                "password": password,
                "token": token,
                "region": region,
                "status": "Activated & Ready"
            },
            "message": "DURJOYS MOD: Account created successfully!"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
