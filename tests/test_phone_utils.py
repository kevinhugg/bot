import sys
import os
import pytest

# Adiciona o diretório do projeto ao path do Python para permitir importações
# Assumindo que a pasta `tests` está na raiz, e o código fonte está em `bottm/BotWhatsApp`
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'bottm/BotWhatsApp'))

# Agora a importação deve funcionar
from services.phone_utils import corrige_numero, normaliza_e164

# --- Testes para a função `corrige_numero` ---

def test_deve_adicionar_nono_digito_em_celular_antigo():
    """
    Verifica se o 9º dígito é adicionado a um número de celular com 8 dígitos
    que começa com 6, 7, 8 ou 9.
    """
    numero_corrigido, flag = corrige_numero("551187654321")
    assert numero_corrigido == "5511987654321"
    assert flag == "ADICIONAR_9_CEL"

def test_deve_remover_nono_digito_de_telefone_fixo():
    """
    Verifica se o 9º dígito é removido de um número que se parece com fixo
    (começando com 2, 3, 4 ou 5).
    """
    numero_corrigido, flag = corrige_numero("5511932324545")
    assert numero_corrigido == "551132324545"
    assert flag == "REMOVER_9_FIXO"

def test_nao_deve_alterar_numero_de_celular_correto():
    """
    Verifica se um número de celular já no formato correto (com 9º dígito)
    não é modificado.
    """
    numero_corrigido, flag = corrige_numero("5511987654321")
    assert numero_corrigido == "5511987654321"
    assert flag == "OK"

def test_nao_deve_alterar_numero_fixo_correto():
    """
    Verifica se um número de telefone fixo sem o 9º dígito
    não é modificado.
    """
    numero_corrigido, flag = corrige_numero("551123456789")
    assert numero_corrigido == "551123456789"
    assert flag == "OK"

def test_deve_retornar_flag_invalido_para_numero_curto():
    """
    Verifica se números muito curtos são marcados como inválidos.
    """
    numero_corrigido, flag = corrige_numero("5511123")
    assert flag == "INVALIDO_CURTO"

# --- Testes para a função `normaliza_e164` ---

def test_deve_adicionar_55_se_ausente():
    """Verifica se o código do país '55' é adicionado."""
    assert normaliza_e164("11987654321") == "5511987654321"

def test_deve_remover_caracteres_nao_numericos():
    """Verifica se parênteses, traços e espaços são removidos."""
    assert normaliza_e164("(11) 98765-4321") == "5511987654321"

def test_deve_remover_prefixo_de_longa_distancia():
    """Verifica se um '0' no início é removido."""
    assert normaliza_e164("011987654321") == "5511987654321"

def test_nao_deve_alterar_numero_ja_normalizado():
    """Verifica se um número já no formato E.164 correto não é alterado."""
    assert normaliza_e164("5511987654321") == "5511987654321"

# Para rodar estes testes, instale o pytest (`pip install pytest`)
# e execute o comando `pytest` no terminal, na raiz do projeto.