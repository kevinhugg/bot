import sys
import pyautogui
import cv2
import numpy as np
import pyautogui
import time


x=650
y=250
largura = 300
altura = 400


def mouse_posicao():
    time.sleep(2)
    x, y = pyautogui.position()
    print(f"x={x}, y={y}")


def captura_retangulo(x, y, largura, altura, caminho_saida):
    # Captura a região especificada
    screenshot = pyautogui.screenshot(region=(x, y, largura, altura))
    # Salva no caminho informado
    screenshot.save(caminho_saida)

def compara_imagem(x, y, largura, altura, caminho_ref, limiar=0.99):
    # Captura a região especificada
    screenshot = pyautogui.screenshot(region=(x, y, largura, altura))

    # Converte para formato OpenCV
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # Carrega imagem de referência
    img_ref = cv2.imread(caminho_ref)

    # Redimensiona a imagem de referência se necessário
    if screenshot_cv.shape != img_ref.shape:
        img_ref = cv2.resize(img_ref, (largura, altura))

    # Compara usando matchTemplate
    resultado = cv2.matchTemplate(screenshot_cv, img_ref, cv2.TM_CCOEFF_NORMED)
    similaridade = np.max(resultado)

    # Retorna 1 para match e 0 para dismatch
    return 1 if similaridade >= limiar else 0

time.sleep(2)
status = compara_imagem(x=x, y=y, largura=largura, altura=altura, caminho_ref=r"C:\Users\ferrati\Documents\img_ref_sem_mensagem_ativa.png")


print(status)
sys.exit()

time.sleep(2)
captura_retangulo(
    x=x
    , y=y
    , largura=300
    , altura=400
    , caminho_saida=r"C:\Users\ferrati\Documents\teste.png"
)