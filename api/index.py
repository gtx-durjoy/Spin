from flask import Flask, jsonify, request
import requests
import json
import random
import string

app = Flask(__name__)

def generate_guest_payload():
    # মূল স্ক্রিপ্টের জেনারেশন লজিক এবং এনক্রিপশন প্রসেস এখানে বসবে
    return {
        "status": "success",
        "uid": "".join(random.choices(string.digits, k=10)),
        "password": "".join(random.choices(string.ascii_letters + string.digits, k=12)),
        "region": "BD"
    }

@app.route('/api/generate', methods=['POST'])
def generate_account():
    try:
        data = request.json or {}
        region = data.get('region', 'BD')
        
        # মূল স্ক্রিপ্টের Garena OAuth/API রিকুয়েস্ট
        result = generate_guest_payload()
        result['region'] = region
        
        return jsonify({
            "success": True,
            "data": result,
            "message": "Account generated successfully!"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Vercel-এর জন্য হ্যান্ডলার
if __name__ == '__main__':
    app.run(debug=True)
    
