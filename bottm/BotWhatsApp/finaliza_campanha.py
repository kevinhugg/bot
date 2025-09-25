from db import get_conn
from bot_leads import set_status, decide_next_status, now_iso

def finalizar_campanha(canal: str):
    """
    Revisão final da campanha:
    percorre discados_{canal} e atualiza lead_status.
    """
    canal = canal.lower()
    updated = 0

    with get_conn() as conn, conn.cursor() as cur:
        # pega todos os discados desse canal
        cur.execute("""
            select telefone, status, coalesce(resposta, '') as resposta
              from discados
             where canal = %s
        """, (canal,))
        rows = cur.fetchall()

        for tel, status, resposta in rows:
            # regra de decisão
            if status == 3:  # inválido/bloqueado
                novo = "🚫 Bloqueado"
            elif "🧿" in (resposta or ""):  # já marcado cliente
                novo = "💎 Cliente 🧿"
            elif resposta and resposta.strip():
                novo = "💎 Cliente 🧿"      # respondeu → cliente
            elif status == 1:  # enviado
                novo = "🔮 Engajado"        # quente
            elif status == 2:  # entregue mas não lido
                novo = "❄️ Frio"
            else:
                novo = "🌙 Neutro"

            # atualiza lead_status
            old = None
            try:
                cur.execute("select status from lead_status where telefone=%s", (tel,))
                r = cur.fetchone()
                if r:
                    old = r[0]
            except Exception:
                pass

            final = decide_next_status(old, novo)
            set_status(conn, tel, final)

            # log em lead_events
            cur.execute("""
                insert into lead_events (telefone, evento, detalhe, criado_em)
                values (%s, %s, %s, now())
            """, (tel, "final_campanha", f"{status}->{final}"))

            updated += 1

        conn.commit()

    print(f"✓ Campanha {canal} revisada. {updated} contatos atualizados.")
