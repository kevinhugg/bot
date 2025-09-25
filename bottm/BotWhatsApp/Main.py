# IMPORTAÇÕES DOS MÓDULOS PERSONALIZADOS
from MainClass import *
import sys
from datetime import datetime, timezone
from config import *
from finaliza_campanha import finalizar_campanha

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

##### FUNÇÕES DE RECHECAGEM
def classificar_feedback(state, sent_at):
    """
    Classifica o feedback de um envio com base no estado atual e no tempo.
    """

    if state == MsgState.READ:
        return Feedback.POSITIVE, "Mensagem lida."

    return Feedback.NOT_SEEN, "Mensagem ainda não lida."

def precisa_reenviar(state, attempts):
    """
    Decide se precisa reenviar:

    - Só reenvia se não entregue
    - Até o limite definido em MAX_UNDELIVERED_ATTEMPTS
    """

    return state == MsgState.NOT_DELIVERED and attempts < MAX_UNDELIVERED_ATTEMPTS



# DEFINIÇÃO DO CANAL E VARIÁVEIS DE CONTROLE
canal = "teste" #colocar o terra depois
spins = 1 #mudar para 300 depois
spins = 1 if canal != "teste" else spins
n = 0
sleep_geral = 2

# DIRETÓRIO DE REFERÊNCIA DAS IMAGENS
raiz_dir = dirs_ref["dir_img_ref"]

# CAMINHOS DAS IMAGENS DE REFERÊNCIA
img_telefone_invalido = os.path.join(raiz_dir, imagens_ref["img_telefone_invalido"])
img_form_msg = os.path.join(raiz_dir, imagens_ref["form_msg"])

# SETA CONTEXTO DO TOOLS (CANAL)
Tools.canal = canal
Tools.log(msg="INICIALIZAÇÃO DO PROCESSO | DEFININDO CANAL E VARIÁVEIS", canal=canal)

# ATUALIZA STATUS DO BOT PARA ATIVO (PRÉ-CHECAGEM)
Tools.log(msg="ATUALIZANDO STATUS DO BOT PARA ATIVO (PRÉ-CHECAGEM)", canal=canal)
Tools.altera_status_bot(novo_status=1, canal=canal)

# ATUALIZA STATUS DO BOT PARA ATIVO (GARANTIA)
Tools.log(msg="REFORÇANDO STATUS DO BOT PARA ATIVO (GARANTIA)", canal=canal)
Tools.altera_status_bot(novo_status=1, canal=canal)

