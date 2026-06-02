import os
import datetime
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Importando as suas funções originais de raspagem e IA
from scraper import buscar_vagas_motorista
from filtro_ia import analisar_vaga_com_ia

# =====================================================================
# CONFIGURAÇÕES VIA GITHUB SECRETS (CONTA 2)
# =====================================================================
BLOG_ID_RAW = os.environ.get("BLOG_ID", "").strip().replace('"', '').replace("'", "")
CLIENT_ID = os.environ.get("BLOGGER_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("BLOGGER_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("BLOGGER_REFRESH_TOKEN", "").strip()

def conectar_api_blogger():
    """Faz a conexão direta e segura com o Blogger usando OAuth2"""
    blog_id_limpo = "".join(filter(str.isdigit, BLOG_ID_RAW))
    
    credentials = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/blogger']
    )
    service = build('blogger', 'v3', credentials=credentials)
    return service, blog_id_limpo

def enviar_vaga_para_o_blog_api(service, blog_id, titulo, localizacao, conteudo_html, link_original):
    """Envia a vaga diretamente para a API do Blogger com data formatada"""
    
    # Gerando a data atual para carimbar na postagem
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y")
    hora_atual = datetime.datetime.now().strftime("%H:%M")
    
    # Incluindo a data no título do post
    assunto_post = f"Vaga de Motorista em {localizacao} - {titulo} ({data_atual})"
    
    # Construindo o corpo estruturado com a data visível no topo
    corpo_html = f"""
    <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <p style="color: #777; font-size: 13px; font-style: italic; margin-bottom: 15px;">
            📅 Atualizado em: {data_atual} às {hora_atual}
        </p>
        
        {conteudo_html}
        
        <br><br>
        <p><strong>Como se candidatar:</strong></p>
        <p>
            <a href="{link_original}" target="_blank" style="display:inline-block;padding:12px 24px;background-color:#28a745;color:white;text-decoration:none;border-radius:5px;font-weight:bold;box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                Ver Vaga Original e Enviar Currículo
            </a>
        </p>
        <br>
        <hr style="border: 0; border-top: 1px solid #eee;">
        <small style="color: #999;">Publicado por: Portal Emprego para Motorista</small>
    </div>
    """
    
    payload = {
        "kind": "blogger#post",
        "title": assunto_post,
        "content": corpo_html,
        "labels": ["Vagas", localizacao, "Motorista"]
    }
    
    try:
        request = service.posts().insert(blogId=blog_id, body=payload)
        response = request.execute()
        print(f"✅ Sucesso via API! Vaga publicada: {titulo} em {localizacao}")
        print(f"🔗 Link do Post: {response.get('url')}")
        return True
    except Exception as e:
        print(f"❌ Erro ao postar na API do Blogger: {e}")
        return False

def rodar_robo_completo():
    print("=== INICIANDO O ROBÔ AUTOMÁTICO VIA API (CONTA 2) ===")
    
    # 1. Validação de segurança das credenciais
    if not BLOG_ID_RAW or not CLIENT_ID or not REFRESH_TOKEN:
        raise ValueError("ERRO: Chaves de autenticação do Blogger não encontradas nos Secrets do GitHub.")
        
    # 2. Conecta ao Blogger antes de iniciar o processo demorado
    blogger_service, blog_id = conectar_api_blogger()
    print(f"📡 Conectado com sucesso ao Blog ID: {blog_id}")
    
    # 3. Busca as vagas usando seu scraper original
    vagas_brutas = buscar_vagas_motorista()
    
    if not vagas_brutas:
        print("Nenhuma vaga encontrada para processar.")
        return
        
    vagas_publicadas = 0
    # LIMITADOR: Processa no máximo 4 vagas por rodada para respeitar a cota da IA
    maximo_vagas_processar = vagas_brutas[:4]
    
    for vaga in maximo_vagas_processar:
        print(f"\nAguardando intervalo de segurança para a IA...")
        time.sleep(4)  # Pausa obrigatória para o Gemini não dar erro 429
        
        print(f"Analisando: {vaga['titulo']}...")
        analise = analisar_vaga_com_ia(vaga['titulo'], vaga['descricao'])
        
        if analise and analise['valida']:
            print(f"-> Aprovada pela IA! Localizado em: {analise['localizacao']}")
            
            # Envia usando o novo motor da API v3
            postou = enviar_vaga_para_o_blog_api(
                service=blogger_service,
                blog_id=blog_id,
                titulo=vaga['titulo'],
                localizacao=analise['localizacao'],
                conteudo_html=analise['texto_html'],
                link_original=vaga['link']
            )
            
            if postou:
                vagas_publicadas += 1
                time.sleep(3)
        else:
            print("-> Reprovada ou descartada pela IA.")
            
    print(f"\n=== PROCESSO CONCLUÍDO: {vagas_publicadas} vagas novas no seu Portal! ===")

if __name__ == "__main__":
    rodar_robo_completo()
