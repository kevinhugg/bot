import random
from datetime import datetime, time, timedelta
from db import get_conn


class Chip:
    """
    Representa o estado e as métricas de um "chip" (canal de envio).
    """

    def __init__(self, canal: str):
        self.canal = canal
        self.feedback_negativo = 0
        self.bounce_rate = 0.0
        self.taxa_resposta = 0.0
        self.nivel_reputacao = 1  # Nível inicial padrão
        self.sem_resposta = 0

    def load_metrics_from_db(self):
        """Carrega as métricas de desempenho do banco de dados."""
        try:
            with get_conn() as conn:
                with conn.cursor() as cur:
                    # Exemplo de queries para buscar métricas (ajuste conforme seu esquema)
                    # Total de tentativas nos últimos 7 dias
                    cur.execute("""
                                SELECT COUNT(*)
                                FROM discagem
                                WHERE canal = %s
                                  AND datadiscagem >= NOW() - INTERVAL '7 days'
                                """, (self.canal,))
                    tentativas = cur.fetchone()[0] or 0

                    # Respostas (supondo status=1 para sucesso/resposta)
                    cur.execute("""
                                SELECT COUNT(*)
                                FROM discagem
                                WHERE canal = %s
                                  AND status = 1
                                  AND datadiscagem >= NOW() - INTERVAL '7 days'
                                """, (self.canal,))
                    respostas = cur.fetchone()[0] or 0

                    # Inválidos (supondo status=3 para inválido)
                    cur.execute("""
                                SELECT COUNT(*)
                                FROM discagem
                                WHERE canal = %s
                                  AND status = 3
                                  AND datadiscagem >= NOW() - INTERVAL '7 days'
                                """, (self.canal,))
                    invalidos = cur.fetchone()[0] or 0

                    # Busca a reputação atual
                    cur.execute("SELECT reputacao FROM status_bot WHERE canal = %s", (self.canal,))
                    reputacao_db = cur.fetchone()
                    if reputacao_db:
                        self.nivel_reputacao = int(reputacao_db[0])

            # Calcula as métricas
            self.taxa_resposta = (respostas / tentativas) if tentativas else 0.0
            self.bounce_rate = (invalidos / tentativas * 100.0) if tentativas else 0.0
            self.sem_resposta = max(0, tentativas - respostas)

        except Exception as e:
            print(f"[Chip.load_from_db] Erro ao carregar métricas: {e}")


class ReputationService:
    """
    Serviço para gerenciar a reputação do bot e as regras de envio.
    """

    def carregar_chip(self, canal: str) -> Chip:
        """Cria e carrega as métricas de um Chip."""
        chip = Chip(canal)
        chip.load_metrics_from_db()
        return chip

    def atualizar_reputacao(self, chip: Chip) -> int:
        """
        Calcula e retorna um novo nível de reputação com base nas métricas do Chip.
        """
        # Esta lógica é um exemplo e pode ser ajustada
        if chip.feedback_negativo > 20:
            return 5  # Banido
        elif chip.feedback_negativo > 10 or chip.bounce_rate > 20:
            return 4  # Perigo de Ban
        elif chip.taxa_resposta > 0.2:
            # Melhora a reputação se a taxa de resposta for boa
            return min(chip.nivel_reputacao + 1, 3)
        elif chip.taxa_resposta < 0.05 and chip.sem_resposta > 50:
            # Piora a reputação se a taxa de resposta for muito baixa
            return max(chip.nivel_reputacao - 1, 1)

        return chip.nivel_reputacao  # Mantém a reputação atual

    def get_regras_envio(self, nivel_reputacao: int, mensagens_sem_resposta: int) -> dict:
        """
        Define as regras de envio (intervalos, pausas) com base no nível de reputação.
        """
        agora = datetime.now().time()

        # Pausa para almoço
        if time(12, 0) <= agora <= time(13, 30):
            return {"pausa": random.randint(300, 900), "motivo": "Almoço"}

        # Fim do expediente
        if agora >= time(20, 0):
            return {"pausa": 36000, "motivo": "Fim do expediente"}  # Pausa longa até o dia seguinte

        # Regras baseadas no nível de reputação
        if nivel_reputacao == 1:  # Aquecimento
            return {"intervalo": random.randint(280, 320), "limite_dia": 100}
        elif nivel_reputacao == 2:  # Confiável
            return {"intervalo": random.randint(160, 200), "limite_dia": 200}
        elif nivel_reputacao == 3:  # Sólido
            return {"intervalo": random.randint(120, 180), "limite_dia": 300}
        elif nivel_reputacao == 4:  # Perigo de Ban
            if mensagens_sem_resposta >= 150:
                return {"pausa": 7200, "motivo": "Muitas mensagens sem resposta"}
            return {"intervalo": random.randint(80, 90), "limite_dia": 999}
        elif nivel_reputacao == 5:  # Banido
            return {"pausa": -1, "motivo": "Bot banido"}  # -1 indica parada permanente

        # Fallback para um intervalo padrão
        return {"intervalo": random.randint(120, 180)}