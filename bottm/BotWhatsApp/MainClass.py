#################
## IMPORTACOES ##
#################
import sys

from mouse import on_click
from pywinauto.application import Application
from pywinauto import Desktop
import pyautogui as pgui
import pandas as pd
from config import *
import numpy as np
import webbrowser
import pyperclip
import pygetwindow as gw
import pyautogui
import random
import warnings
import psutil
import time
import cv2
import pyautogui
import mouse
import os
#################

# SUPRIME AVISOS
warnings.filterwarnings("ignore", category=SyntaxWarning)

###############
## VARIAVEIS ##
###############


raiz = r"\\100.96.1.3\transfer"
l = rf"{raiz}\imgs_referencia\form_msg.png"
raiz_status = fr"{raiz}\status_bots"
raiz_logs = rf"{raiz}\logs\log_transacional"
dir_log_imgs = rf"{raiz}\logs\log_img"
raiz_projeto = fr"{raiz}"
img_form_msg = rf"{raiz}\imgs_referencia\form_msg.png"


x_formulario_msg = 615
y_formulario_msg = 707


########################
class Tools:

    canal = None

    # MAILING
    @staticmethod
    def mailing(canal):
        df_mailing = None
        df_discagem = None

        ###############
        ## ARQUIVOS ##
        ###############
        arquivo_mailing = fr"{raiz_projeto}\mailing\mailing_{canal}.txt"
        arquivo_discagem = fr'{raiz_projeto}\dump_discagem\discagem_{canal}.txt'

        ##############
        ## LEITURAS ##
        ##############
        try:
            df_mailing = pd.read_csv(
                arquivo_mailing
                , sep=";"
                , header=0
                , names=["Cliente", "Telefone"]
                , usecols=[0, 1]
                , dtype=str
            )
        except Exception as e:
            Tools.log(msg=f"Erro ao ler mailing: {e}", canal=Tools.canal)
            sys.exit()

        try:
            df_discagem = pd.read_csv(
                arquivo_discagem
                , sep=";"
                , header=None
                , usecols=[1]
                , names=["Telefone"]
                , dtype=str
            )
        except Exception as e:
            Tools.log(msg=f"Erro ao ler discagem: {e}", canal=Tools.canal)
            sys.exit()

        #################################################################
        ## FORMATAÇÃO DOS TELEFONES (SOMENTE DÍGITOS E ADIÇÃO DO 55) ##
        #################################################################
        df_mailing['Telefone'] = df_mailing['Telefone'].astype(str).str.replace(r'\D', '', regex=True).str.strip()
        df_discagem['Telefone'] = df_discagem['Telefone'].astype(str).str.replace(r'\D', '', regex=True).str.strip()

        df_mailing['Telefone'] = df_mailing['Telefone'].apply(lambda x: x if x.startswith('55') else '55' + x)
        df_discagem['Telefone'] = df_discagem['Telefone'].apply(lambda x: x if x.startswith('55') else '55' + x)

        ##################################################
        ## RETORNA MAILING COMPLETO OU FILTRADO POR DISCAGEM ##
        ##################################################
        if canal.lower() == "teste":
            df = df_mailing.copy()  # sem filtro
        else:
            df = df_mailing[~df_mailing["Telefone"].isin(df_discagem["Telefone"])].copy()
        #df = df_mailing[~df_mailing["Telefone"].isin(df_discagem["Telefone"])].copy()

        ###############
        ## REMOVER DUPLICADOS ##
        ###############
        df = df.drop_duplicates(subset=["Telefone"])
        return df

    # REGISTRA DISCAGEM
    @staticmethod
    def registra_discagem(datadiscagem, telefone, canal, status):
        try:
            # garante a pasta dump_discagem
            dir_dump = fr'{raiz_projeto}\dump_discagem'
            os.makedirs(dir_dump, exist_ok=True)

            # mantém o mesmo caminho e formato
            with open(fr'{dir_dump}\discagem_{canal}.txt', 'a', encoding='utf-8') as f:
                # campos: DataDiscagem;Telefone;Status
                f.write(f"{datadiscagem};{telefone};{status}\n")

            Tools.log(msg=f"DISCAGEM ADICIONADA COM SUCESSO", canal=Tools.canal)
        except Exception as e:
            Tools.log(msg=f"ERRO AO REGISTRAR DISCAGEM | {e}", canal=Tools.canal)

    # VALIDA STATUS
    @staticmethod
    def valida_status_bot(canal):
        canal = canal.lower()
        caminho = os.path.join(raiz_status, f"status_{canal}.txt")

        try:
            df = pd.read_csv(caminho, sep=";", header=None)  # Sem cabeçalho
            status = df.iloc[0, 1]  # Pega valor da linha 0, coluna 1
            return status
        except Exception as e:
            Tools.log(msg=f"Erro ao ler o status do bot: {e}", canal=canal)
            return None

    @staticmethod
    def altera_status_bot(canal, novo_status):
        canal = canal.lower()
        caminho = os.path.join(raiz_status, f"status_{canal}.txt")

        try:
           # LEITURA DO ARQUIVO
            df = pd.read_csv(caminho, sep=";", header=None)

            # ALTERA O VALOR DO STATUS
            df.iloc[0, 1] = novo_status

            # SALVA O ARQUIVO
            df.to_csv(caminho, sep=";", header=False, index=False)
            print(f"Status do canal '{canal}' atualizado para '{novo_status}'.")
        except Exception as e:
            print(f"Erro ao alterar o status do bot: {e}")

    # LOGS
    @staticmethod
    def log(msg, canal):
        timestamp = time.strftime('%y-%m-%d %H:%M:%S')

        # IMPRIME FORMATADO NO CONSOLE
        print(f"{'-' * 50}\n{timestamp} | {msg}\n{'-' * 50}")

        # GRAVA SIMPLES NO ARQUIVO
        caminho_log = os.path.join(raiz_logs, f"log_{canal}.txt")
        with open(caminho_log, "a", encoding="utf-8") as f:
            f.write(f"{timestamp};{msg}\n")

    @staticmethod
    def abre_whatsapp_desktop(numero, sleep=None):
        """
        Abre uma conversa no WhatsApp Web com o número informado.
        :param numero: Número no formato DDI + DDD + número (ex: 5511987654321)
        :param sleep: tempo de espera generico
        """

        # PROCESSOS QUE PRECISAM SER ENCERRADOS
        procs_ambiente_whatsapp = ["WhatsApp.exe", "msedge.exe"]

        def garante_edge():
            """
            GARANTE QUE O EDGE ESTEJA ABERTA EM PRIMEIRO PLANO
            """
            try:
                app = Application(backend="uia").connect(title_re=".*Edge.*")
                window = app.top_window()
                window.set_focus()
            except Exception as e:
                Tools.log(msg=f"Erro ao ativar o Edge: {e}", canal=Tools.canal)

            time.sleep(2)
            Tools.pressionar_tecla(tecla1="ctrl", tecla2="l", press_enter="yes")

        # ENCERRA TODOS OS PROCESSOS DE WHATSAPP E EDGE ABERTOS
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                if proc.info["name"] in procs_ambiente_whatsapp:
                    proc.kill()
            except Exception as e:
                print(f"Erro ao encerrar processo: {e}")

        # Abre o link que direciona para o WhatsApp Desktop
        url = f"https://wa.me/{numero}"
        webbrowser.open(url)
        time.sleep(5)
        for i in range(2):
            garante_edge()


        if sleep:
            time.sleep(sleep)

    @staticmethod
    def click(posicao, sleep=None):

        x = posicao[0]
        y = posicao[1]

        try:
            pgui.click([x, y])

            if sleep:
                time.sleep(sleep)

        except Exception as e:
            print(f"Erro | {e}")

    @staticmethod
    def escreve(msg, sleep=None, press_enter=None):

        pgui.write(message=msg)

        if sleep:
            time.sleep(sleep)

        if press_enter:
            Tools.pressionar_tecla(tecla1="enter")

    @staticmethod
    def pressionar_tecla(tecla1, tecla2=None, sleep=None, press_enter=None):
        """
        Pressiona uma tecla ou combinação de teclas.

        :param tecla1: Tecla principal (ex: 'enter', 'shift')
        :param tecla2: Tecla secundária (usada se for hotkey)
        :param sleep: Tempo para aguardar após pressionar (em segundos)
        :param usar_hotkey: Se True, pressiona como hotkey (ex: shift + tab)
        """
        if tecla2:
            pgui.hotkey(tecla1, tecla2)
        else:
            pgui.press(tecla1)

        if sleep:
            time.sleep(sleep)

        if press_enter:

            pgui.press(keys="enter")

    @staticmethod
    def area_trabalho(sleep=None):
        pgui.hotkey("win", "d")
        if sleep:
            time.sleep(1)

    @staticmethod
    def anexa_img_campanha(canal, lead, espera=2):
        """

        :param espera:
        :return:
        """

        # DIRETORIOS
        dir_img_db = rf"\\100.96.1.3\transfer\tm\imgs\Campanha{random.randint(1, 13)}"
        raiz_dir = dirs_ref["dir_img_ref"]

        limit = 10
        posicao_fotos_videos = None
        posicao_anexar_imgs = None
        step = 1

        # IMGS
        btn_anexar_img = os.path.join(raiz_dir, imagens_ref["btn_anexar_img"])
        btn_fotos_videos = os.path.join(raiz_dir, imagens_ref["btn_fotos_videos"])
        form_msg = os.path.join(raiz_dir, imagens_ref["form_msg"])

        # Aguarda um tempo antes de iniciar
        time.sleep(espera)

        # LOCALIZA BOTÃO DE ANEXO
        posicao_anexar_imgs = Tools.ciclo_tentativa(
            funcao=Tools.localiza_imagem
            , args=([btn_anexar_img],)
            , limit=limit
            , step=step
            , descricao="BOTÃO ANEXO"
        )

        # CLICA NO BOTÃO DE ANEXO
        Tools.click(posicao=posicao_anexar_imgs)
        Tools.log_img(log_img=f"BOTAO_ANEXA_IMG_{lead}", canal=canal)

        time.sleep(0.5)

        # LOCALIZA BOTÃO FOTOS E VÍDEOS
        try:
            posicao_fotos_videos = Tools.ciclo_tentativa(
                funcao=Tools.localiza_imagem
                , args=([btn_fotos_videos],)
                , limit=limit
                , step=step
                , descricao="BOTÃO FOTOS E VIDEOS"
            )
        except Exception as e:
            print(f"Erro {e}")

        if not posicao_fotos_videos:
            print("BOTÃO 'FOTOS E VIDEOS' NÃO LOCALIZADO")

        Tools.log_img(log_img=f"BOTAO_FOTOS_VIDEOS_{lead}", canal=canal)
        for _ in range(2):
            Tools.click(posicao=posicao_fotos_videos)

        time.sleep(espera)
        # SELECIONA O FORMULARIO DE DIRETORIOS
        Tools.pressionar_tecla(tecla1="ctrl", tecla2="l")


        # LIMPA O FORMULARIO
        Tools.pressionar_tecla(tecla1="backspace")

        # ESCREVE E ACESSA O DIRETORIO
        Tools.log(msg=f"CONJUNTO CAMPANHA SELECIONADO {dir_img_db}", canal=canal)
        Tools.escreve(msg=dir_img_db, press_enter="yes")
        Tools.log_img(log_img=f"SELECAO_CONJUNTO_CAMPANHA_{lead}", canal=canal)

        time.sleep(espera)
        for _ in range(4):
            Tools.pressionar_tecla(tecla1="tab")

        time.sleep(espera)
        Tools.pressionar_tecla(tecla1="ctrl", tecla2="a", press_enter="yes")


        time.sleep(espera)
        pgui.press(keys="enter")
        time.sleep(5)
        """
        # LOCALIZA FORMULÁRIO DE MENSAGEM

        posicao = Img.localiza_imagem(lista_imgs=[form_msg])
        if not posicao:
            print("Formulário de mensagem não localizado.")
            sys.exit()

        for _ in range(2):
            pgui.click(x=posicao[0] + 150, y=posicao[1])  # Posiciona à direita do ponto alvo
        """

    @staticmethod
    def tm_mensagem():
        raiz_dir = dirs_ref["dir_tm_msg"]

        mensagem = ""
        num = random.randint(1, 7)

        for file in os.listdir(raiz_dir):

            if file == f"Frase{num}.txt":
                file_path = os.path.join(raiz_dir, file)

                with open(file_path, "r", encoding="utf-8") as f:
                    mensagem = f.read().strip()
                break

        return mensagem

    @staticmethod
    def localiza_imagem(lista_imgs, precisao=0.8, ):

        localizacao = None

        for img in lista_imgs:
            try:
                localizacao = pgui.locateOnScreen(img, confidence=precisao)
            except Exception as e:
                raise e
                #Logs.log_script(msg=f"Img.localiza_imagem | Erro ao localizar imagem  {img}| {e}")


            if localizacao:
                x = localizacao.left
                y = localizacao.top
                return [x, y]

        return None

    @staticmethod
    def valida_maximizacao(timeout=10):
        status = None
        janela = None

        for _ in range(timeout):
            try:
                janela = Desktop(backend="uia").window(title="WhatsApp")
                if janela.exists(timeout=1):
                    rect = janela.rectangle()
                    screen_width, screen_height = pgui.size()

                    # Considera maximizada se ocupa quase toda a tela e está no canto superior esquerdo
                    if (
                            abs(rect.width() - screen_width) < 20
                            and abs(rect.height() - screen_height) < 80
                            and rect.top <= 10
                            and rect.left <= 10
                    ):
                        status = 1
                        print("Maximizada")
                    else:
                        status = 0
                        print("Minimizada")
                    return status
            except Exception:
                time.sleep(1)

        print("Janela não encontrada.")
        return None

    @staticmethod
    def maximiza_janela(app_name_parcial):
        """
        Garante que a janela do aplicativo esteja maximizada (expandida).
        :param app_name_parcial: parte do nome da janela do app (ex: 'WhatsApp')
        """
        try:
            # Procura janelas que contenham o nome
            janelas = [win for win in gw.getWindowsWithTitle(app_name_parcial) if win.title]
            if not janelas:
                Tools.log(msg=f"Aplicativo '{app_name_parcial}' não encontrado.", canal=Tools.canal)
                return

            janela = janelas[0]
            if not janela.isMaximized:
                Tools.log(msg=f"Maximizando janela: {janela.title}", canal=Tools.canal)
                janela.maximize()
            else:
                Tools.log(msg=f"A janela '{janela.title}' já está maximizada.", canal=Tools.canal)
        except Exception as e:
            Tools.log(msg=f"Erro ao tentar maximizar janela: {e}", canal=Tools.canal)

    @staticmethod
    def ciclo_tentativa(funcao, args=(), kwargs=None, limit=10, step=1, descricao="objeto"):
        """
        Tenta executar uma função até 'limit' vezes com intervalo de 'step' segundos entre tentativas.

        :param funcao: função que será chamada
        :param args: argumentos posicionais da função
        :param kwargs: argumentos nomeados da função
        :param limit: número máximo de tentativas
        :param step: tempo de espera entre tentativas
        :param descricao: descrição do que está tentando localizar (para log)
        :return: resultado da função ou levanta exceção
        """
        if kwargs is None:
            kwargs = {}

        for tentativa in range(1, limit + 1):
            Tools.log(msg=f"TENTANDO LOCALIZAR {descricao} | TENTATIVA n° {tentativa}", canal=Tools.canal)

            try:
                resultado = funcao(*args, **kwargs)
                Tools.log(msg=f"IMAGEM LOCALIZADA", canal=Tools.canal)

                return resultado
            except Exception as e:
                Tools.log(msg=f"FALHA AO LOCALIZAR {descricao} | {e}", canal=Tools.canal)
                time.sleep(step)
        Tools.log(msg=f"NÃO FOI POSSIVEL LOZALIZAR {descricao} APÓS {limit} TENTATIVAS", canal=Tools.canal)

    @staticmethod
    def compara_com_tolerancia(bbox, caminho_referencia, threshold=0.97):

        # CAPTURA A REGIÃO DA TELA
        screenshot = pyautogui.screenshot(region=bbox)
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # LÊ A IMAGEM DE REFERÊNCIA
        ref = cv2.imread(caminho_referencia)
        if ref is None:
            print("Imagem de referência não encontrada.")
            return 0

        # VERIFICA TAMANHO
        if screenshot.shape[0] < ref.shape[0] or screenshot.shape[1] < ref.shape[1]:
            print("A captura é menor que a referência.")
            return 0

        # USA MATCH TEMPLATE COM CORRELAÇÃO NORMALIZADA
        resultado = cv2.matchTemplate(screenshot, ref, cv2.TM_CCOEFF_NORMED)
        max_val = np.max(resultado)

        # DEBUG opcional
        print(f"Similaridade: {max_val:.4f}")

        # RETORNA 1 SE SIMILAR O SUFICIENTE
        return 1 if max_val >= threshold else 0

    @staticmethod
    def garante_msg():
        loc = None
        time.sleep(2)
        try:
            loc = Tools.localiza_imagem(lista_imgs=[l])
            status = 1
        except Exception:
            status = 0
        if loc:
            for _ in range(3):
                pgui.click(loc[0], loc[1])
        else: raise Exception("Erro | imagem não localizada")

    @staticmethod
    def on_click():
        pos = pyautogui.position()
        print(f"{pos}")

    @staticmethod
    def monta_msg(cliente, msg_tm):



        Tools.log(msg=f"ACESSANDO FORMULARIO DE MENSAGEM", canal=Tools.canal)
        for i in range(5):
            pgui.click(x=x_formulario_msg, y=y_formulario_msg, button="left")

        Tools.log(msg=f"ESCREVENDO A MENSAGEM", canal=Tools.canal)
        pyperclip.copy(f"Olá, {cliente}! {msg_tm}")
        pgui.hotkey('ctrl', 'v')
        time.sleep(1)
        pgui.press("enter")
        time.sleep(2)

    @staticmethod
    def gera_print(dir_destino, nome_img):

        caminho_destino = os.path.join(dir_destino, nome_img)
        pyautogui.sleep(2)


        x, y = pyautogui.position()


        largura = 400
        altura = 50
        bbox = (950, 1015, 400, 45)

        print(f"Capturando área em: {bbox}")
        img = pyautogui.screenshot(region=bbox)
        img.save(f"{caminho_destino}.png")

    @staticmethod
    def valida_caixa_texto(cliente, msg_tm, lead):

        try:
            localizacao = pyautogui.locateOnScreen(img_form_msg, confidence=0.8)
            if localizacao:
                Tools.monta_msg(cliente=cliente, msg_tm=msg_tm)
                return 1
            else:
                return 0
                print("ERRO: FORMULARIO NÃO LOCALIZADO")
            return 1
        except pyautogui.ImageNotFoundException as e:
            return 0
            print(f"ERRO: FORMULARIO NÃO LOCALIZADO {e}")

    @staticmethod
    def log_img(log_img, canal, ativar=None):
        if ativar:

            try:
                # REALIZA CAPITURA DA TELA
                screenshot = pyautogui.screenshot()

                # SALVA A IMAGEM NO DIRETORIO DESTINO DOS LOGS
                screenshot.save(rf"{dir_log_imgs}\{log_img}_{time.strftime(f"%Y%m%d%H%M%S")}.png")

                Tools.log(msg=rf"Logs de imagem salvo com sucesso", canal=canal)
            except Exception as e:
                Tools.log(msg=f"Erro ao realizar log de imagem | {e}", canal=canal)

        pass



    @staticmethod
    def status_msg_ativo(x=650, y=250, largura=300, altura=400, caminho_ref=r"\\100.96.1.3\transfer\imgs_referencia\img_ref_sem_mensagem_ativa.png", limiar=0.99, save_teste=None):
        """
        FUNCAO PARA VALIDAR SE EXISTE MENSAGEM ATIVA NA CONVERSA COM O CLIENTEE
        AO ABRIR A CONVERSA, O LADO DO ROBO PRECISA ESTAR VAZIO
        :param x:
        :param y:
        :param largura:
        :param altura:
        :param caminho_ref:
        :param limiar:
        :return:
        """

        # Captura a região especificada
        screenshot = pyautogui.screenshot(region=(x, y, largura, altura))
        if save_teste:
            screenshot.save(r"\\100.96.1.3\transfer\imgs_referencia\testes\img_teste.png")
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

