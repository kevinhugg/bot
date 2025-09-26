# etl_txt_para_pg.py
import os, csv, re, sys, argparse
import p

sycopg
from datetime import datetime
from psycopg.rows import tuple_row


# ========= CONFIG =========
DEVICES = ["lua", "cosmo", "terra", "estrela", "sol", "teste"]

BASE_DIR   = r"C:\BW\transfer-2"
STATUS_DIR = os.path.join(BASE_DIR, "status_bots")           # status\status_<device>.txt
DISC_DIR   = os.path.join(BASE_DIR, "dump_discagem")    # dump_discagem\discagem_<device>.txt
MAIL_DIR   = os.path.join(BASE_DIR, "mailing")          # mailing\mailing_<device>.txt

# Conexão: use o pooler (6543) com usuario COM sufixo. Se sua rede bloquear, troque para o bloco comentado (direto 5432).
PG = dict(
    host="aws-1-sa-east-1.pooler.supabase.com",
    port=6543,
    user="postgres.cektludugzbdpwbanqrf",   # COM sufixo do projeto
    password="1234Strass#$%",              # <<< TROQUE
    dbname="postgres",
    sslmode="require",
    connect_timeout=10
)

# PG = dict(
#     host="db.szzmhhpnfqojuvhftkjr.supabase.co",
#     port=5432,
#     user="postgres",                        # SEM sufixo
#     password="SUA_SENHA_AQUI",
#     dbname="postgres",
#     sslmode="require",
#     connect_timeout=10
# )

# ========= UTILS =========
def log(*a): print(*a)

def norm_phone(p):
    p = re.sub(r"\D+", "", p or "")
    if not p: return ""
    return p if p.startswith("55") else ("55" + p)

def parse_datetime(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try: return datetime.strptime(s, fmt)
        except ValueError: pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try: return datetime.strptime(s, fmt)
        except ValueError: pass
    return datetime.now()

def ensure_schema(conn):
    with conn.cursor() as cur:
        cur.execute("""
        create table if not exists mailing (
          id bigserial primary key,
          device text not null default 'default',
          cliente text,
          telefone text not null,
          unique (device, telefone)
        );
        create table if not exists discagem (
          id bigserial primary key,
          datadiscagem timestamptz not null,
          telefone text not null,
          canal text not null,
          status int not null,
          created_at timestamptz default now()
        );
        create table if not exists status_bot (
          canal text primary key,
          status int not null
        );
        create index if not exists idx_discagem_canal_tel on discagem(canal, telefone);
        """)
    log("✓ Schema OK")

# ========= STATUS =========
def read_status_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            txt = f.read().strip().lower()
        m = re.search(r"(\d+)", txt)
        if m: return 1 if int(m.group(1)) != 0 else 0
        if "inativo" in txt: return 0
        return 1
    except Exception:
        return None

def import_status(conn):
    log("▶ Importando STATUS…")
    total = 0
    for dev in DEVICES:
        p = os.path.join(STATUS_DIR, f"status_{dev}.txt")
        st = read_status_file(p) if os.path.isfile(p) else 1
        with conn.cursor() as cur:
            cur.execute("""
                insert into status_bot (canal, status)
                values (%s, %s)
                on conflict (canal) do update set status = excluded.status
            """, (dev, int(st)))
        log(f"  ✓ status_bot[{dev}] = {st} {'(arquivo)' if os.path.isfile(p) else '(default)'}")
        total += 1
    conn.commit()
    log(f"✓ Status finalizados ({total})")

# ========= DISCAGEM =========
def import_discagem_file(conn, dev, path):
    if not os.path.isfile(path):
        log(f"  … sem arquivo para {dev}: {path}")
        return 0
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        if not reader.fieldnames:
            log(f"  … cabeçalho ausente: {path}")
            return 0
        cols = {c.lower(): c for c in reader.fieldnames}
        c_data = cols.get("data") or cols.get("datadiscagem") or cols.get("datahora") or cols.get("data_hora")
        c_tel  = cols.get("telefone") or cols.get("tel")
        c_st   = cols.get("status")
        if not c_data or not c_tel:
            log(f"  … cabeçalho insuficiente (precisa Data/Datadiscagem e Telefone): {path}")
            return 0
        rows = []
        for r in reader:
            d  = parse_datetime(r.get(c_data))
            tl = norm_phone(r.get(c_tel))
            st = r.get(c_st)
            try: st = int(st)
            except Exception: st = 1
            if tl: rows.append((d, tl, dev, st))
    if not rows:
        log(f"  … nenhum registro válido em {path}")
        return 0
    with conn.cursor() as cur:
        for row in rows:
            cur.execute(
                "insert into discagem (datadiscagem, telefone, canal, status) values (%s, %s, %s, %s)",
                row
            )

    log(f"  ✓ discagem[{dev}]: +{len(rows)}")
    return len(rows)

def import_discagem(conn):
    log("▶ Importando DISCAGEM…")
    total = 0
    for dev in DEVICES:
        p = os.path.join(DISC_DIR, f"discagem_{dev}.txt")
        total += import_discagem_file(conn, dev, p)
    conn.commit()
    log(f"✓ Discagem total: {total}")

# ========= MAILING =========
def import_mailing_file(conn, dev, path):
    if not os.path.isfile(path):
        log(f"  … sem arquivo para {dev}: {path}")
        return 0

    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        if not reader.fieldnames or "Cliente" not in reader.fieldnames or "Telefone" not in reader.fieldnames:
            log(f"  … cabeçalho esperado: Cliente;Telefone  → {path}")
            return 0
        for r in reader:
            cliente = (r.get("Cliente") or "").strip()
            tel = norm_phone(r.get("Telefone"))
            if tel:
                rows.append((cliente, tel, dev))  # <<< agora inclui device

    if not rows:
        log(f"  … nenhum registro válido em {path}")
        return 0

    with conn.cursor(row_factory=tuple_row) as cur:
        cur.executemany("""
            insert into mailing (cliente, telefone, device)
            values (%s, %s, %s)
            on conflict (device, telefone) do update set cliente = excluded.cliente
        """, rows)

    log(f"  ✓ mailing[{dev}]: +{len(rows)} (upsert)")
    return len(rows)

def import_mailing(conn):
    log("▶ Importando MAILING…")
    total = 0
    for dev in DEVICES:
        p = os.path.join(MAIL_DIR, f"mailing_{dev}.txt")
        total += import_mailing_file(conn, dev, p)
    conn.commit()
    log(f"✓ Mailing total: {total}")

# ========= MAIN =========
def main():
    os.makedirs(STATUS_DIR, exist_ok=True)
    os.makedirs(DISC_DIR,   exist_ok=True)
    os.makedirs(MAIL_DIR,   exist_ok=True)

    ap = argparse.ArgumentParser(description="ETL de TXT → Postgres (status, discagem, mailing)")
    ap.add_argument("--status",   action="store_true", help="importar status_bot")
    ap.add_argument("--discagem", action="store_true", help="importar discagem")
    ap.add_argument("--mailing",  action="store_true", help="importar mailing")
    args = ap.parse_args()
    run_all = not (args.status or args.discagem or args.mailing)

    with psycopg.connect(**PG) as conn:
        ensure_schema(conn)
        if args.status or run_all:   import_status(conn)
        if args.discagem or run_all: import_discagem(conn)
        if args.mailing or run_all:  import_mailing(conn)

    log("🏁 ETL concluído.")

if __name__ == "__main__":
    main()
