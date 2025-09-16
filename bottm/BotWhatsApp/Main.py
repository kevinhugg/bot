# IMPORTAÇÕES DOS MÓDULOS PERSONALIZADOS
from MainClass import *
import sys

# DEFINIÇÃO DO CANAL E VARIÁVEIS DE CONTROLE
canal = "terra" #terra
spins = 300
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

                # ABRE O WHATSAPP DESKTOP
                Tools.log(msg="ABRINDO WHATSAPP DESKTOP VIA URL (WA.ME)", canal=canal)
                Tools.abre_whatsapp_desktop(lead, sleep=3)
                Tools.log_img(log_img=f"ABERTURA_WHATSAPP_{lead}", canal=canal)

                Tools.log(msg="GARANTINDO JANELA DO WHATSAPP EM PRIMEIRO PLANO (MAXIMIZAÇÃO)", canal=canal)
                Tools.maximiza_janela("WhatsApp")
                Tools.log_img(log_img=f"VALIDACAO_ABERTURA_WHATSAPP_{lead}", canal=canal)

                # VALIDAÇÃO DO NÚMERO DO CLIENTE
                Tools.log(msg="VALIDANDO TELEFONE DO CLIENTE", canal=canal)
                time.sleep(sleep_geral)

                try:
                    loc = Tools.localiza_imagem(lista_imgs=[img_telefone_invalido])
                    status = 1
                    Tools.log(msg="TELA 'TELEFONE INVÁLIDO' LOCALIZADA", canal=canal)
                    Tools.log_img(log_img=f"VALIDACAO_TELEFONE_{lead}", canal=canal)
                except Exception:
                    status = 0
                    Tools.log(msg="TELA 'TELEFONE INVÁLIDO' NÃO LOCALIZADA, SEGUINDO O FLUXO", canal=canal)

                # RAMIFICAÇÃO: TELEFONE INVÁLIDO
                if status == 1:
                    Tools.log(msg=f"LEAD INVÁLIDO | TELEFONE {lead} | REGISTRANDO STATUS 3 (INVÁLIDO)", canal=canal)
                    lead = lead_new if lead_new else lead
                    Tools.registra_discagem(
                        datadiscagem=time.strftime("%Y-%m-%d %H:%M:%S"),
                        telefone=lead, canal=canal, status=3
                    )
                    Tools.log(msg="SEGUINDO PARA O PRÓXIMO LEAD", canal=canal)
                    continue

                Tools.log(msg="VALIDANDO SE EXISTE MENSAGEM ATIVA DA CAMPANHA", canal=canal)
                status_msg_ativo = Tools.status_msg_ativo()
                if status_msg_ativo == 0:
                    Tools.log(msg=f"STATUS 0, MENSAGEM ATIVA NO TELEFONE {lead}", canal=canal)
                    continue


                # ANEXA IMAGEM DA CAMPANHA
                Tools.log(msg="ABRINDO SELETOR E ANEXANDO IMAGENS DA CAMPANHA", canal=canal)
                Tools.anexa_img_campanha(canal=canal, espera=sleep_geral, lead=lead)
                Tools.log_img(log_img=f"VALIDACAO_BTN_ANEXAR_IMG_{lead}", canal=canal)

                # MONTA E ENVIA MENSAGEM
                Tools.log(msg="SELECIONANDO TEMPLATE DE MENSAGEM (TM)", canal=canal)
                time.sleep(2)
                msg_tm = Tools.tm_mensagem()
                Tools.log(msg=f"TM SELECIONADO {msg_tm}", canal=canal)

                time.sleep(1)

                # LOCALIZA O FORMULÁRIO DE MENSAGEM
                Tools.log(msg="LOCALIZANDO FORMULÁRIO DE MENSAGEM NA TELA", canal=canal)
                try:
                    loc = Tools.localiza_imagem(lista_imgs=[img_form_msg])
                    status = 1
                    Tools.log(msg="FORMULÁRIO DE MENSAGEM LOCALIZADO", canal=canal)
                except Exception:
                    status = 0
                    Tools.log(msg="FORMULÁRIO DE MENSAGEM NÃO LOCALIZADO (TENTAREMOS MESMO ASSIM)", canal=canal)

                # VALIDA E ESCREVE A MENSAGEM NA CAIXA DE TEXTO
                Tools.log(msg="VALIDANDO CAIXA DE TEXTO E INSERINDO MENSAGEM", canal=canal)
                time.sleep(10)
                status_formulario = Tools.valida_caixa_texto(cliente=linha['Cliente'], msg_tm=msg_tm, lead=lead
                                                             )
                if status_formulario == 0:
                    Tools.log(msg="ERRO AO LOCALIZAR FOMULARIO, PULANDO PARA PROXIMO LEAD", canal=canal)
                    continue


                Tools.log_img(log_img=f"SELECAO_TM_{lead}", canal=canal)

                # REGISTRA A DISCAGEM (SUCESSO)
                Tools.log(msg=f"REGISTRANDO DISCAGEM (SUCESSO) | TELEFONE={lead}", canal=canal)
                lead = lead_new if lead_new else lead
                Tools.registra_discagem(
                    datadiscagem=time.strftime("%Y-%m-%d %H:%M:%S"),
                    telefone=lead, canal=canal, status=1
                )

                Tools.log(msg="FINAL DA ITERAÇÃO | PAUSA ENTRE LEADS", canal=canal)
                time.sleep(sleep_geral)

        # FIM DO PROCESSO NORMAL: ENCERRA E ATUALIZA STATUS
        Tools.log(msg="PROCESSO FINALIZADO SEM EXCEÇÕES | ATUALIZANDO STATUS DO BOT PARA 0 (INATIVO)", canal=canal)
        Tools.altera_status_bot(novo_status=0, canal=canal)
        Tools.log(msg="FIM DO PROCESSO", canal=canal)
        print("FIM")
        break

    except Exception as e:
        # REGISTRA EVENTO DE ERRO E DISCAGEM COM STATUS=3
        Tools.log(msg=f"ERRO NO PROCESSO | DETALHE: {e}", canal=canal)
        try:
            Tools.registra_discagem(
                datadiscagem=time.strftime("%Y-%m-%d %H:%M:%S")
                , telefone=lead, canal=canal, status=3
            )
            Tools.log(msg="DISCAGEM DE ERRO REGISTRADA COM SUCESSO (STATUS=3)", canal=canal)
        except Exception as ee:
            Tools.log(msg=f"FALHA AO REGISTRAR DISCAGEM DE ERRO | {ee}", canal=canal)

        # OPCIONAL: MANTER LOOP OU SAIR — MANTIVE COM CONTROLE PELO WHILE/STATUS
        Tools.log(msg="CONTINUANDO LOOP APÓS ERRO (SE STATUS PERMITIR)", canal=canal)
