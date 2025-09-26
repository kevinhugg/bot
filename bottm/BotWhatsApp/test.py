import pyautogui

# mesma região usada em captura_resposta
region = (410, 400, 800, 600)

print(f"📸 Capturando região: {region}")
screenshot = pyautogui.screenshot(region=region)

# salva o print na pasta do projeto
screenshot.save("teste_ocr.png")
print("✅ Screenshot salvo como teste_ocr.png")
