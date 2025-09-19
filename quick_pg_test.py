from db import get_conn

with get_conn() as conn, conn.cursor() as cur:
    cur.execute("select current_user, inet_server_addr(), inet_server_port()")
    print(cur.fetchone())