import json
from db import get_conn, ensure_lead_status_table
from typing import Optional
from services.phone_utils import normaliza_e164
from config import ASSETS_DIR
import os


# Carrega o fluxo de um arquivo JSON para flexibilidade.
def load_flux():
    flux_path = os.path.join(ASSETS_DIR, "flux.json")
    try:
        with open(flux_path, "r", encoding="utf-8") as f:
            return json.load(f).get("fluxo", {})
    except FileNotFoundError:
        # Retorna um fluxo padrão se o arquivo não existir.
        return {
            "novo_lead": ["🌙 Neutro", "🔮 Engajado", "❄️ Frio", "🚫 Bloqueado"],
            "🌙 Neutro": ["🔮 Engajado", "❄️ Frio"],
            "❄️ Frio": ["🔮 Engajado", "📦 Arquivado"],
            "🔮 Engajado": ["💎 Cliente", "🚫 Bloqueado"],
        }


FLUX = load_flux()

# Mapeia o status técnico da mensagem para um status de negócio.
STATE_TO_STATUS = {
    "READ": "🔮 Engajado",
    "DELIVERED": "🔮 Engajado",
    "SENT": "❄️ Frio",
    "NOT_DELIVERED": "❄️ Frio",
    "NOT_FOUND": "🌙 Neutro",
}


class LeadService:
    """
    Serviço para gerenciar o ciclo de vida e o status dos leads.
    """

    def __init__(self):
        # Garante que as tabelas necessárias existam no início.
        ensure_lead_status_table()

    def get_current_status(self, telefone: str) -> Optional[str]:
        """Busca o status atual de um lead no banco de dados."""
        telefone_norm = normaliza_e164(telefone)
        query = "SELECT status FROM lead_status WHERE telefone = %s"
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(query, (telefone_norm,))
                r = cur.fetchone()
                return r[0] if r else None
        except Exception as e:
            print(f"[LeadService] Erro ao buscar status: {e}")
            return None

    def _set_status(self, telefone: str, status: str):
        """Define ou atualiza o status de um lead no banco de dados."""
        telefone_norm = normaliza_e164(telefone)
        query = """
                INSERT INTO lead_status (telefone, status, atualizado_em)
                VALUES (%s, %s, NOW()) ON CONFLICT (telefone) DO \
                UPDATE \
                    SET status = EXCLUDED.status, \
                    atualizado_em = EXCLUDED.atualizado_em \
                """
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(query, (telefone_norm, status))
        except Exception as e:
            print(f"[LeadService] Erro ao definir status: {e}")

    def _decide_next_status(self, old_status: Optional[str], target_status: str) -> str:
        """Decide o próximo status com base no fluxo definido."""
        if not old_status:
            return target_status or "🌙 Neutro"

        if target_status == old_status:
            return old_status

        allowed_transitions = FLUX.get(old_status, [])
        if target_status in allowed_transitions:
            return target_status

        # Regra de fallback: se o alvo for "Engajado", permite a transição.
        if target_status == "🔮 Engajado":
            return target_status

        return old_status  # Mantém o status antigo se a transição não for permitida

    def on_send(self, telefone: str):
        """
        Chamado quando uma mensagem é enviada para um lead.
        Se for um novo lead, define seu status inicial.
        """
        telefone_norm = normaliza_e164(telefone)
        current_status = self.get_current_status(telefone_norm)
        if not current_status:
            self._set_status(telefone_norm, "🌙 Neutro")

    def on_check(self, telefone: str, detected_state: str):
        """
        Chamado após verificar o status de uma mensagem (lida, entregue, etc.).
        Atualiza o status do lead de acordo com o fluxo.
        """
        telefone_norm = normaliza_e164(telefone)
        mapped_target = STATE_TO_STATUS.get(detected_state, "🌙 Neutro")

        old_status = self.get_current_status(telefone_norm)
        new_status = self._decide_next_status(old_status, mapped_target)

        if old_status != new_status:
            self._set_status(telefone_norm, new_status)
            print(f"[LeadService] Status de {telefone_norm} atualizado de '{old_status}' para '{new_status}'.")