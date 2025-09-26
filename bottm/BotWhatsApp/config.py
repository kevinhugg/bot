###############
## VARIAVEIS ##
###############
import os, random
from dotenv import load_dotenv
from enum import IntEnum
from datetime import timedelta
import socket

# ===============================
# 🔧 Carrega .env
# ===============================
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Sempre define os DB_* (com fallback se não tiver no .env)
DB_USER = os.getenv("PGUSER", "postgres.cektludugzbdpwbanqrf")
DB_PASS = os.getenv("PGPASSWORD", "1234Strass#$%")
DB_HOST = os.getenv("PGHOST", "aws-1-sa-east-1.pooler.supabase.com")
DB_PORT = os.getenv("PGPORT", "6543")
DB_NAME = os.getenv("PGDATABASE", "postgres")

try:
    ipv4_host = socket.gethostbyname(DB_HOST)
    print(f"🔧 Host resolvido para IPv4: {ipv4_host}")
    DB_HOST = ipv4_host
except Exception as e:
    print("⚠️ Falha ao resolver host em IPv4:", e)

# Recria DATABASE_URL usando IPv4 fixo
DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"
)

# ===============================
# 🔧 Diretórios principais
# ===============================
DIR_RAIZ = r"C:\BW\transfer-2"
DIR_TRANSFER = DIR_RAIZ

dir_projeto         = DIR_RAIZ
dir_transfer        = DIR_TRANSFER
dir_imgs_ref        = os.path.join(DIR_TRANSFER, "imgs_referencia")
dir_logs            = os.path.join(DIR_TRANSFER, "logs")
dir_logs_trans      = os.path.join(dir_logs, "log_transacional")
dir_logs_img        = os.path.join(dir_logs, "log_img")
dir_status_bots     = os.path.join(DIR_TRANSFER, "status_bots")

dir_mailing         = os.path.join(DIR_TRANSFER, "mailing")
dir_dump_discagem   = os.path.join(DIR_TRANSFER, "dump_discagem")
dir_tm_imgs         = os.path.join(DIR_TRANSFER, r"tm\imgs")
dir_tm_msgs         = os.path.join(DIR_TRANSFER, r"tm\msgs")

# ===============================
# 🔧 Imagens de referência
# ===============================
imagens_ref = {
    "tela_inicial": "whatsapp_tela_incial.png",
    "img_telefone_invalido": "telefone_invalido.png",
    "form_msg": "form_mensagem.png",
    "form_pesquisa_cliente": "whatsapp_form_pesquisa_cliente.png",
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

# ===============================
# 🔧 Coordenadas / Prints
# ===============================
x_formulario_msg = 615
y_formulario_msg = 707

IMG_SENT_1TICK   = r"C:\BW\prints\one_check.png"
IMG_DELIV_2TICKS = r"C:\BW\prints\two_checks.png"
IMG_READ_2BLUE   = r"C:\BW\prints\blue_checks.png"

STATUS_REGION    = (1670, 950, 35, 35)
MATCH_THRESHOLD  = 0.80

# ===============================
# 🔧 Estados de mensagem
# ===============================
class MsgState(IntEnum):
    NOT_DELIVERED  = 0
    SENT           = 1
    DELIVERED      = 2
    READ           = 3

class Feedback(IntEnum):
    NONE           = 0
    NEGATIVE       = 1
    POSITIVE       = 2
    NOT_SEEN       = 3

# ===============================
# 🔧 Políticas de rechecagem
# ===============================
UNREAD_NEGATIVE_AFTER       = timedelta(days=14)
MAX_UNDELIVERED_ATTEMPTS    = 2
COOLDOWN_NEGATIVE_MIN_DAYS  = 30
COOLDOWN_NEGATIVE_MAX_DAYS  = 60

def get_random_freeze_days():
    return random.randint(COOLDOWN_NEGATIVE_MIN_DAYS, COOLDOWN_NEGATIVE_MAX_DAYS)
