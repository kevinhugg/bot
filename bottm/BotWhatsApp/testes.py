import sys, os, time
import pyautogui, cv2, numpy as np
from config import dir_imgs_ref

x, y, largura, altura = 650, 250, 300, 400
os.makedirs(dir_imgs_ref, exist_ok=True)

caminho_ref = os.path.join(dir_imgs_ref, "img_ref_sem_mensagem_ativa.png")

def captura_ref():
    ref_img = pyautogui.screenshot(region=(x, y, largura, altura))
    ref_img.save(caminho_ref)
    print(f"Referência criada em: {caminho_ref}")

def compara_imagem(caminho_ref, limiar=0.85):
    screenshot = pyautogui.screenshot(region=(x, y, largura, altura))
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    img_ref = cv2.imread(caminho_ref)
    if img_ref is None:
        raise FileNotFoundError(f"Não encontrei a referência: {caminho_ref}")

    if screenshot_cv.shape != img_ref.shape:
        img_ref = cv2.resize(img_ref, (largura, altura))

    resultado = cv2.matchTemplate(screenshot_cv, img_ref, cv2.TM_CCOEFF_NORMED)
    similaridade = float(np.max(resultado))
    print(f"similaridade={similaridade:.4f}")
    return 1 if similaridade >= limiar else 0

if not os.path.isfile(caminho_ref):
    captura_ref()
else:
    status = compara_imagem(caminho_ref)
    print("STATUS:", status)
