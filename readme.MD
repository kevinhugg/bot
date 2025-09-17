# 🤖 WhatsApp Bot – Fluxo Humanizado

Automação de mensagens no WhatsApp Desktop com **humanização** (pausas randômicas, digitação natural, movimentos suaves do mouse).  
Este README explica **o que mudou**, **como configurar** e **como rodar**.

---

## 📦 Sumário
- [Visão geral](#visão-geral)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Como funciona a humanização](#como-funciona-a-humanização)
- [O que foi alterado no código](#o-que-foi-alterado-no-código)
- [Execução](#execução)
- [Dicas de uso](#dicas-de-uso)
- [Solução de problemas](#solução-de-problemas)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Licença](#licença)

---

## Visão geral
Antes, o fluxo utilizava `time.sleep(...)` fixo, colava mensagens instantaneamente e clicava sem movimento.  
Agora, com o **módulo `humanizer.py`**:
- Pausas entre ações são **randômicas** (`Tools.espera(a, b)`).
- Mensagem é **digitada** (30%) ou **colada** (70%) com variação de tempo.
- O mouse **se move suavemente** até o alvo antes de clicar.
- O Enter é enviado com **pequeno delay natural**.

Benefícios:
- Fluxo mais “humano” e menos previsível.
- Menor risco de bloqueios por comportamento robótico.
- Configurável sem mexer no código (via `config.py`).

---

## Estrutura do projeto

```
.
├─ Main.py                  # Loop principal (spins/leads/fluxo)
├─ MainClass.py             # Classe Tools (UI, logs, anexos, etc.)
├─ humanizer.py             # ← NOVO: módulo de humanização
├─ config.py                # Diretórios e HUMANIZE (config da humanização)
├─ server.js                # API Node (whatsapp-web.js)
├─ send.py                  # Cliente Python (chama API Node)
├─ mailing/
│  └─ mailing_<canal>.txt   # Mailing de teste/produção
├─ dump_discagem/
│  └─ discagem_<canal>.txt  # Log de discagens (gerado)
├─ imgs_referencia/
│  ├─ form_mensagem.png
│  ├─ telefone_invalido.png
│  └─ ...                   # Outros botões/telas
├─ tm/
│  ├─ imgs/                 # Pastas de imagens de campanha (CampanhaX)
│  └─ msgs/                 # Textos .txt usados como template
└─ logs/
   ├─ log_transacional/
   └─ log_img/
```

---

## Instalação

> Python ≥ 3.9 recomendado. Node.js ≥ 18 para a API.

### Dependências Python
```bash
pip install pyautogui pyperclip pywinauto pandas opencv-python pygetwindow psutil mouse requests
```

### Dependências Node
```bash
npm install whatsapp-web.js express body-parser qrcode-terminal
```

---

## Configuração

1. **`config.py`**  
   Ajuste diretórios e adicione:
   ```python
   HUMANIZE = {
       "enabled": True,
       "min_wait": 1.2, "max_wait": 3.8,
       "mouse_move_min": 0.35, "mouse_move_max": 1.15, "mouse_jitter_px": 4,
       "type_min": 0.05, "type_max": 0.14, "prob_type": 0.30,
       "micro_min": 0.20, "micro_max": 0.55,
   }
   ```

2. **`humanizer.py`**  
   Novo módulo que controla pausas, digitação e cliques. (já incluso neste projeto)

3. **`MainClass.py`**  
   - Importe o Humanizer.
   - Substitua `time.sleep` por `Tools.espera`.
   - Troque `pgui.click`/`pyperclip.copy` por `Tools.click`/`Tools.escreve`.

4. **API Node (`server.js`)**  
   - Sobe um servidor Express na porta `3000`.
   - Exige `x-api-token` no header (default: `dev-token`).
   - Endpoints:
     - `/health`
     - `/send/text`
     - `/send/media`
     - `/send/bulk`

---

## Como funciona a humanização

- **Pausas naturais:** `Tools.espera(2, 5)` espera entre 2–5s.
- **Escrita:** `Tools.escreve(msg)` → 70% cola, 30% digita com variação.
- **Mouse:** `Tools.click((x,y))` move suavemente e clica com micro-pausa.
- **Enter:** `Tools.enter()` adiciona um pequeno delay e envia.

Tudo configurável em `config.py`.

---

## O que foi alterado no código

- `Main.py`  
  - `time.sleep(...)` → `Tools.espera(...)` (delays humanizados).

- `MainClass.py`  
  - Classe `Tools`: novos métodos `espera`, `escreve`, `click`, `enter`.  
  - Substituição de `pyperclip+ctrl+v` e `pgui.write`.

- `server.js` e `send.py`  
  - Mantêm API de envio de mensagens.  
  - Já incluem jitter (atrasos aleatórios) no envio em lote.

---

## Execução

### API Node
```bash
node server.js
```
- Na primeira vez, escaneie o QR no terminal com o WhatsApp.

### Bot Python
```bash
python Main.py
```

### Cliente Python simples
```bash
python send.py
```
- Pode enviar texto, mídia ou lote via CSV.

---

## Dicas de uso

- Rode em tela maximizada, escala 100%.  
- Use imagens de referência nítidas.  
- Ajuste `HUMANIZE` para calibrar velocidade.  
- Para testes, use `canal = "teste"` no `Main.py`.  
- Ative logs de imagem para depurar pontos de clique.

---

## Solução de problemas

- **Não localiza imagem**: verifique escala 100%, capture nova referência.  
- **WhatsApp não abre**: confirme instalação do Desktop/Edge.  
- **Mensagens rápidas demais**: aumente `min_wait`/`max_wait`.  
- **Erro de permissão**: rode como administrador, confirme pastas no `config.py`.

---

## FAQ

**Posso desligar a humanização?**  
Sim. `HUMANIZE["enabled"] = False`.

**Funciona no Linux/Mac?**  
Focado em Windows (UI Automation). Node/whatsapp-web.js roda em qualquer SO.

**Como adicionar novas campanhas?**  
Crie pasta em `tm/imgs/CampanhaX` e arquivos `.txt` em `tm/msgs/`.

---

## Roadmap

- [ ] UI Automation sem visão computacional (pywinauto).  
- [ ] Perfis de humanização por canal.  
- [ ] Painel de controle web.  
- [ ] Webhook de status/acks integrado com Python.

---

## Licença

Uso interno. Ajuste para MIT, GPL ou proprietário conforme sua necessidade.
