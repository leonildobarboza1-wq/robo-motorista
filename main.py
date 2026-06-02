import os
import json
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Coleta direta das credenciais do ambiente do GitHub
BLOG_ID = os.environ.get("BLOG_ID")
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

def main():
    print("🚨 [EXECUÇÃO FORÇADA CRÍTICA] Iniciando tentativa direta de postagem...")
    
    # 1. Validação de Variáveis de Ambiente
    if not BLOG_ID:
        raise ValueError("ERRO: A variável 'BLOG_ID' está vazia ou não foi carregada no GitHub Actions.")
    if not SERVICE_ACCOUNT_JSON:
        raise ValueError("ERRO: A variável 'GOOGLE_SERVICE_ACCOUNT_JSON' está vazia ou incorreta.")

    print(f"🔎 Identificador do Blog Alvo: {BLOG_ID}")
    
    # 2. Autenticação Direta (Sem travas de erro)
    info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/blogger']
    )
    blogger_service = build('blogger', 'v3', credentials=credentials)
    
    # 3. Criação de um Post Simples para Forçar Entrada
    titulo_urgente = "Vaga Urgente - Motorista Profissional - " + datetime.datetime.now().strftime("%d/%m %H:%M")
    
    html_conteudo = """
    <h2>Oportunidade para Motorista Profissional</h2>
    <p>Esta é uma publicação automatizada gerada pelo robô de integração direta via API v3.</p>
    <p>Se você está lendo esta mensagem, o canal de comunicação entre o GitHub Actions e o Blogger foi desbloqueado com sucesso!</p>
    """
    
    payload = {
        "kind": "blogger#post",
        "title": titulo_urgente,
        "content": html_conteudo,
        "labels": ["Conectado"]
    }
    
    print("📤 Despachando requisição para os servidores do Google...")
    
    # Execução nua e crua (Sem try/except). Se falhar, vai quebrar o build e mostrar o motivo real!
    request = blogger_service.posts().insert(blogId=BLOG_ID, body=payload)
    response = request.execute()
    
    print("\n✅====================================================")
    print(f"🎉 SUCESSO ABSOLUTO! O post foi publicado!")
    print(f"🔗 Link do Post: {response.get('url')}")
    print("======================================================")

if __name__ == "__main__":
    main()
