from enum import IntEnum
from datetime import timedelta

# --- Lógica de Negócios e Regras ---
UNREAD_NEGATIVE_AFTER = timedelta(days=14)
MAX_UNDELIVERED_ATTEMPTS = 2
COOLDOWN_NEGATIVE_MIN_DAYS = 30
COOLDOWN_NEGATIVE_MAX_DAYS = 60

# --- Enums para Status e Feedback ---
class MsgState(IntEnum):
    """Define os estados de uma mensagem enviada."""
    NOT_DELIVERED = 0  # Sem ticks visíveis
    SENT = 1           # 1 tick cinza
    DELIVERED = 2      # 2 ticks cinzas
    READ = 3           # 2 ticks azuis

class Feedback(IntEnum):
    """Define o tipo de feedback de uma mensagem."""
    NONE = 0
    NEGATIVE = 1
    POSITIVE = 2
    NOT_SEEN = 3

# --- Constantes de Automação de UI ---
# Limiar de confiança para reconhecimento de imagem.
MATCH_THRESHOLD = 0.80

# Coordenadas e regiões podem ser definidas aqui se forem fixas,
# ou movidas para a classe de automação se forem mais específicas.
# Por enquanto, vou mantê-las aqui para referência, mas a prática
# ideal seria movê-las para a classe `WhatsappAutomator`.
STATUS_REGION = (1670, 950, 35, 35)
X_FORMULARIO_MSG = 615
Y_FORMULARIO_MSG = 707

# Nomes de arquivos de imagem de referência, para evitar "strings mágicas" no código.
IMAGENS_REF = {
    "TELA_INICIAL": "whatsapp_tela_incial.png",
    "TELEFONE_INVALIDO": "telefone_invalido.png",
    "FORM_MSG": "form_mensagem.png",
    "FORM_PESQUISA_CLIENTE": "whatsapp_form_pesquisa_cliente.png",
    "BTN_ANEXAR_IMG": "btn_anexar_img.png",
    "BTN_FOTOS_VIDEOS": "btn_fotos_videos.png",
    "IMG_REF_SEM_MENSAGEM": "img_ref_sem_mensagem_ativa.png",
    "TICK_SENT": "one_check.png",
    "TICKS_DELIVERED": "two_checks.png",
    "TICKS_READ": "blue_checks.png",
}