# -*- coding: utf-8 -*-
import json
import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from paga_services import PagaService

# Imports que añadimos para servir las páginas HTML
from fastapi.responses import FileResponse

app = FastAPI()

# ... (código de configuración de CORS, igual que el original)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cargar variables de entorno
load_dotenv()
PAGA_ACCOUNT = os.getenv("PAGA_ACCOUNT")
PAGA_PASSWORD = os.getenv("PAGA_PASSWORD")
PROXY_URL = os.getenv("PROXY_URL")


@app.get('/api/paga/getAccountInfo')
async def get_account_info(request: Request):
    paga_service = PagaService(PAGA_ACCOUNT, PAGA_PASSWORD, PROXY_URL)
    response = paga_service.get_account_info()
    return JSONResponse(content=response)


@app.post('/api/paga/openUsdCard')
async def open_usd_card(request: Request):
    try:
        req_info = await request.json()
    except Exception:
        return "request body is not json"
    email = req_info['email']
    password = req_info['password']
    validation_code = req_info['validationCode']
    paga_service = PagaService(email, password, PROXY_URL)
    response = paga_service.open_usd_card(validation_code)
    return JSONResponse(content=response)


@app.post('/api/paga/fundPagaCard')
async def fund_paga_card(request: Request):
    try:
        req_info = await request.json()
    except Exception:
        return "request body is not json"
    email = req_info['email']
    password = req_info['password']
    validation_code = req_info['validationCode']
    amount = req_info['amount']
    card_last_four_digits = req_info['cardLastFourDigits']
    external_serial_number = req_info['externalSerialNumber']
    is_auto_card = req_info['is_auto_card']

    paga_service = PagaService(email, password, PROXY_URL)
    response = paga_service.fund_paga_card(validation_code, amount, card_last_four_digits, external_serial_number,
                                           is_auto_card)
    return JSONResponse(content=response)

# ===============================================================
# ||      SECCIÓN AÑADIDA PARA MOSTRAR LAS PÁGINAS WEB         ||
# ===============================================================

@app.get("/", response_class=FileResponse)
async def read_index():
    return "paga/index.html"

@app.get("/card.html", response_class=FileResponse)
async def read_card_page():
    return "paga/card.html"

@app.get("/fundCard.html", response_class=FileResponse)
async def read_fund_card_page():
    return "paga/fundCard.html"

# ===============================================================
# ||                 FIN DE LA SECCIÓN AÑADIDA                 ||
# ===============================================================

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
