import os
import sys
import logging
import urllib.request
import urllib.parse
import json
from datetime import datetime
import zoneinfo

# Importações locais
from scraper import buscar_vagas
from filtro_ia import processar_vaga_com_gemini

logging.basicConfig(level=logging.INFO)

def obter_access_token(client_id, client_secret, refresh_token):
    """Gera um Access Token válido a partir do Refresh Token (OAuth2)"""
    url = "https://oauth2.googleapis.com/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    data = urllib.parse.urlencode(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['access_token']
    except Exception as e:
        logging.error("Erro crítico ao renovar o Access Token via OAuth2.")
        if hasattr(e, 'read'):
            logging.error(f"Detalhes do erro OAuth2: {e.read().decode('utf-8')}")
        raise e

def postar_no_blogger(blog_id, access_token, titulo, conteudo):
    """Envia a requisição POST para publicar no Blogger"""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/"
    
    # Payload exigido pela API v3 do Blogger
    payload = {
        "kind": "blogger#post",
        "title": titulo,
        "content": conteudo
    }
    
    data = json.dumps(payload).encode('utf-8')
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            logging.info(f"Post publicado com sucesso! ID: {res_data.get('id')}")
            return True
    except Exception as e:
        logging.error("Erro ao postar na API do Blogger.")
        if hasattr(e, 'read'):
            logging.error(f"Resposta de erro do Blogger: {e.read().decode('utf-8')}")
        raise e

def main():
    # Carregando e validando variáveis de ambiente
    blog_id = os.getenv('BLOG_ID')
    api_key_gemini = os.getenv('GOOGLE_API_KEY')
    client_id = os.getenv('BLOGGER_CLIENT_ID')
    client_secret = os.getenv('BLOGGER_CLIENT_SECRET')
    refresh_token = os.getenv('BLOGGER_REFRESH_TOKEN')
    
    if not all([blog_id, api_key_gemini, client_id, client_secret, refresh_token]):
        logging.error("ERRO CRÍTICO: Chaves ou Secrets faltando no ambiente do GitHub.")
        sys.exit(1)
        
    # 1. Coleta das vagas
    vagas = buscar_vagas()
    if not vagas:
        logging.warning("Nenhuma vaga encontrada para processar.")
        return
        
    # Usaremos a primeira vaga válida capturada para o ciclo atual
    vaga_alvo = vagas[0]
    
    # 2. Filtragem e formatação com Inteligência Artificial
    logging.info("Enviando vaga para análise do Gemini...")
    dados_vaga = processar_vaga_com_gemini(vaga_alvo, api_key_gemini)
    
    if not dados_vaga.get('e_motorista'):
        logging.warning("A vaga analisada não passou no filtro de validação para Motoristas.")
        return
        
    # 3. Preparação dos dados dinâmicos de Data/Hora (Fuso do Brasil)
    fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
    
    titulo_final = f"{dados_vaga['titulo_otimizado']} - Atualizado em {agora}"
    conteudo_final = f"""
    {dados_vaga['conteudo_html']}
    <br><hr>
    <p><small><i>Post automatizado gerado em: {agora} (Horário de Brasília)</i></small></p>
    """
    
    # 4. Autenticação e Publicação
    try:
        logging.info("Gerando token de acesso OAuth2...")
        access_token = obter_access_token(client_id, client_secret, refresh_token)
        
        logging.info("Enviando postagem para o Blogger...")
        postar_no_blogger(blog_id, access_token, titulo_final, conteudo_final)
        
    except Exception as erro_final:
        logging.error(f"Execução falhou na etapa de publicação: {erro_final}")
        sys.exit(1) # Força o GitHub Actions a ficar vermelho!

if __name__ == '__main__':
    main()
