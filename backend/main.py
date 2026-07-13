from fastapi import FastAPI, File, HTTPException, UploadFile

from preprocessing import preprocessar
from vision import extrair_dados_da_imagem

app = FastAPI(title="RestaurApp — Extração de Notas")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
async def extract(imagem: UploadFile = File(...)):
    conteudo = await imagem.read()
    try:
        imagem_processada = preprocessar(conteudo)
        dados = extrair_dados_da_imagem(imagem_processada)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha na extração: {exc}") from exc
    return dados