# INÍCIO DO LOOP PRINCIPAL
Tools.log(msg="INICIANDO LOOP PRINCIPAL", canal=canal)
while True:

    # ###########################
    # VALIDAÇÕES DE EXECUÇÃO
    # ###########################
    Tools.log(msg="VALIDANDO STATUS DO BOT", canal=canal)
    status_robo = Tools.valida_status_bot(canal=canal)
    if status_robo != 1:
        Tools.log(msg=f"ROBO {canal} INATIVO | STATUS ATUAL: {status_robo} | ENCERRANDO", canal=canal)
        sys.exit()

    try:
        # ###########################
        # CARGA DE MAILING
        # ###########################
        Tools.log(msg="LENDO MAILING E APLICANDO FILTROS (DISCAGENS JÁ REALIZADAS)", canal=canal)
        df_mailing = Tools.mailing(canal=canal)
        Tools.log(msg=f"MAILING CARREGADO | TOTAL REGISTROS: {len(df_mailing)}", canal=canal)

        # --- próximo ao topo, imports se necessário ---
        from db import get_conn


        # -------------------------------------------

        # Dentro do while (logo antes de Tools.mailing)
        class Chip:
            def __init__(self, canal):
                self.canal = canal
                # métricas iniciais; serão recalculadas a cada run
                self.feedback_negativo = 0  # respostas negativas / reclamações
                self.bounce_rate = 0.0  # % telefones inválidos (bounce)
                self.taxa_resposta = 0.0  # respostas / tentativas
                self.tempo_atividade = 0  # dias/meses desde início
                self.nivel_reputacao = 1  # valor inicial (1..5)
                self.sem_resposta = 0  # mensagens sem resposta (consecutivas)

            def load_from_db(self):
                """Popula métricas com queries reais (exemplos abaixo)."""
                try:
                    with get_conn() as conn, conn.cursor() as cur:
                        # total tentativas (ultimas N dias)
                        cur.execute("""
                                    select count(*)
                                    from discados
                                    where canal = %s
                                      and datadiscagem >= now() - interval '7 days'
                                    """, (self.canal,))
                        tentativas = cur.fetchone()[0] or 0

                        # respostas (ex: status = 1 => sucesso / resposta)
                        cur.execute("""
                                    select count(*)
                                    from discados
                                    where canal = %s
                                      and status = 1
                                      and datadiscagem >= now() - interval '7 days'
                                    """, (self.canal,))
                        respostas = cur.fetchone()[0] or 0

                        # invalido (status=3 por exemplo)
                        cur.execute("""
                                    select count(*)
                                    from discados
                                    where canal = %s
                                      and status = 3
                                      and datadiscagem >= now() - interval '7 days'
                                    """, (self.canal,))
                        invalidos = cur.fetchone()[0] or 0

                        # feedback negativo (pode ser outro evento/coluna; se não existir, usar invalidos como proxy)
                        cur.execute("""
                                    select sum(coalesce(feedback_negativo, 0))
                                    from canal_feedback
                                    where canal = %s
                                      and created_at >= now() - interval '7 days'
                                    """, (self.canal,))
                        fb_neg = cur.fetchone()[0] or 0

                    # calcula métricas
                    self.taxa_resposta = (respostas / tentativas) if tentativas else 0.0
                    self.bounce_rate = (invalidos / tentativas * 100.0) if tentativas else 0.0
                    self.feedback_negativo = fb_neg
                    self.sem_resposta = max(0, tentativas - respostas)  # simples proxy
                    # tempo_atividade e nivel_reputacao você pode buscar em status_bot.reputacao
                    try:
                        with get_conn() as conn, conn.cursor() as cur:
                            cur.execute("select reputacao from status_bot where canal=%s", (self.canal,))
                            r = cur.fetchone()
                            if r:
                                self.nivel_reputacao = int(r[0])
                    except Exception:
                        pass

                except Exception as e:
                    Tools.log(msg=f"[Chip.load_from_db] erro: {e}", canal=self.canal)


        # --- dentro do loop ---
        chip = Chip(canal)
        chip.load_from_db()

        # recalcula reputacao e regras
        novo_nivel = Tools.atualizar_reputacao(chip)
        chip.nivel_reputacao = novo_nivel

        regras = Tools.regras_envio(novo_nivel, chip.sem_resposta)

        # atualiza no supabase
        Tools.altera_status_bot(canal=canal, novo_status=1, reputacao=novo_nivel)

        # aplica pausa/intervalo (exatamente como no patch)
        if "pausa" in regras:
            if regras["pausa"] == -1:
                Tools.log(msg="🚫 Bot banido, parando execução", canal=canal)
                sys.exit()
            else:
                Tools.log(msg=f"⏸️ Pausa automática de {regras['pausa'] / 60:.0f} minutos", canal=canal)
                time.sleep(regras["pausa"])
        else:
            delay = regras["intervalo"]
            Tools.log(msg=f"⌛ Delay entre mensagens: {delay}s (nível {novo_nivel})", canal=canal)
            time.sleep(delay)

        # ###########################
        # EXECUÇÃO POR SPINS
        # ###########################
        for _ in range(spins):
            Tools.log(msg=f"INICIANDO SPIN | MODO={'TESTE' if canal.lower()=='teste' else 'PRODUÇÃO'} | SPINS {spins}", canal=canal)

            # ###########################
            # ITERAÇÃO POR LEAD
            # ###########################
            for i, (_, linha) in enumerate(df_mailing.iterrows()):
                n += 1
                lead_new = None
                lead = linha["Telefone"]

                Tools.log(msg=f"INÍCIO DA ITERAÇÃO #{n} | INDEX_MAILING {i} | LEAD {lead}", canal=canal)

                # ACESSA A ÁREA DE TRABALHO
                Tools.log(msg="ACESSANDO ÁREA DE TRABALHO (WIN + D)", canal=canal)
                Tools.area_trabalho()

                # ABRE O WHATSAPP DESKTOP (SEM PAUSA CEGA)
                Tools.log(msg="ABRINDO WHATSAPP DESKTOP VIA URL (WA.ME)", canal=canal)
                Tools.abre_whatsapp_desktop(lead)
                #Tools.log_img(log_img=f"ABERTURA_WHATSAPP_{lead}", canal=canal)

                Tools.log(msg="GARANTINDO JANELA DO WHATSAPP EM PRIMEIRO PLANO (MAXIMIZAÇÃO)", canal=canal)
                Tools.maximiza_janela("WhatsApp")
                #Tools.log_img(log_img=f"VALIDACAO_ABERTURA_WHATSAPP_{lead}", canal=canal)

                # VALIDAÇÃO INTELIGENTE: AGUARDA A TELA CARREGAR OU DAR ERRO
                Tools.log(msg="AGUARDANDO TELA DO WHATSAPP CARREGAR (MÁX 20S)...", canal=canal)
                is_invalid = False
                try:
                    # Primeiro, verifica rapidamente se a tela é de telefone inválido
                    Tools.localiza_imagem(lista_imgs=[img_telefone_invalido], precisao=0.85)
                    is_invalid = True
                    Tools.log(msg="TELA 'TELEFONE INVÁLIDO' LOCALIZADA.", canal=canal)
                except Exception:
                    # Se não for inválido,
                    # ativamente pelo campo de mensagem, que indica que a tela carregou
                    Tools.log(msg="TELA 'TELEFONE INVÁLIDO' NÃO ENCONTRADA, AGUARDANDO TELA DE CONVERSA...", canal=canal)
                    try:
                        Tools.ciclo_tentativa(
                            funcao=Tools.localiza_imagem,
                            args=([img_form_msg],),
                            kwargs={"precisao": 0.8},
                            limit=20,  # Tenta por até 20 segundos
                            step=1,
                            descricao="CAMPO DE MENSAGEM"
                        )
                    except Exception as e:
                        # Se nem a tela de inválido nem o campo de mensagem apareceram, é um erro.
                        Tools.log(msg=f"ERRO CRÍTICO: A TELA DO WHATSAPP NÃO CARREGOU A TEMPO PARA O LEAD {lead}. DETALHE: {e}", canal=canal)
                        # Registra como falha e pula para o próximo
                        Tools.registra_discagem(
                            datadiscagem=time.strftime("%Y-%m-%d %H:%M:%S"),
                            telefone=lead, canal=canal, status=3
                        )
                        continue # Pula para o próximo lead

                # RAMIFICAÇÃO: TELEFONE INVÁLIDO
                if is_invalid:
                    Tools.log(msg=f"LEAD INVÁLIDO | TELEFONE {lead} | REGISTRANDO STATUS 3 (INVÁLIDO)", canal=canal)
                    lead = lead_new if lead_new else lead
                    Tools.registra_discagem(
                        datadiscagem=time.strftime("%Y-%m-%d %H:%M:%S"),
                        telefone=lead, canal=canal, status=3
                    )
                    Tools.log(msg="SEGUINDO PARA O PRÓXIMO LEAD", canal=canal)
                    continue

                Tools.log(msg="VALIDANDO SE EXISTE MENSAGEM ATIVA DA CAMPANHA", canal=canal)
                status_msg_ativo = Tools.status_msg_ativo(limiar=0.80, save_teste=True)
                #Tools.log_img(log_img=f"STATUS_MSG_{lead}", canal=canal)
                if status_msg_ativo == 0:
                    Tools.log(msg=f"STATUS 0, MENSAGEM ATIVA NO TELEFONE {lead}", canal=canal)
                    continue

                # MONTA E ENVIA MENSAGEM
                Tools.log(msg="SELECIONANDO TEMPLATE DE MENSAGEM (TM)", canal=canal)
                msg_tm = Tools.tm_mensagem() # Removida pausa desnecessária daqui
                Tools.log(msg=f"TM SELECIONADO {msg_tm}", canal=canal)

                # VALIDA E ESCREVE A MENSAGEM NA CAIXA DE TEXTO
                Tools.log(msg="VALIDANDO CAIXA DE TEXTO E INSERINDO MENSAGEM", canal=canal)
                for tentativa in range(2):
                    status_formulario = Tools.valida_caixa_texto(cliente=linha['Cliente'], msg_tm=msg_tm, lead=lead)
                    if status_formulario == 1:
                        break
                    Tools.espera(1.0, 2.2) # Pausa mantida pois é para retry de uma ação específica

                    Tools.pressionar_tecla(tecla1="tab")
                    Tools.pressionar_tecla(tecla1="tab")

                if status_formulario == 0:
                    Tools.log(msg="ERRO AO LOCALIZAR FORMULÁRIO, PULANDO PARA PRÓXIMO LEAD", canal=canal)
                    continue

                # ANEXA IMAGEM DA CAMPANHA (SEM PAUSA CEGA ANTES)
                Tools.log(msg="ABRINDO SELETOR E ANEXANDO IMAGENS DA CAMPANHA", canal=canal)
                Tools.anexa_img_campanha(canal=canal, espera=sleep_geral, lead=lead)
                #Tools.log_img(log_img=f"VALIDACAO_BTN_ANEXAR_IMG_{lead}", canal=canal)

                #Tools.log_img(log_img=f"SELECAO_TM_{lead}", canal=canal)

                # REGISTRA A DISCAGEM (SUCESSO)
                Tools.log(msg=f"REGISTRANDO DISCAGEM (SUCESSO) | TELEFONE={lead}", canal=canal)
                lead = lead_new if lead_new else lead
                Tools.registra_discagem(
                    datadiscagem=time.strftime("%Y-%m-%d %H:%M:%S"),
                    telefone=lead, canal=canal, status=1
                )

                Tools.log(msg="FINAL DA ITERAÇÃO | PAUSA ENTRE LEADS", canal=canal)
                (Tools.espera
                 (1.2, 2.4))


        finalizar_campanha(canal)

        # FIM DO PROCESSO NORMAL: ENCERRA E ATUALIZA STATUS
        Tools.log(msg="PROCESSO FINALIZADO SEM EXCEÇÕES | ATUALIZANDO STATUS DO BOT PARA 0 (INATIVO)", canal=canal)
        Tools.altera_status_bot(novo_status=0, canal=canal)
        Tools.log(msg="FIM DO PROCESSO", canal=canal)
        print("FIM")
        break

    except Exception as e:
        # REGISTRA EVENTO DE ERRO E DISCAGEM COM STATUS=0
        Tools.log(msg=f"ERRO NO PROCESSO | DETALHE: {e}", canal=canal)
        try:
            Tools.registra_discagem(
                datadiscagem=time.strftime("%Y-%m-%d %H:%M:%S")
                , telefone=lead, canal=canal, status=0
            )
            Tools.log(msg="DISCAGEM DE ERRO REGISTRADA COM SUCESSO (STATUS=0)", canal=canal)
        except Exception as ee:
            Tools.log(msg=f"FALHA AO REGISTRAR DISCAGEM DE ERRO | {ee}", canal=canal)

        # OPCIONAL: MANTER LOOP OU SAIR — MANTIVE COM CONTROLE PELO WHILE/STATUS
        Tools.log(msg="CONTINUANDO LOOP APÓS ERRO (SE STATUS PERMITIR)", canal=canal)