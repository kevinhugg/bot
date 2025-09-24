import psycopg

try:
    conn = psycopg.connect(
        host="aws-1-sa-east-1.pooler.supabase.com",
        port=6543,
        user="postgres.cektludugzbdpwbanqrf",   # ⚠️ pegue do painel do Supabase
        password="1234Strass#$%",   # ⚠️ pegue do painel do Supabase
        dbname="postgres"
    )
    cur = conn.cursor()
    cur.execute("select now()")
    print("✅ Conexão OK:", cur.fetchone())
    conn.close()
except Exception as e:
    print("❌ Erro:", e)
