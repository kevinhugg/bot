import re
import pandas as pd
from MainClass import Tools  # usa seu loader do mailing

def so_digitos(s): 
    return re.sub(r"\D+", "", str(s or ""))

def normaliza_e164(br):
    br = so_digitos(br)
    # remove 0/0XX de operadora no começo
    br = re.sub(r"^0\d{2}", "", br)
    if not br.startswith("55"):
        br = "55" + br
    return br

def corrige_numero(e164):
    e164 = normaliza_e164(e164)
    if len(e164) < 7: 
        return e164, "INVALIDO_CURTO"
    ddd = e164[2:4]
    local = e164[4:]
    # Regra 1: remover 9 indevido em fixo (9 + [2-5] + 7 dígitos)
    if len(local) == 9 and local[0] == "9" and local[1] in "2345":
        return "55" + ddd + local[1:], "REMOVER_9_FIXO"
    # Regra 2: adicionar 9 em celular sem 9 (8 dígitos iniciando 6-9)
    if len(local) == 8 and local[0] in "6789":
        return "55" + ddd + "9" + local, "ADICIONAR_9_CEL"
    # Mantém
    return e164, "OK"

# Leia seu mailing pelo Tools (mantém seu fluxo)
canal = "teste"  # ajuste para o canal que estiver usando
df = Tools.mailing(canal=canal).copy()

# normaliza, corrige e marca
df["Telefone_Limpo"] = df["Telefone"].apply(normaliza_e164)
corrigidos = df["Telefone_Limpo"].apply(corrige_numero)
df["Telefone_Corrigido"] = [t for t,flag in corrigidos]
df["Flag_Correcao"] = [flag for t,flag in corrigidos]

# Classificação: tem 9 após DDD?
df["Tem_9_Apos_DDD"] = df["Telefone_Corrigido"].str[4].eq("9")

df.to_excel("mailing_corrigido.xlsx", index=False)
print("Gerado: mailing_corrigido.xlsx")
