import cv2, os

path = r"C:\Users\Administração\Desktop\BW\transfer-2\imgs_referencia\img_ref_sem_mensagem_ativa.png"

print("Existe:", os.path.isfile(path))
img = cv2.imread(path)
print("Carregado:", img is not None)
