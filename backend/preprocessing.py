import cv2
import numpy as np


def _bytes_para_cv2(imagem_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(imagem_bytes, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _cv2_para_bytes(imagem: np.ndarray, qualidade: int = 85) -> bytes:
    ok, buffer = cv2.imencode(".jpg", imagem, [cv2.IMWRITE_JPEG_QUALITY, qualidade])
    return buffer.tobytes()


def _transformar_quatro_pontos(imagem, pontos):
    soma = pontos.sum(axis=1)
    diferenca = np.diff(pontos, axis=1)

    topo_esquerda = pontos[np.argmin(soma)]
    baixo_direita = pontos[np.argmax(soma)]
    topo_direita = pontos[np.argmin(diferenca)]
    baixo_esquerda = pontos[np.argmax(diferenca)]

    origem = np.array([topo_esquerda, topo_direita, baixo_direita, baixo_esquerda], dtype="float32")

    largura = max(
        int(np.linalg.norm(baixo_direita - baixo_esquerda)),
        int(np.linalg.norm(topo_direita - topo_esquerda)),
    )
    altura = max(
        int(np.linalg.norm(topo_direita - baixo_direita)),
        int(np.linalg.norm(topo_esquerda - baixo_esquerda)),
    )

    destino = np.array(
        [[0, 0], [largura - 1, 0], [largura - 1, altura - 1], [0, altura - 1]], dtype="float32"
    )
    matriz = cv2.getPerspectiveTransform(origem, destino)
    return cv2.warpPerspective(imagem, matriz, (largura, altura))


def corrigir_perspectiva(imagem: np.ndarray) -> np.ndarray:
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    borrado = cv2.GaussianBlur(cinza, (5, 5), 0)
    bordas = cv2.Canny(borrado, 50, 150)
    bordas = cv2.dilate(bordas, np.ones((5, 5), np.uint8), iterations=1)

    contornos, _ = cv2.findContours(bordas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contornos:
        return imagem

    maior = max(contornos, key=cv2.contourArea)
    area_imagem = imagem.shape[0] * imagem.shape[1]
    if cv2.contourArea(maior) < 0.2 * area_imagem:
        return imagem

    perimetro = cv2.arcLength(maior, True)
    aproximado = cv2.approxPolyDP(maior, 0.02 * perimetro, True)
    if len(aproximado) != 4:
        return imagem

    pontos = aproximado.reshape(4, 2).astype("float32")
    return _transformar_quatro_pontos(imagem, pontos)


def melhorar_contraste(imagem: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(imagem, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def redimensionar(imagem: np.ndarray, lado_maximo: int = 1600) -> np.ndarray:
    altura, largura = imagem.shape[:2]
    maior_lado = max(altura, largura)
    if maior_lado <= lado_maximo:
        return imagem
    escala = lado_maximo / maior_lado
    return cv2.resize(
        imagem, (int(largura * escala), int(altura * escala)), interpolation=cv2.INTER_AREA
    )


def preprocessar(imagem_bytes: bytes) -> bytes:
    imagem = _bytes_para_cv2(imagem_bytes)
    imagem = corrigir_perspectiva(imagem)
    imagem = melhorar_contraste(imagem)
    imagem = redimensionar(imagem)
    return _cv2_para_bytes(imagem)
