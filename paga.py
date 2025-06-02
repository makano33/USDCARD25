import hashlib

import requests
import urllib3
from fastapi import FastAPI, Request, Response
from pathlib import Path
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

urllib3.disable_warnings()
from urllib.parse import quote_plus

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64

import logging

PAGA_DIR = Path("paga")
PAGA_DIR.mkdir(parents=True, exist_ok=True)

# 自行配置动态代理
# proxies = {
#     "https:": "socks5://127.0.0.1:40000"
# }

proxies = None

# -------------------------- 日志配置 --------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("main")

# -------------------------- app配置 --------------------------
# 可以根据手机号hash唯一值
DEVICES_ID = 'e0adbaa600fde332'
APP_VERSION = '4.4.28'
VERSION_COED = '2072221570'

app = FastAPI()

# 配置静态访问路径
app.mount("/paga", StaticFiles(directory=PAGA_DIR), name="paga")

# 添加根路径入口点，直接返回index.html内容
@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = PAGA_DIR / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content

# 添加卡片页面入口点
@app.get("/card", response_class=HTMLResponse)
async def card_page():
    card_path = PAGA_DIR / "card.html"
    with open(card_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content

# 添加充值页面入口点
@app.get("/fundcard", response_class=HTMLResponse)  
async def fund_card_page():
    fund_path = PAGA_DIR / "fundCard.html"
    with open(fund_path, "r", encoding="utf-8") as f:
        content = f.read()
    return content

# paga开美金卡
@app.post("/api/paga/openUsdCard")
async def openUsdCard(request: Request):
    req_json = await request.json()

    email = req_json['email']

    password = req_json['password']
    validationCode = req_json['validationCode']

    headers = {
        'appVersion': APP_VERSION,
        'versionCode': VERSION_COED,
        'deviceId': DEVICES_ID,
        'Cookie': 'paga-webservices-canary=never; Path=/; Secure; HttpOnly; SameSite=None',
        'Content-Type': 'application/json; charset=UTF-8',
        'Host': 'www.mypaga.com',
        'User-Agent': 'okhttp/4.12.0',
    }

    json_data = {
        'appBuildVersion': APP_VERSION,
        'deviceId': DEVICES_ID,
    }

    response = requests.post('https://www.mypaga.com/paga-webservices/customer-mobile/handshake/v1', headers=headers,
                             json=json_data, proxies=proxies, verify=False)

    if response.status_code == 200:
        response_json = response.json()
        if response_json['responseCode'] == 0:

            privateKey = response_json['privateKey']
            credential = encrypt_data(password, privateKey)

            json_data = {
                'credential': credential,
                'deviceId': DEVICES_ID,
                'principal': email,
                'validationCode': validationCode,
                'appBuildVersion': APP_VERSION,
                'deviceType': 'MOBILE_ANDROID',
            }
            if validationCode != '':
                # 验证码不为空的时候，注册新设备
                response = requests.post(
                    'https://www.mypaga.com/paga-webservices/customer-mobile/validateDevice/v1',
                    headers=headers,
                    json=json_data, proxies=proxies, verify=False
                )

                if response.status_code == 200:
                    response_json = response.json()
                    if response_json['responseCode'] != 0:
                        return Response(content=response.content, status_code=response.status_code,
                                        headers=response.headers)
                else:
                    return Response(content=response.content, status_code=response.status_code,
                                    headers=response.headers)

            json_data = {
                'cardTheme': 'CLASSIC',
                'nickname': '',
                'amount': 2.0,
                'currency': 'USD',
                'fundingSource': {
                    'type': 'PAGA',
                },
                'credential': credential,
                'credentialType': 'password',
                'deviceId': DEVICES_ID,
                'principal': email,
                'appBuildVersion': APP_VERSION,
                'deviceType': 'MOBILE_ANDROID',
            }

            response = requests.post(
                'https://www.mypaga.com/paga-webservices/customer-mobile/secured/requestVirtualCard/v1',
                headers=headers,
                json=json_data,
                proxies=proxies, verify=False
            )

            if response.status_code == 200:
                response_json = response.json()

                if response_json['responseCode'] == 0:
                    logger.info(f' --- paga open usd card success --- {email}')

                else:
                    logger.info(f' --- paga open usd card fail --- {email} --- {response.content}')

            else:
                logger.info(f' --- paga open usd card fail --- {email} --- {response.content}')

    return Response(content=response.content, status_code=response.status_code, headers=response.headers)


# paga钱包充值到卡里
@app.post("/api/paga/fundPagaCard")
async def fundPagaCard(request: Request):
    req_json = await request.json()

    email = req_json['email']

    password = req_json['password']
    cardLastFourDigits = req_json['cardLastFourDigits']
    externalSerialNumber = req_json['externalSerialNumber']
    amount = req_json['amount']
    # 根据用户信息自动获取卡片信息,1是自动,0是手动填写
    is_auto_card = req_json['is_auto_card']

    validationCode = req_json['validationCode']

    headers = {
        'appVersion': APP_VERSION,
        'versionCode': VERSION_COED,
        'deviceId': DEVICES_ID,
        'Cookie': 'paga-webservices-canary=never; Path=/; Secure; HttpOnly; SameSite=None',
        'Content-Type': 'application/json; charset=UTF-8',
        'Host': 'www.mypaga.com',
        'User-Agent': 'okhttp/4.12.0',
    }

    json_data = {
        'appBuildVersion': APP_VERSION,
        'deviceId': DEVICES_ID,
    }

    response = requests.post('https://www.mypaga.com/paga-webservices/customer-mobile/handshake/v1', headers=headers,
                             json=json_data, proxies=proxies, verify=False)

    if response.status_code == 200:
        response_json = response.json()
        if response_json['responseCode'] == 0:

            privateKey = response_json['privateKey']
            credential = encrypt_data(password, privateKey)

            json_data = {
                'credential': credential,
                'deviceId': DEVICES_ID,
                'principal': email,
                'validationCode': validationCode,
                'appBuildVersion': APP_VERSION,
                'deviceType': 'MOBILE_ANDROID',
            }
            if validationCode != '':
                # 验证码不为空的时候，注册新设备
                response = requests.post(
                    'https://www.mypaga.com/paga-webservices/customer-mobile/validateDevice/v1',
                    headers=headers,
                    json=json_data, proxies=proxies, verify=False
                )

                if response.status_code == 200:
                    response_json = response.json()
                    if response_json['responseCode'] != 0:
                        return Response(content=response.content, status_code=response.status_code,
                                        headers=response.headers)
                else:
                    return Response(content=response.content, status_code=response.status_code,
                                    headers=response.headers)
            # 根据账号自动获取卡片信息
            if is_auto_card == '1':
                json_data = {
                    'requestType': 'ALL_DATA',
                    'validationType': 'EMAIL',
                    'credential': credential,
                    'credentialType': 'password',
                    'deviceId': DEVICES_ID,
                    'principal': email,
                    'appBuildVersion': APP_VERSION,
                    'deviceType': 'MOBILE_ANDROID',
                }
                response = requests.post(
                    'https://www.mypaga.com/paga-webservices/customer-mobile/secured/getUserData/v3',
                    headers=headers,
                    json=json_data,
                    proxies=proxies, verify=False
                )

                response_json = response.json()

                if response_json['responseCode'] == 0 and 'userData' in response_json:
                    if 'virtualCards' in response_json['userData']:
                        virtualCards = response_json['userData']['virtualCards']
                        for virtualCard in virtualCards:
                            if virtualCard['cardCurrency'] == 'USD':
                                cardLastFourDigits = virtualCard['cardPan']
                                if len(cardLastFourDigits) >= 4:
                                    cardLastFourDigits = cardLastFourDigits[-4:]

                                externalSerialNumber = virtualCard['externalSerialNumber']
                                break
                    else:

                        logger.info(f' --- paga get user info fail --- {email} --- {response.content}')

                        return Response(content="没有美金卡", status_code=response.status_code,
                                        headers=response.headers)
                else:
                    logger.info(f' --- paga get user info fail --- {email} --- {response.content}')

                    return Response(content=response.text, status_code=response.status_code,
                                    headers=response.headers)

            params = concatenate_parameters(cardLastFourDigits, amount, externalSerialNumber, privateKey)

            hash = convert_sha512(params)

            json_data = {
                'credential': credential,
                'appBuildVersion': APP_VERSION,
                'currency': 'USD',
                'cardLastFourDigits': cardLastFourDigits,
                'externalSerialNumber': externalSerialNumber,
                'amount': amount,
                'hash': hash,
                'deviceType': 'MOBILE_ANDROID',
                'deviceId': DEVICES_ID,
                'credentialType': 'password',
                'fundingSource': {
                    'type': 'PAGA',
                },
                'principal': email,
            }

            response = requests.post(
                'https://www.mypaga.com/paga-webservices/customer-mobile/secured/fundPagaCard/v1',
                headers=headers,
                json=json_data,
                proxies=proxies, verify=False
            )

    logger.info(f' --- paga fundPagaCard --- {email} --- {response.content}')

    return Response(content=response.content, status_code=response.status_code, headers=response.headers)


def concatenate_parameters(*str_arr):
    if str_arr is None:
        return ""

    result = []
    for s in str_arr:
        if s:  # This checks if the string is not None or empty
            result.append(s)

    return "".join(result)


def encrypt_data(data, key):
    if data is None:
        data = ""
    data_bytes = data.encode('utf-8')

    # 如果密钥不足32字节，补全到32字节
    if key is not None:
        key = key[:32]
    else:
        key = ""
    key_bytes = key.encode('utf-8').ljust(32, b'\0')  # 补全到32字节

    cipher = AES.new(key_bytes, AES.MODE_ECB)
    padded_data = pad(data_bytes, AES.block_size)
    encrypted_bytes = cipher.encrypt(padded_data)
    encoded_encrypted_data = base64.b64encode(encrypted_bytes).decode('utf-8')

    return encoded_encrypted_data


def convert_sha512(input_str):
    if len(input_str) == 0:
        return ""

    try:
        digest = hashlib.sha512(input_str.encode()).digest()
        hex_digest = ''.join(['{:02x}'.format(b) for b in digest])
        return hex_digest
    except Exception as e:
        return None


# 启动服务器
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
