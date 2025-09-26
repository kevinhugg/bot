# bot_leads.py
import json
import os
from datetime import datetime, timezone
from typing import Optional

from db import get_conn, ensure_lead_status_table

BASE_DIR = os.path.dirname(__file__)
FLUX_PATH = os.path.join(BASE_DIR, "flux.json")
CLIENTES_JSON = os.path.join(BASE_DIR, "clientes.json")


def load_flux(path=FLUX_PATH):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("fluxo", {})
    except Exception:
        return {
            "novo_lead": ["🌙 Neutro", "🔮 Engajado", "❄️ Frio", "🚫 Bloqueado"],
            "🌙 Neutro": ["🔮 Engajado", "❄️ Frio"],
            "❄️ Frio": ["🔮 Engajado", "📦 Arquivado"],
            "🔮 Engajado": ["💎 Cliente", "🚫 Bloqueado"],
            "💎 Cliente": ["(sai do mailing)"],
            "🚫 Bloqueado": ["(não recebe mais campanhas)"],
        }


FLUX = load_flux()
ensure_lead_status_table()


STATE_TO_STATUS = {
    "READ": "🔮 Engajado",
    "DELIVERED": "❄️ Frio",
    "SENT": "❄️ Frio",
    "NOT_DELIVERED": "🌙 Neutro",
    "NOT_FOUND": "🌙 Neutro",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def normalize_phone(tel: str) -> str:
    if not tel:
        return tel
    t = "".join([c for c in tel if c.isdigit()])
    if not t.startswith("55"):
        t = "55" + t
    return t


def get_current_status(conn, telefone: str) -> Optional[str]:
    telefone = normalize_phone(telefone)
    with conn.cursor() as cur:
        cur.execute("select status from lead_status where telefone=%s", (telefone,))
        r = cur.fetchone()
        return r[0] if r else None


def set_status(conn, telefone: str, status: str):
    telefone = normalize_phone(telefone)
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into lead_status (telefone, status, atualizado_em)
            values (%s, %s, now())
            on conflict (telefone) do update
              set status = excluded.status,
                  atualizado_em = excluded.atualizado_em
        """,
            (telefone, status),
        )


def decide_next_status(old: Optional[str], target: str) -> str:
    if not old:
        return target or "🌙 Neutro"

    if target == old:
        return old

    nexts = FLUX.get(old, [])
    if target in nexts:
        return target

    if target == "🔮 Engajado":
        return target

    return old


def lead_on_send(canal: str, telefone: str):
    telefone = normalize_phone(telefone)
    with get_conn() as conn:
        cur_status = get_current_status(conn, telefone)
        if not cur_status:
            set_status(conn, telefone, "🌙 Neutro")
        try:
            _ensure_clientes_json()
            _upsert_clientes_json(telefone, status="🌙 Neutro", origem=canal)
        except Exception:
            pass


def lead_on_check(telefone: str, detected_state: str, score: float = 0.0):
    telefone = normalize_phone(telefone)
    mapped_target = STATE_TO_STATUS.get(detected_state, "🌙 Neutro")

    with get_conn() as conn:
        old = get_current_status(conn, telefone)
        new = decide_next_status(old, mapped_target)
        set_status(conn, telefone, new)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into lead_events (telefone, evento, detalhe, criado_em)
                    values (%s, %s, %s, now())
                """,
                    (telefone, f"check:{detected_state}", f"score={score}"),
                )
        except Exception:
            pass

    try:
        _ensure_clientes_json()
        _upsert_clientes_json(telefone, status=new)
    except Exception:
        pass


def _ensure_clientes_json(path=CLIENTES_JSON):
    if not os.path.isfile(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"clientes": []}, f, ensure_ascii=False, indent=2)


def _load_clientes_json(path=CLIENTES_JSON):
    _ensure_clientes_json(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("clientes", [])


def _save_clientes_json(clientes, path=CLIENTES_JSON):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"clientes": clientes}, f, ensure_ascii=False, indent=2)


def _upsert_clientes_json(telefone, status=None, nome=None, origem=None):
    telefone = normalize_phone(telefone)
    clientes = _load_clientes_json()
    found = False
    for c in clientes:
        if c.get("telefone") == telefone:
            if status:
                c["status"] = status
            if origem:
                c["origem"] = origem
            c["ultima_atualizacao"] = now_iso()
            found = True
            break
    if not found:
        clientes.append(
            {
                "telefone": telefone,
                "nome": nome or f"Cliente {len(clientes)+1}",
                "status": status or "🌙 Neutro",
                "origem": origem or "bot",
                "interacoes": 0,
                "ultima_atualizacao": now_iso(),
            }
        )
    _save_clientes_json(clientes)
