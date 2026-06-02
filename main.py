import os
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# 1. Coleta e limpeza cirúrgica das credenciais do ambiente
BLOG_ID_RAW = os.environ.get("BLOG_ID", "").strip().replace('"', '').replace("'", "")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN", "").strip()

def main():
    print("🚨 [EXECUÇÃO FORÇADA CRÍTICA] Iniciando tentativa direta de postagem via OAuth2...")
    
    # Validação de Variáveis de Ambiente
    if not BLOG_ID_RAW:
        raise ValueError("ERRO: A variável 'BLOG_ID' está vazia no GitHub Actions.")
    if not CLIENT_ID or not CLIENT_SECRET or not REFRESH_TOKEN:
        raise ValueError("ERRO: As chaves OAuth2 (CLIENT_ID, SECRET ou REFRESH_TOKEN) não foram carregadas no GitHub.")

    # Força a conversão para texto limpo removendo qualquer espaço residual
    blog_id_limpo = "".join(filter(str.isdigit, BLOG_ID_RAW))
    print(f"🔎 Identificador do Blog Alvo Convertido: {blog_id_limpo}")
    
    # 2. Autenticação Humana Direta usando o Token da Conta 2
    credentials = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/blogger']
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
    
    # Execução enviando o ID 100% limpo antes de rodar
    request = blogger_service.posts().insert(blogId=blog_id_limpo, body=payload)
    response = request.execute()
    
    print("\n✅====================================================")
    print(f"🎉 SUCESSO ABSOLUTO! O post foi publicado!")
    print(f"🔗 Link do Post: {response.get('url')}")
    print("======================================================")

if __name__ == "__main__":
    main()
