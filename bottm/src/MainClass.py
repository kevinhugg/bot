import time
import sys
import argparse

# Importa as novas classes de serviço
from services.database import DatabaseService
from services.automation import WhatsappAutomator
from services.reputation import ReputationService
from services.phone_utils import mascara_telefone


def processar_lead(lead: dict, automator: WhatsappAutomator, db: DatabaseService, canal: str):
    """
    Encapsula toda a lógica de processamento para um único lead.
    Retorna True se o processo foi bem-sucedido, False caso contrário.
    """
    telefone = lead.get("Telefone_Corrigido", lead.get("Telefone"))
    cliente = lead.get("Cliente", "Cliente")

    print(f"\n--- Processando lead: {cliente} ({mascara_telefone(telefone)}) ---")

    try:
        # 1. Abrir a conversa e verificar o estado
        automator.open_conversation(telefone)
        if automator.check_for_invalid_number():
            print(f"Número inválido detectado para {telefone}. Registrando e pulando.")
            db.register_dispatch(telefone, canal, status=3)  # 3 = Inválido
            return False

        # 2. Preparar e enviar a mensagem
        template = db.get_message_template()
        automator.send_message(cliente, template)

        # 3. Anexar imagem da campanha
        automator.attach_campaign_image()

        # 4. Registrar sucesso
        db.register_dispatch(telefone, canal, status=1)  # 1 = Sucesso
        print(f"--- Lead {cliente} processado com sucesso. ---")
        return True

    except Exception as e:
        print(f"!!! ERRO CRÍTICO ao processar o lead {telefone}: {e} !!!")
        # Tenta registrar o erro no banco de dados
        try:
            db.register_dispatch(telefone, canal, status=0)  # 0 = Erro
        except Exception as db_error:
            print(f"!!! FALHA ao registrar o erro no banco de dados: {db_error} !!!")
        return False


def main(canal: str):
    """
    Função principal que orquestra o bot.
    """
    print(f"🚀 Iniciando Bot WhatsApp para o canal: '{canal}'")

    # Inicializa todos os serviços necessários
    db_service = DatabaseService()
    automation_service = WhatsappAutomator()
    reputation_service = ReputationService()

    # Loop principal de execução
    while True:
        # 1. Verificar status do bot
        bot_status = db_service.get_bot_status(canal)
        if bot_status != 1:
            print(f"🤖 Bot para o canal '{canal}' está inativo (status: {bot_status}). Encerrando.")
            sys.exit()

        # 2. Gerenciar reputação e pausas
        chip = reputation_service.carregar_chip(canal)
        novo_nivel = reputation_service.atualizar_reputacao(chip)
        if novo_nivel != chip.nivel_reputacao:
            db_service.update_bot_status(canal, novo_status=1, reputacao=novo_nivel)
            print(f"Reputação do canal '{canal}' atualizada para o nível {novo_nivel}.")

        regras = reputation_service.get_regras_envio(novo_nivel, chip.sem_resposta)

        if "pausa" in regras:
            if regras["pausa"] == -1:
                print(f"🚫 Bot banido. Encerrando operação.")
                db_service.update_bot_status(canal, novo_status=2, reputacao=5)  # Status 2 = Banido
                sys.exit()

            print(f"⏸️ Pausa automática de {regras.get('motivo', 'manutenção')} por {regras['pausa']:.0f} segundos.")
            time.sleep(regras["pausa"])
            continue

        # 3. Carregar e processar o mailing
        print("📰 Carregando mailing...")
        mailing = db_service.get_mailing(canal)

        if not mailing:
            print("📪 Mailing vazio. Aguardando 5 minutos antes de verificar novamente.")
            time.sleep(300)
            continue

        print(f"📧 Mailing carregado com {len(mailing)} leads para processar.")

        for lead in mailing:
            processar_lead(lead, automation_service, db_service, canal)

            # Pausa entre os leads
            intervalo = regras.get("intervalo", 60)
            print(f"⌛ Aguardando {intervalo:.1f}s para o próximo lead (Nível de Reputação: {novo_nivel}).")
            time.sleep(intervalo)

        print("\n🏁 Fim do ciclo de mailing. Aguardando 15 minutos para reiniciar.")
        time.sleep(900)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bot de automação para WhatsApp.")
    parser.add_argument(
        "canal",
        type=str,
        help="O nome do canal a ser executado (ex: 'teste', 'terra')."
    )
    args = parser.parse_args()

    main(args.canal)