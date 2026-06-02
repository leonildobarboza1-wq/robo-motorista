import os
import json
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ==========================================
# CONFIGURAÇÕES E AMBIENTE (OBRIGATÓRIO NO TOPO)
# ==========================================
BLOG_ID = os.environ.get("BLOG_ID")
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

def get_blogger_service():
    """Autentica na API do Blogger utilizando a Conta de Serviço."""
    if not SERVICE_ACCOUNT_JSON:
        raise ValueError("A chave GOOGLE_SERVICE_ACCOUNT_JSON não está configurada nos Secrets.")
    
    info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/blogger']
    )
    return build('blogger', 'v3', credentials=credentials)

def build_final_html(ai_body: str, item_link: str) -> str:
    """Monta um HTML simples estruturado para o teste."""
    html_topo = f"""
    <div style="background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 12px 16px; margin-bottom: 20px; font-family: sans-serif;">
        <span style="color: #495057; font-weight: bold; font-size: 14px;">📅 Vaga de Teste Forçado</span>
    </div>
    """
    html_rodape = f"""
    <hr style="border: 0; border-top: 1px solid #e9ecef; margin: 30px 0;" />
    <div style="text-align: center; margin: 25px 0; font-family: sans-serif;">
        <a href="{item_link}" target="_blank" style="background-color: #28a745; color: #ffffff; padding: 14px 28px; text-decoration: none; font-weight: bold; border-radius: 4px; display: inline-block;">
            👉 Link de Destino Funcionando
        </a>
    </div>
    """
    return f"{html_topo}\n{ai_body}\n{html_rodape}"

def send_to_blogger(blogger_service, title: str, html_content: str):
    """Envia o post direto para a API."""
    body = {
        "kind": "blogger#post",
        "title": title,
        "content": html_content,
        "labels": ["Teste Automático"]
    }
    request = blogger_service.posts().insert(blogId=BLOG_ID, body=body)
    response = request.execute()
    print(f"🎉 [SUCESSO] O post foi aceito pela API! URL: {response.get('url')}")

# ==========================================
# DIRETRIZ PRINCIPAL DO TESTE FORÇADO
# ==========================================
def main():
    print("🧪 [MODO TESTE FORÇADO] Iniciando injeção direta no Blogger...")
    
    if not BLOG_ID:
        print("❌ [ERRO] Variável BLOG_ID não foi encontrada no topo do arquivo ou no ambiente.")
        return

    try:
        # Tenta obter o cliente autenticado
        blogger = get_blogger_service()
        
        # Dados estáticos para o teste
        titulo_teste = "Vaga de Teste Forçado - Motorista - " + datetime.datetime.now().strftime("%H:%M")
        link_teste = "https://google.com"
        
        print("🤖 Estruturando HTML padrão de teste...")
        html_final = build_final_html("<p>Se você está lendo isso, a API do Blogger está configurada e recebendo dados perfeitamente do GitHub Actions!</p>", link_teste)
        
        print("📤 Despachando carga útil para a API do Blogger...")
        send_to_blogger(blogger, titulo_teste, html_final)
        
    except Exception as e:
        print(f"💥 O TESTE FALHOU! O erro retornado foi: {e}")

if __name__ == "__main__":
    main()
