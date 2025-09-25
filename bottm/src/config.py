import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente de um arquivo .env
load_dotenv()

# --- Configuração do Banco de Dados ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida. Crie um arquivo .env e adicione a variável.")

# --- Estrutura de Diretórios (Portátil) ---
# A raiz do projeto é definida dinamicamente.
# Assumindo que config.py está em `bottm/BotWhatsApp/`, subimos 2 níveis.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Diretórios Principais ---
# O usuário irá criar estas pastas, o código apenas as referencia.
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"

# --- Caminhos para Ativos (Imagens, Templates) ---
IMG_REF_DIR = ASSETS_DIR / "imgs_referencia"
PRINTS_DIR = ASSETS_DIR / "prints"  # Para os prints de status (1-tick, 2-ticks)
TM_DIR = ASSETS_DIR / "tm"
TM_IMGS_DIR = TM_DIR / "imgs"
TM_MSGS_DIR = TM_DIR / "msgs"

# --- Caminhos para Dados (Logs) ---
LOGS_DIR = DATA_DIR / "logs"
LOGS_IMG_DIR = LOGS_DIR / "log_img"
LOGS_TRANS_DIR = LOGS_DIR / "log_transacional"

# Garante que os diretórios de log existam para evitar erros de escrita.
LOGS_IMG_DIR.mkdir(parents=True, exist_ok=True)
LOGS_TRANS_DIR.mkdir(parents=True, exist_ok=True)

# --- Verificação de Sanidade (Opcional, mas útil para depuração) ---
# print(f"Raiz do projeto: {PROJECT_ROOT}")
# print(f"Diretório de logs: {LOGS_DIR}")
# print(f"Diretório de imagens de referência: {IMG_REF_DIR}")