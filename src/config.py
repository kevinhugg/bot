###############
## VARIAVEIS ##
###############
import os, random
from dotenv import load_dotenv
from enum import IntEnum
from datetime import timedelta

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# RAIZ ÚNICA
#DIR_RAIZ      = r"\\100.96.1.3"
#DIR_TRANSFER  = os.path.join(DIR_RAIZ, "transfer")
#DIR_RAIZ      = r"\\100.96.1.3"
#DIR_TRANSFER  = os.path.join(DIR_RAIZ, "transfer")
DIR_RAIZ = r"/"
DIR_TRANSFER = DIR_RAIZ


# DIRETORIOS DERIVADOS DA MESMA RAIZ
dir_projeto         = DIR_RAIZ
dir_transfer        = DIR_TRANSFER
dir_imgs_ref        = os.path.join(DIR_TRANSFER, "imgs_referencia")
dir_logs            = os.path.join(DIR_TRANSFER, "logs")
dir_logs_trans      = os.path.join(dir_logs, "log_transacional")
dir_logs_img        = os.path.join(dir_logs, "log_img")
dir_status_bots     = os.path.join(DIR_TRANSFER, "status_bots")

# DIRETORIOS OPERACIONAIS
dir_mailing         = os.path.join(DIR_TRANSFER, "mailing")
dir_dump_discagem   = os.path.join(DIR_TRANSFER, "dump_discagem")
dir_tm_imgs         = os.path.join(DIR_TRANSFER, r"tm\imgs")
dir_tm_msgs         = os.path.join(DIR_TRANSFER, r"tm\msgs")

# DIRETORIOS DE IMAGENS DE REFERENCIA - APENAS NOMES DAS IMAGENS
imagens_ref = {
    # PÁGINAS
    "tela_inicial": "whatsapp_tela_incial.png",
    "img_telefone_invalido": "telefone_invalido.png",

    # FORMULÁRIOS
    "form_msg": "form_mensagem.png",
    "form_pesquisa_cliente": "whatsapp_form_pesquisa_cliente.png",

    # BOTÕES
    "btn_anexar_img": "btn_anexar_img.png",
    "btn_fotos_videos": "btn_fotos_videos.png",
}


dirs_ref = {
    "dir_tm_msg":  dir_tm_msgs,
    "dir_img_ref": dir_imgs_ref,
}


raiz             = dir_transfer
raiz_projeto     = dir_transfer
raiz_status      = dir_status_bots
raiz_logs        = dir_logs_trans
raiz_log_imgs    = dir_logs_img


l               = os.path.join(dir_imgs_ref, imagens_ref["form_msg"])
img_form_msg    = l

# COORDENADAS DA TELA
x_formulario_msg = 615
y_formulario_msg = 707



#STATUS DE MENSAGENS (PRINTS)

##CAMINHOS DOS PRINTS
IMG_SENT_1TICK      = r"C:\BW\prints\one_check.png"         # 1 = Apenas enviada
IMG_DELIV_2TICKS    = r"C:\BW\prints\two_checks.png"   # 2 = Entregue
IMG_READ_2BLUE      = r"C:\BW\prints\blue_checks.png"         # 3 = Lida

#Região que ele vai olhar para comparar
STATUS_REGION       = (1670, 950, 35, 35)

#SENSIBILIDADE DA COMPARAÇÃO
MATCH_THRESHOLD     = 0.80

class MsgState(IntEnum):
    NOT_DELIVERED  = 0  # Sem ticks visíveis
    SENT           = 1  # 1 tick
    DELIVERED      = 2  # 2 ticks
    READ           = 3  # 2 ticks azuis

class Feedback(IntEnum):
    NONE           = 0
    NEGATIVE       = 1
    POSITIVE       = 2
    NOT_SEEN       = 3

#POLÍTICAS DE RECHECAGEM/BAN-SAFE
UNREAD_NEGATIVE_AFTER       = timedelta(days=14)
MAX_UNDELIVERED_ATTEMPTS    = 2
COOLDOWN_NEGATIVE_MIN_DAYS  = 30
COOLDOWN_NEGATIVE_MAX_DAYS  = 60


#randomiza os dias de FREEZE
def get_random_freeze_days():
    """Retorna um cooldown aleatório entre os limites estabelecidos"""
    return random.randint(COOLDOWN_NEGATIVE_MIN_DAYS, COOLDOWN_NEGATIVE_MAX_DAYS)