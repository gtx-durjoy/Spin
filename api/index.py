# api/index.py — Vercel Python serverless function
# Runtime: python3.11, Vercel Hobby (10s) / Pro (60s)
import os
import sys
import json
import base64
import random
import codecs
import hashlib
import hmac
import secrets
import threading
from datetime import datetime
from typing import Dict, Optional, Any

from flask import Flask, render_template, request, jsonify

# ---- path fix: Vercel-এ root different ----
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE, "templates"),
    static_folder=os.path.join(BASE, "static"),
)

import requests
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Config:
    # serverless-এ /tmp writable; persistent না, তাই response-এই account ফেরত দাও
    ACCOUNTS_FILE = "/tmp/rixor.json"
    API_HEX_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
    API_SECRET_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

    # ---- ORIGINAL থেকে হুবহু, তোমার version-এ ভুল ছিল ----
    AES_KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    AES_IV  = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

    REGION_LANG = {
        "BD": "bn", "IND": "hi", "PK": "ur", "SG": "en", "ID": "id",
        "ME": "ar", "CIS": "ru", "TH": "th", "EU": "en", "US": "en",
        "SAC": "es", "LK": "en"
    }


class SecurityEngine:
    @staticmethod
    def generate_ultra_secure_password() -> str:
        return secrets.token_hex(16)

    @staticmethod
    def generate_signature(payload: str) -> str:
        # ORIGINAL: API_SECRET_KEY ব্যবহার হয়
        key = bytes.fromhex(Config.API_SECRET_KEY)
        return hmac.new(key, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def encrypt_api_payload(hex_data: str) -> str:
        # ORIGINAL: fixed AES_KEY + fixed AES_IV, zero IV না
        cipher = AES.new(Config.AES_KEY, AES.MODE_CBC, Config.AES_IV)
        padded = pad(bytes.fromhex(hex_data), AES.block_size)
        return cipher.encrypt(padded).hex()


class ProtoBuilder:
    @staticmethod
    def encode_varint(n: int) -> bytes:
        if n < 0: return b""
        result = bytearray()
        while True:
            byte = n & 0x7F
            n >>= 7
            if n: byte |= 0x80
            result.append(byte)
            if not n: break
        return bytes(result)

    @classmethod
    def create_field(cls, field_num: int, value: Any) -> bytes:
        if isinstance(value, int):
            return cls.encode_varint((field_num << 3) | 0) + cls.encode_varint(value)
        if isinstance(value, (str, bytes)):
            ev = value.encode() if isinstance(value, str) else value
            return cls.encode_varint((field_num << 3) | 2) + cls.encode_varint(len(ev)) + ev
        return b""

    @classmethod
    def build(cls, fields_dict: Dict[int, Any]) -> bytes:
        return b"".join(cls.create_field(k, v) for k, v in fields_dict.items())


# ---- module-level session: Vercel warm invocation-এ reuse হয় ----
_session = requests.Session()


class GarenaAPI:
    def __init__(self):
        self.session = _session

    def perform_major_login(self, access_token: str, open_id: str, lang: str):
        try:
            payload_parts = [
                b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.114.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02',
                lang.encode("ascii"),
                b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019118693\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'
            ]
            raw = b"".join(payload_parts)
            raw = raw.replace(b'afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390', access_token.encode())
            raw = raw.replace(b'1d8ec0240ede109973f3321b9354b44d', open_id.encode())
            enc = bytes.fromhex(SecurityEngine.encrypt_api_payload(raw.hex()))

            headers = {
                "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
                "Accept-Encoding": "deflate, gzip",
                "X-GA-SV": "1789535859",
                "Authorization": "Bearer",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB55",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Unity-Version": "2018.4.12f1",
            }
            r = self.session.post(
                "https://loginbp.ppmainecoonghj.com/MajorLogin",
                headers=headers, data=enc, verify=False, timeout=8,
            )
            if r.status_code == 200:
                i = r.text.find("eyJ")
                if i != -1:
                    tok = r.text[i:]
                    d = tok.find(".", tok.find(".") + 1)
                    if d != -1:
                        tok = tok[:d + 44]
                        pb = tok.split(".")[1]
                        pad_ = "=" * (4 - len(pb) % 4)
                        j = json.loads(base64.urlsafe_b64decode(pb + pad_))
                        acc = j.get("account_id") or j.get("external_id")
                        if acc:
                            return {"account_id": str(acc), "jwt_token": tok}
        except Exception:
            pass
        return None


def _save_account(rec: dict) -> None:
    try:
        data = []
        if os.path.exists(Config.ACCOUNTS_FILE):
            with open(Config.ACCOUNTS_FILE) as f:
                try:
                    d = json.load(f)
                    if isinstance(d, list): data = d
                except Exception:
                    pass
        data.append(rec)
        with open(Config.ACCOUNTS_FILE, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    req = request.get_json(silent=True) or {}
    region = str(req.get("region", "BD")).upper()
    prefix = str(req.get("prefix", "Rixor"))[:20]

    try:
        api = GarenaAPI()
        password = SecurityEngine.generate_ultra_secure_password()

        # ---- step 1: guest register ----
        reg_payload = json.dumps(
            {"app_id": 100067, "client_type": 2, "password": password, "source": 2},
            separators=(",", ":"),
        )
        headers_reg = {
            "User-Agent": "GarenaMSDK/4.0.44(25028RN03A ;Android 15;ar;EG;app 1.132.1 2019121229;)",
            "Connection": "Keep-Alive",
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Authorization": f"Signature {SecurityEngine.generate_signature(reg_payload)}",
            "Content-Type": "application/json; charset=utf-8",
            "Cookie": "datadome=oYpIhVco_RFvLHe_T9KFd5wuY0gcQuNfrlt4rHJY5QOkwv4TGt8gPMK32MbHuBdzJyfXnXlfzNZT_2tHr2kys8AMYT2~T71QP1S78_7Pdx4JLOXdSrflPT6cOX2vsyJh",
            "Host": "100067.connect.garena.com",
        }
        r1 = api.session.post(
            "https://100067.connect.garena.com/api/v2/oauth/guest:register",
            headers=headers_reg, data=reg_payload, timeout=8, verify=False,
        )
        try:
            j1 = r1.json()
        except Exception:
            j1 = {}
        if r1.status_code != 200 or j1.get("code") != 0:
            return jsonify({
                "status": "error",
                "step": "guest_register",
                "http": r1.status_code,
                "message": "Failed at guest registration step.",
                "body": r1.text[:300],
            })
        uid = j1["data"]["uid"]

        # ---- step 2: token grant ----
        tok_payload = json.dumps({
            "client_id": 100067,
            "client_secret": Config.API_HEX_KEY,
            "client_type": 2,
            "device_id": "02-344afb0e-593c-40b7-92f2-171972f74807",
            "password": password,
            "response_type": "token",
            "uid": uid,
        }, separators=(",", ":"))

        headers_tok = headers_reg.copy()
        headers_tok["Cookie"] = "datadome=y23Z3X17pgkMHEt5zY8dqxC6BIf7WJMgC0RXNbqifHT7t9zajKe_hegFb1Ie9_7JixXpz7FRGVodOn~mWPk_NrqIIhUOXDYqKOahzoRQcyEy77GWEMcdA9_MqPJeM5qv"
        r2 = api.session.post(
            "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant",
            headers=headers_tok, data=tok_payload, timeout=8, verify=False,
        )
        try:
            j2 = r2.json()
        except Exception:
            j2 = {}
        if r2.status_code != 200 or j2.get("code") != 0:
            return jsonify({
                "status": "error",
                "step": "token_grant",
                "http": r2.status_code,
                "message": "Failed at token grant step.",
                "body": r2.text[:300],
            })
        access_token = j2["data"]["access_token"]
        open_id = j2["data"]["open_id"]

        # ---- step 3: derive field ----
        ks = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,
              0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,
              0x30,0x30,0x32,0x30]
        field = codecs.decode(
            "".join(chr(ord(open_id[i]) ^ ks[i % len(ks)]) for i in range(len(open_id)))
            .encode("unicode_escape").decode("utf-8"),
            "unicode_escape",
        ).encode("latin1")

        name = f"{prefix}{random.randint(10000, 99999)}"
        lang = Config.REGION_LANG.get(region, "en")

        # ---- step 4: MajorRegister ----
        proto = ProtoBuilder.build({
            1: name, 2: access_token, 3: open_id, 5: 102000007, 6: 4, 7: 1,
            13: 1, 14: field, 15: lang, 16: 1, 17: 1,
        })
        enc_major = bytes.fromhex(SecurityEngine.encrypt_api_payload(proto.hex()))
        headers_major = {
            "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept-Encoding": "deflate, gzip",
            "X-GA-SV": "1789535859",
            "Authorization": "Bearer",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB55",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.12f1",
            "Host": "loginbp.ppmainecoonghj.com",
        }
        api.session.post(
            "https://loginbp.ppmainecoonghj.com/MajorRegister",
            headers=headers_major, data=enc_major, verify=False, timeout=8,
        )

        # ---- step 5: MajorLogin (get account_id) ----
        login_data = api.perform_major_login(access_token, open_id, lang)

        rec = {
            "uid": int(uid),
            "password": password,
            "account_id": login_data["account_id"] if login_data else "N/A",
            "name": name,
            "region": region,
            "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        _save_account(rec)
        return jsonify({"status": "success", "data": rec})

    except requests.Timeout:
        return jsonify({"status": "error", "step": "timeout",
                        "message": "Garena API request timed out (Vercel 10s limit)."})
    except Exception as e:
        return jsonify({"status": "error", "step": "exception",
                        "message": f"{type(e).__name__}: {e}"})


# Vercel entry — 'app' নামেই export হয়
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
