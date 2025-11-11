#!/usr/bin/env python3
"""
Obsidian Remote CLI
API para executar Claude Code remotamente via links do Obsidian
"""

from flask import Flask, request, jsonify
import subprocess
import os
from datetime import datetime

app = Flask(__name__)

# Paths (será configurado quando Syncthing estiver ativo)
OBSIDIAN_VAULT = "/vault"  # Placeholder
CLAUDE_CODE_WORKSPACE = "/workspace"  # Placeholder

def log_request(action, status, message=""):
    """Log de requisições"""
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"[{timestamp}] {action} - {status} - {message}")

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "obsidian-remote-cli",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/organize-notes', methods=['POST'])
def organize_notes():
    """
    Organiza notas soltas usando Claude Code

    Workflow:
    1. Detecta notas soltas na raiz do vault
    2. Executa Claude Code com prompt de organização
    3. Retorna resultado
    """
    try:
        log_request("organize-notes", "INICIADO")

        # TODO: Implementar verificação quando Syncthing estiver configurado
        # Por enquanto, retorna status de configuração pendente
        log_request("organize-notes", "CONFIGURAÇÃO PENDENTE")
        return jsonify({
            "status": "pending",
            "message": "⚠️  Syncthing não configurado ainda. Funcionalidade disponível em breve.",
            "next_steps": [
                "1. Configurar Syncthing na VPS",
                "2. Sincronizar pasta Obsidian",
                "3. Atualizar paths no docker-compose.yml"
            ]
        }), 503

        # Executa Claude Code para organizar
        cmd = [
            "claude",
            "--yes",
            f"--directory={CLAUDE_CODE_WORKSPACE}",
            "--message",
            f"Organize as seguintes notas soltas do Obsidian: {', '.join(loose_notes)}. Use a skill obsidian-organizer."
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )

        if result.returncode == 0:
            log_request("organize-notes", "SUCESSO", f"{len(loose_notes)} notas organizadas")
            return jsonify({
                "status": "success",
                "message": f"✅ {len(loose_notes)} nota(s) organizada(s)",
                "notes": loose_notes,
                "output": result.stdout[-500:]  # Últimas 500 chars
            })
        else:
            log_request("organize-notes", "ERRO", result.stderr)
            return jsonify({
                "status": "error",
                "message": "Erro ao executar Claude Code",
                "error": result.stderr
            }), 500

    except subprocess.TimeoutExpired:
        log_request("organize-notes", "TIMEOUT")
        return jsonify({
            "status": "error",
            "message": "Timeout ao executar Claude Code"
        }), 504

    except Exception as e:
        log_request("organize-notes", "ERRO", str(e))
        return jsonify({
            "status": "error",
            "message": f"Erro inesperado: {str(e)}"
        }), 500

@app.route('/execute-claude', methods=['POST'])
def execute_claude():
    """
    Executa comando Claude Code customizado

    Body: {
        "message": "Seu prompt aqui"
    }
    """
    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message:
            return jsonify({
                "status": "error",
                "message": "Campo 'message' é obrigatório"
            }), 400

        log_request("execute-claude", "INICIADO", f"Prompt: {message[:50]}...")

        # Executa Claude Code
        cmd = [
            "claude",
            "--yes",
            f"--directory={CLAUDE_CODE_WORKSPACE}",
            "--message",
            message
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            log_request("execute-claude", "SUCESSO")
            return jsonify({
                "status": "success",
                "output": result.stdout[-1000:]  # Últimos 1000 chars
            })
        else:
            log_request("execute-claude", "ERRO", result.stderr)
            return jsonify({
                "status": "error",
                "message": "Erro ao executar Claude Code",
                "error": result.stderr
            }), 500

    except subprocess.TimeoutExpired:
        log_request("execute-claude", "TIMEOUT")
        return jsonify({
            "status": "error",
            "message": "Timeout ao executar Claude Code"
        }), 504

    except Exception as e:
        log_request("execute-claude", "ERRO", str(e))
        return jsonify({
            "status": "error",
            "message": f"Erro inesperado: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("🚀 Obsidian Remote CLI API")
    print(f"📂 Vault: {OBSIDIAN_VAULT}")
    print(f"💻 Workspace: {CLAUDE_CODE_WORKSPACE}")
    app.run(host='0.0.0.0', port=8080)
