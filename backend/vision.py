import base64
import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "minicpm-v")

PROMPT = """Você extrai dados de notas fiscais de fornecedores de restaurante a partir de uma foto.

Responda SOMENTE com um JSON neste formato, sem texto antes ou depois:

{
  "fornecedor": "nome do fornecedor visível na nota, ou null se não der para ler",
  "data": "AAAA-MM-DD se visível, senão null",
  "itens": [
    {"produto": "nome do produto", "quantidade": 0.0, "unidade": "kg|g|L|ml|un|cx|dz", "preco_unitario": 0.0}
  ],
  "total": 0.0
}

Se não conseguir ler um campo com confiança, use null nesse campo. Não invente valores."""


def _para_numero(valor):
    """Converte para float mesmo se o modelo devolver texto tipo 'R$ 6,20'.

    O `format: "json"` do Ollama garante JSON válido, mas não garante que os
    campos numéricos do schema realmente venham como número — modelos locais
    às vezes formatam como moeda. Sem isso, a tela de validação quebraria ao
    tentar converter a string direto para float.
    """
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = re.sub(r"[^\d,.-]", "", str(valor)).strip()
    if not texto:
        return None
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _sanitizar(dados: dict) -> dict:
    dados["total"] = _para_numero(dados.get("total"))
    for item in dados.get("itens") or []:
        item["quantidade"] = _para_numero(item.get("quantidade"))
        item["preco_unitario"] = _para_numero(item.get("preco_unitario"))
    return dados


def extrair_dados_da_imagem(imagem_bytes: bytes) -> dict:
    imagem_b64 = base64.b64encode(imagem_bytes).decode("utf-8")

    resposta = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": PROMPT,
            "images": [imagem_b64],
            "format": "json",
            "stream": False,
        },
        timeout=480,
    )
    resposta.raise_for_status()
    texto = resposta.json()["response"]
    return _sanitizar(json.loads(texto))
