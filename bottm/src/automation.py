import pyautogui as pgui
import pygetwindow as gw
import psutil
import webbrowser
import time
import cv2
import numpy as np
import os
import random

from humanizer import Humanizer, HumanizeConfig
from config import IMG_REF_DIR, TM_IMGS_DIR
from constants import IMAGENS_REF, MATCH_THRESHOLD


class WhatsappAutomator:
    """
    Serviço para centralizar toda a automação da interface do usuário (UI) do WhatsApp.
    """

    def __init__(self, humanizer_config: HumanizeConfig | None = None):
        self.humanizer = Humanizer(humanizer_config or HumanizeConfig())
        self._load_reference_images()

    def _load_reference_images(self):
        """Carrega os caminhos completos das imagens de referência."""
        self.ref_imgs = {
            name: os.path.join(IMG_REF_DIR, path)
            for name, path in IMAGENS_REF.items()
        }
        # Garante que as imagens essenciais existam
        for name, path in self.ref_imgs.items():
            if not os.path.exists(path):
                print(f"AVISO: Imagem de referência não encontrada: {path}")

    def _find_image(self, image_key: str, precision: float = MATCH_THRESHOLD) -> list[int] | None:
        """Localiza uma imagem na tela usando sua chave de referência."""
        try:
            path = self.ref_imgs[image_key]
            location = pgui.locateOnScreen(path, confidence=precision)
            if location:
                return [location.left, location.top]
        except Exception as e:
            # pgui.ImageNotFoundException é comum, outros erros também podem ocorrer
            print(f"Erro ao localizar imagem '{image_key}': {e}")
        return None

    def _retry_find(self, image_key: str, limit: int = 10, step: float = 1.0) -> list[int]:
        """Tenta localizar uma imagem repetidamente até um limite de tempo."""
        for tentativa in range(limit):
            print(f"Tentando localizar '{image_key}' (tentativa {tentativa + 1}/{limit})")
            pos = self._find_image(image_key)
            if pos:
                print(f"'{image_key}' localizado com sucesso.")
                return pos
            self.humanizer.esperar(step * 0.8, step * 1.2)
        raise Exception(f"Não foi possível localizar o elemento '{image_key}' após {limit} tentativas.")

    def open_conversation(self, phone_number: str):
        """Abre uma conversa no WhatsApp Desktop para um número específico."""
        # Garante que processos antigos sejam encerrados para um estado limpo
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] in ["WhatsApp.exe", "msedge.exe"]:
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass

        self.humanizer.esperar(1, 2)
        webbrowser.open(f"https://wa.me/{phone_number}")
        self.humanizer.esperar(4, 6)  # Espera o navegador abrir e processar o link

        # Maximiza a janela para um estado consistente
        try:
            # Tenta focar e maximizar a janela do Edge/Chrome e depois do WhatsApp
            self._maximize_window("Edge")
            self.humanizer.esperar(1, 2)
            self._maximize_window("WhatsApp")
        except Exception as e:
            print(f"Não foi possível maximizar a janela, continuando... Erro: {e}")

    def check_for_invalid_number(self, timeout_sec: int = 20) -> bool:
        """
        Verifica de forma inteligente se a tela de número inválido apareceu ou se a
        tela de conversa carregou.
        """
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            if self._find_image("TELEFONE_INVALIDO", precision=0.85):
                print("Tela de 'Telefone Inválido' detectada.")
                return True
            if self._find_image("FORM_MSG", precision=0.8):
                print("Tela de conversa carregada com sucesso.")
                return False
            self.humanizer.esperar(0.8, 1.2)

        raise Exception("Timeout: A tela do WhatsApp não carregou (nem sucesso, nem erro).")

    def send_message(self, client_name: str, message_template: str):
        """Encontra o campo de texto, digita e envia a mensagem."""
        try:
            pos = self._retry_find("FORM_MSG", limit=5)
            # Clica um pouco à direita do ícone para focar o campo de texto
            click_point = (pos[0] + 150, pos[1])

            self.humanizer.click(click_point[0], click_point[1], clicks=2)

            full_message = f"Olá, {client_name}! {message_template}"
            self.humanizer.escrever(full_message)
            self.humanizer.enter()
            print(f"Mensagem enviada para {client_name}.")

        except Exception as e:
            print(f"Falha ao enviar mensagem: {e}")
            raise

    def attach_campaign_image(self):
        """Anexa uma imagem de uma campanha aleatória na conversa."""
        try:
            # 1. Encontra e clica no botão de anexo
            pos_anexo = self._retry_find("BTN_ANEXAR_IMG", limit=5)
            self.humanizer.click(pos_anexo[0], pos_anexo[1])

            # 2. Encontra e clica no botão de "Fotos e Vídeos"
            pos_fotos = self._retry_find("BTN_FOTOS_VIDEOS", limit=5)
            self.humanizer.click(pos_fotos[0], pos_fotos[1], clicks=2)  # Clica duas vezes para garantir

            self.humanizer.esperar(1.5, 2.5)  # Espera a janela de seleção de arquivo abrir

            # 3. Navega até a pasta e seleciona as imagens
            pgui.hotkey("ctrl", "l")  # Foca na barra de endereço
            self.humanizer.esperar(0.5, 1)

            # Escolhe uma pasta de campanha aleatória
            campanhas = [d for d in os.listdir(TM_IMGS_DIR) if os.path.isdir(os.path.join(TM_IMGS_DIR, d))]
            if not campanhas:
                print("Nenhuma pasta de campanha encontrada.")
                return

            campanha_escolhida = random.choice(campanhas)
            dir_campanha = os.path.join(TM_IMGS_DIR, campanha_escolhida)

            self.humanizer.escrever(str(dir_campanha))
            self.humanizer.enter()
            self.humanizer.esperar(1, 2)

            # Seleciona todos os arquivos e envia
            pgui.hotkey("ctrl", "a")
            self.humanizer.esperar(0.5, 1)
            self.humanizer.enter()  # Confirma a seleção
            self.humanizer.esperar(2, 3)
            self.humanizer.enter()  # Envia as imagens
            print(f"Imagens da campanha '{campanha_escolhida}' anexadas.")

        except Exception as e:
            print(f"Falha ao anexar imagem: {e}")
            # Tenta fechar a janela de anexo para não travar o fluxo
            pgui.press("esc")
            raise

    def _maximize_window(self, app_name_partial: str):
        """Tenta encontrar e maximizar uma janela pelo seu título parcial."""
        try:
            windows = [win for win in gw.getWindowsWithTitle(app_name_partial) if win.title]
            if not windows:
                print(f"Janela com título '{app_name_partial}' não encontrada.")
                return

            window = windows[0]
            if not window.isMaximized:
                window.maximize()
                print(f"Janela '{window.title}' maximizada.")
            else:
                print(f"Janela '{window.title}' já estava maximizada.")
            window.activate()

        except Exception as e:
            print(f"Erro ao tentar maximizar a janela '{app_name_partial}': {e}")