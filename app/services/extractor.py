import base64
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.environ.get("EXTRACTOR_PROVIDER", "ollama")
API_URL = os.environ.get("EXTRACTOR_API_URL", "http://localhost:8000")

PROMPT_CLAUDE = """Extraia os dados desta nota fiscal de fornecedor de restaurante.

Se não conseguir ler um campo com confiança, use null nesse campo — não invente valores."""

SCHEMA_NOTA = {
    "type": "object",
    "properties": {
        "fornecedor": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "data": {"anyOf": [{"type": "string"}, {"type": "null"}]},
        "itens": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "produto": {"type": "string"},
                    "quantidade": {"type": "number"},
                    "unidade": {"type": "string", "enum": ["kg", "g", "L", "ml", "un", "cx", "dz"]},
                    "preco_unitario": {"type": "number"},
                },
                "required": ["produto", "quantidade", "unidade", "preco_unitario"],
                "additionalProperties": False,
            },
        },
        "total": {"anyOf": [{"type": "number"}, {"type": "null"}]},
    },
    "required": ["fornecedor", "data", "itens", "total"],
    "additionalProperties": False,
}


def extrair_nota(imagem_bytes: bytes) -> dict:
    if PROVIDER == "claude":
        return _extrair_via_claude(imagem_bytes)
    return _extrair_via_ollama(imagem_bytes)


def _extrair_via_ollama(imagem_bytes: bytes) -> dict:
    resposta = requests.post(
        f"{API_URL}/extract",
        files={"imagem": ("nota.jpg", imagem_bytes, "image/jpeg")},
        timeout=180,
    )
    resposta.raise_for_status()
    return resposta.json()


def _extrair_via_claude(imagem_bytes: bytes) -> dict:
    import anthropic

    cliente = anthropic.Anthropic()
    imagem_b64 = base64.b64encode(imagem_bytes).decode("utf-8")

    resposta = cliente.messages.create(
        model="claude-opus-4-8",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA_NOTA}},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/jpeg", "data": imagem_b64},
                    },
                    {"type": "text", "text": PROMPT_CLAUDE},
                ],
            }
        ],
    )
    texto = next(bloco.text for bloco in resposta.content if bloco.type == "text")
    return json.loads(texto)
