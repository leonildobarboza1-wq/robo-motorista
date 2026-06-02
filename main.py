import os
import datetime
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Importações dos módulos locais
from scraper import buscar_vagas_motorista
from filtro_ia import analisar_vaga_com_ia

# Coleta de credenciais do GitHub Environment
BLOG_ID_RAW = os.environ.get("BLOG_ID", "").strip().replace('"', '').replace("'", "")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN", "").strip()

def main():
    print("🚀 [PRODUÇÃO] Iniciando ciclo de postagem automatizada via API v3...")
    
    # Validação agressiva de chaves
    if not CLIENT_ID:
        raise ValueError("ERRO CRÍTICO: 'BLOGGER_CLIENT_ID' não foi encontrado nos Secrets do GitHub!")
    if not CLIENT_SECRET:
        raise ValueError("ERRO CRÍTICO: 'BLOGGER_CLIENT_SECRET' não foi encontrado nos Secrets do GitHub!")
    if not REFRESH_TOKEN:
        raise ValueError("ERRO CRÍTICO: 'BLOGGER_REFRESH_TOKEN' não foi encontrado nos Secrets do GitHub!")
    if not BLOG_ID_RAW:
        raise ValueError("ERRO CRÍTICO: 'BLOG_ID' não foi encontrado nos Secrets do GitHub!")

    blog_id_limpo = "".join(filter(str.isdigit, BLOG_ID_RAW))
    print(f"📡 Conectando ao Blog ID: {blog_id_limpo}")
    
    # Autenticação OAuth2
    credentials = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/blogger']
    )
    blogger_service = build('blogger', 'v3', credentials=credentials)
    
    # Executa raspagem de dados
    vagas = buscar_vagas_motorista()
    if not vagas:
        print("ℹ️ Nenhuma vaga nova localizada pelo scraper nesta rodada.")
        return

    vagas_publicadas = 0
    # Processa até 3 vagas para evitar estouro de limite
    for vaga in vagas[:3]:
        print(f"\n⏳ Pausa de segurança anti-bloqueio...")
        time.sleep(5)
        
        print(f"🧠 Enviando para análise da IA: {vaga['titulo']}")
        analise = analisar_vaga_com_ia(vaga['titulo'], vaga['descricao'])
        
        if analise and analise.get('valida'):
            print(f"🎯 Vaga Aprovada! Região: {analise['localizacao']}")
            
            data_str = datetime.datetime.now().strftime("%d/%m/%Y")
            hora_str = datetime.datetime.now().strftime("%H:%M")
            
            titulo_final = f"Vaga de Motorista em {analise['localizacao']} - {vaga['titulo']} ({data_str})"
            
            corpo_html = f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto;">
                <p style="color: #666; font-size: 13px; font-style: italic;">📅 Oportunidade atualizada em: {data_str} às {hora_str}</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin-bottom: 20px;">
                {analise['texto_html']}
                <br><br>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{vaga['link']}" target="_blank" style="display:inline-block;padding:15px 30px;background-color:#2eb85c;color:white;text-decoration:none;border-radius:5px;font-weight:bold;font-size:16px;">
                        Ver Vaga Original & Enviar Currículo
                    </a>
                </div>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <small style="color: #bbb;">Publicado automaticamente por Portal Emprego para Motorista</small>
            </div>
            """
            
            payload = {
                "kind": "blogger#post",
                "title": titulo_final,
                "content": corpo_html,
                "labels": ["Vagas", analise['localizacao'], "Automático"]
            }
            
            # Força o envio direto via API v3
            request = blogger_service.posts().insert(blogId=blog_id_limpo, body=payload)
            request.execute()
            vagas_publicadas += 1
            print(f"✅ Post criado com sucesso no Blogger!")
        else:
            print("❌ Vaga descartada pelos filtros da IA.")
            
    print(f"\n🚀 Ciclo finalizado! Total de novas postagens: {vagas_publicadas}")

if __name__ == "__main__":
    main()
