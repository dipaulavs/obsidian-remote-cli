# 🤖 Obsidian Remote CLI

API para controlar Claude Code remotamente via links clicáveis no Obsidian.

## 🎯 Funcionalidades

1. **Organizar Notas** - Um clique organiza todas as notas soltas
2. **Executar Claude Code** - Rodar comandos remotamente via API
3. **Integração Syncthing** - Sincronização automática de volta

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────┐
│ Obsidian Desktop/Mobile                     │
│ (nota com botões HTML)                      │
└────────────────┬────────────────────────────┘
                 │ HTTPS
                 ↓
┌─────────────────────────────────────────────┐
│ Traefik (SSL + Routing)                     │
│ obsidian-cli.loop9.com.br                   │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│ Flask API (Docker Container)                │
│ - /organize-notes                           │
│ - /execute-claude                           │
│ - /health                                   │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│ Claude Code CLI                             │
│ Executa no Syncthing folder                 │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│ Syncthing                                   │
│ Sincroniza de volta para dispositivos       │
└─────────────────────────────────────────────┘
```

## 📦 Deploy

### Pré-requisitos na VPS

1. **Claude Code instalado:**
```bash
npm install -g @anthropics/claude-code
```

2. **Syncthing configurado:**
```bash
# Pasta compartilhada: /root/Obsidian/Claude-code-ios
# Sincronizando com Mac/iOS/Android
```

3. **Docker Swarm + Traefik:**
```bash
# Rede loop9Net criada
# Traefik rodando com Let's Encrypt
```

### Deploy do Serviço

```bash
# 1. Copiar arquivos para VPS
cd ClaudeCode-Workspace/SWARM/automations/obsidian-remote-cli
scp -r * root@82.25.68.132:/root/SWARM/automations/obsidian-remote-cli/

# 2. Na VPS, fazer deploy
ssh root@82.25.68.132
cd /root/SWARM/automations/obsidian-remote-cli
docker stack deploy -c docker-compose.yml obsidian-cli

# 3. Verificar
docker service ls | grep obsidian-cli
docker service logs obsidian-cli_app -f
```

## 🔗 Endpoints

### GET /health
Health check do serviço.

**Resposta:**
```json
{
    "status": "healthy",
    "service": "obsidian-remote-cli",
    "timestamp": "2025-11-11T10:00:00"
}
```

### POST /organize-notes
Organiza notas soltas na raiz do vault.

**Workflow:**
1. Busca arquivos `.md` na raiz (exceto dashboards)
2. Executa: `claude --message "organize minhas notas" --yes`
3. Claude usa skill `obsidian-organizer`
4. Syncthing sincroniza resultado

**Resposta (sucesso):**
```json
{
    "status": "success",
    "message": "✅ 3 nota(s) organizada(s)",
    "notes": ["nota1.md", "nota2.md", "nota3.md"],
    "output": "..."
}
```

**Resposta (sem notas):**
```json
{
    "status": "success",
    "message": "Nenhuma nota solta para organizar",
    "notes_organized": 0
}
```

### POST /execute-claude
Executa comando Claude Code customizado.

**Body:**
```json
{
    "message": "Seu prompt completo aqui"
}
```

**Exemplo:**
```bash
curl -X POST https://obsidian-cli.loop9.com.br/execute-claude \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Cria uma nova tarefa chamada Implementar Feature X"
  }'
```

**Resposta:**
```json
{
    "status": "success",
    "output": "✅ Tarefa criada: 📋 Tarefas/Implementar Feature X.md"
}
```

## 📱 Uso no Obsidian

### Desktop (botões HTML)

Criar nota com botões clicáveis:

```html
<button onclick="fetch('https://obsidian-cli.loop9.com.br/organize-notes', {method: 'POST'}).then(r => r.json()).then(d => alert(d.message))">
🗂️ Organizar Notas
</button>
```

### Mobile (Advanced URI Plugin)

```
obsidian://advanced-uri?vault=Claude-code-ios&commandid=shell-commands&command=curl%20-X%20POST%20https://obsidian-cli.loop9.com.br/organize-notes
```

### Templater Plugin

```javascript
<%*
const response = await fetch('https://obsidian-cli.loop9.com.br/organize-notes', {
    method: 'POST'
});
const result = await response.json();
new Notice(result.message);
%>
```

## 🔒 Segurança

**HTTPS Obrigatório:**
- Traefik fornece SSL via Let's Encrypt
- Certificado renovado automaticamente

**Acesso:**
- URL pública: https://obsidian-cli.loop9.com.br
- Sem autenticação (adicionar se necessário)

**Recomendação:** Adicionar autenticação básica se expor publicamente:

```python
from functools import wraps
from flask import request, Response

def check_auth(username, password):
    return username == 'admin' and password == 'sua-senha-aqui'

def authenticate():
    return Response('Login required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/organize-notes', methods=['POST'])
@requires_auth
def organize_notes():
    # ...
```

## 🐛 Troubleshooting

### Serviço não inicia?
```bash
# Ver logs
docker service logs obsidian-cli_app

# Verificar se Claude Code está instalado
ssh root@82.25.68.132
which claude
claude --version
```

### Timeout (504)?
```bash
# Claude Code pode demorar
# Aumentar timeout no docker-compose.yml se necessário
# Padrão: 300 segundos (5 minutos)
```

### Syncthing não sincroniza?
```bash
# Verificar status do Syncthing
curl http://localhost:8384/rest/system/status

# Forçar scan
curl -X POST http://localhost:8384/rest/db/scan?folder=obsidian
```

## 📊 Monitoramento

### Health Check
```bash
curl https://obsidian-cli.loop9.com.br/health
```

### Logs em tempo real
```bash
ssh root@82.25.68.132
docker service logs obsidian-cli_app -f
```

### Métricas Docker
```bash
docker service ps obsidian-cli_app
docker stats $(docker ps -q --filter name=obsidian-cli)
```

## 🎯 Casos de Uso

1. **Organização periódica** - Clicar botão 1x por dia para organizar notas
2. **Mobile workflow** - Capturar no mobile, organizar remotamente
3. **Automação** - Webhook acionado por outros serviços
4. **CI/CD** - Integrar com pipelines para processar notas

## 🔄 Fluxo Completo

```
1. Você cria notas soltas no Obsidian (Mac/iOS/Android)
        ↓ Syncthing sincroniza
2. VPS recebe notas via Syncthing
        ↓
3. Você clica "Organizar Notas" no Obsidian
        ↓ HTTPS request
4. API executa Claude Code na VPS
        ↓
5. Claude organiza notas (skill obsidian-organizer)
        ↓ Escreve arquivos organizados
6. Syncthing detecta mudanças
        ↓ Sincroniza de volta
7. Obsidian atualiza automaticamente ✅
```

## 📝 TODO

- [ ] Adicionar autenticação (Basic Auth ou Token)
- [ ] Rate limiting (evitar spam)
- [ ] Webhook notifications (Discord/Telegram)
- [ ] Dashboard web para visualizar status
- [ ] Logs persistentes (não só stdout)
- [ ] Queue system para múltiplas requisições

---

**URL:** https://obsidian-cli.loop9.com.br
**Deploy:** Docker Swarm na VPS 82.25.68.132
**SSL:** Automático via Traefik + Let's Encrypt
**Atualizado:** 11/11/2025
