# -*- coding: utf-8 -*-
import json
import os
from urllib.parse import urljoin
import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
import base64


class PagaService(object):
    def __init__(self, email, password, proxy_url=None):
        self.email = email
        self.password = password
        self.base_url = "https://api.paga.com"
        self.session = requests.Session()
        if proxy_url:
            self.session.proxies = {
                "http": proxy_url,
                "https:"": proxy_url,
            }
        self.session.headers.update({
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "content-type": "application/json;charset=UTF-8",
            "Referer": "https://mypaga.com/",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        })
        self.public_key = self.get_public_key()

    def get_public_key(self):
        url = urljoin(self.base_url, "/paga-services/paga-web/v2/get-public-key")
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json().get('publicKey')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching public key: {e}")
            return None

    def encrypt_password(self):
        if not self.public_key:
            return None
        key = f"-----BEGIN PUBLIC KEY-----\n{self.public_key}\n-----END PUBLIC KEY-----"
        pub_key = RSA.importKey(key)
        cipher = PKCS1_v1_5.new(pub_key)
        return base64.b64encode(cipher.encrypt(self.password.encode('utf-8'))).decode('utf-8')

    def _make_request(self, method, endpoint, data=None):
        url = urljoin(self.base_url, endpoint)
        encrypted_password = self.encrypt_password()
        if not encrypted_password:
            return {"error": "Failed to encrypt password, check public key."}

        auth_data = {
            "principal": self.email,
            "credentials": encrypted_password,
            "rememberMe": "true",
            "validationCode": data.get('validationCode', '') if data else ''
        }

        headers = self.session.headers.copy()
        response = self.session.post(urljoin(self.base_url, "/paga-services/paga-web/v2/authenticate"), json=auth_data)

        if response.status_code != 200 or "authToken" not in response.json():
            return response.json()

        auth_token = response.json()["authToken"]
        headers["Authorization"] = f"Bearer {auth_token}"

        if data:
            # Remove auth-related fields from data before sending to the final endpoint
            data.pop('validationCode', None)

        try:
            req = self.session.request(method, url, json=data, headers=headers)
            req.raise_for_status()
            return req.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def get_account_info(self):
        return self._make_request("GET", "/paga-services/paga-web/v2/get-account-info")

    def open_usd_card(self, validation_code):
        data = {"validationCode": validation_code}
        return self._make_request("POST", "/paga-services/paga-web/v2/virtual-card/USD", data=data)

    def fund_paga_card(self, validation_code, amount, card_last_four_digits, external_serial_number, is_auto_card):
        payload = {
            "validationCode": validation_code,
            "amount": amount,
            "cardLastFourDigits": card_last_four_digits,
            "externalSerialNumber": external_serial_number,
            "is_auto_card": is_auto_card
        }
        # This logic might need adjustment based on how the API expects the call
        # Assuming a generic endpoint for funding. This might need to be more specific.
        return self._make_request("POST", "/paga-services/paga-web/v2/fund-card", data=payload)
