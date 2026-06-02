import os
import sys
import logging
import urllib.request
import urllib.parse
import json
from datetime import datetime
import zoneinfo

# Importações dos novos módulos modulares
from scrapers_vagas import buscar_indeed, buscar_simplyhired, buscar_jooble, buscar_trabalhabrasil
from scrapers_noticias import buscar_noticia_caminhoneiro
from filtro_ia import processar_vaga_com_gemini, formatar_noticia_com_gemini

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
            logging.error(f"Detalhes: {e.read().decode('utf-8')}")
        raise e

def obter_ultimos_titulos_blogger(blog_id, access_token):
    """Busca os títulos das últimas postagens do blog para evitar duplicidade"""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?maxResults=15&fetchBodies=false"
    headers = {'Authorization': f'Bearer {access_token}'}
    req = urllib.request.Request(url, headers=headers, method='GET')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            items = res_data.get('items', [])
            # Armazena apenas o começo do título original, ignorando as estampas de tempo
            return [item['title'].split(" - ")[0].strip() for item in items]
    except Exception as e:
        logging.warning(f"Não foi possível buscar posts antigos do Blogger: {e}")
        return []

def postar_no_blogger(blog_id, access_token, titulo, conteudo):
    """Envia a requisição POST para publicar no Blogger forçando status ativo (isDraft=false)"""
    # O parâmetro isDraft=false força o post a ficar visível instantaneamente no painel público
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/?isDraft=false"
    
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
            logging.info(f"Post publicado com sucesso absoluto! ID: {res_data.get('id')}")
            return True
    except Exception as e:
        logging.error("Erro ao postar na API do Blogger.")
        if hasattr(e, 'read'):
            logging.error(f"Resposta do Blogger: {e.read().decode('utf-8')}")
        raise e

def main():
    # 1. Validação de Ambiente
    blog_id = os.getenv('BLOG_ID')
    api_key_gemini = os.getenv('GOOGLE_API_KEY')
    client_id = os.getenv('BLOGGER_CLIENT_ID')
    client_secret = os.getenv('BLOGGER_CLIENT_SECRET')
    refresh_token = os.getenv('BLOGGER_REFRESH_TOKEN')
    
    if not all([blog_id, api_key_gemini, client_id, client_secret, refresh_token]):
        logging.error("ERRO CRÍTICO: Chaves ou Secrets faltando no ambiente do GitHub.")
        sys.exit(1)
        
    # 2. Conectar ao Blogger e Puxar Histórico Anti-Duplicação
    try:
        logging.info("Iniciando autenticação OAuth2...")
        access_token = obter_access_token(client_id, client_secret, refresh_token)
        titulos_publicados = obter_ultimos_titulos_blogger(blog_id, access_token)
        logging.info(f"Títulos recentes mapeados no blog: {len(titulos_publicados)}")
    except Exception as e:
        sys.exit(1)

    # 3. Executar o Carrossel de Vagas (Ordem de Prioridade)
    lista_fontes_vagas = [buscar_indeed, buscar_simplyhired, buscar_jooble, buscar_trabalhabrasil]
    vaga_selecionada = None
    
    logging.info("Varrendo fontes de vagas em busca de novidades...")
    for buscar_fonte in lista_fontes_vagas:
        vagas_da_fonte = buscar_fonte()
        
        for vaga in vagas_da_fonte:
            titulo_vaga_limpo = vaga['titulo'].strip()
            
            # Validação: Se o título da vaga já existir no histórico recente, pula
            ja_existe = any(titulo_vaga_limpo in t or t in titulo_vaga_limpo for t in titulos_publicados)
            
            if not ja_existe:
                vaga_selecionada = vaga
                break # Encontrou uma vaga inédita nesta fonte
                
        if vaga_selecionada:
            break # Interrompe a busca nas outras fontes, pois já temos o alvo do dia
            
    # 4. Preparação das Variáveis de Tempo (Fuso Horário de Brasília)
    fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
    
    titulo_final = ""
    conteudo_final = ""

    # 5. Processamento e Tomada de Decisão do Conteúdo
    if vaga_selecionada:
        logging.info(f"Vaga inédita selecionada para processamento: {vaga_selecionada['titulo']}")
        dados_ia = processar_vaga_com_gemini(vaga_selecionada, api_key_gemini)
        
        if dados_ia.get('e_motorista'):
            titulo_final = f"{dados_ia['titulo_otimizado']} - Vaga de Emprego"
            conteudo_final = dados_ia['conteudo_html']
        else:
            logging.warning("A vaga selecionada foi descartada pelo filtro de IA por não ser de motorista.")
            vaga_selecionada = None # Força a ativação da contingência de notícias

    # Se NÃO encontrou vaga inédita OU se a IA rejeitou a vaga selecionada
    if not vaga_selecionada:
        logging.warning("⚠️ Nenhuma vaga de emprego inédita encontrada hoje. Ativando Plano B de Notícias!")
        noticia_bruta = buscar_noticia_caminhoneiro()
        
        dados_noticia = formatar_noticia_com_gemini(noticia_bruta, api_key_gemini)
        titulo_final = dados_noticia['titulo_otimizado']
        conteudo_final = dados_noticia['conteudo_html']

    # Adiciona o carimbo final de automação comum a ambos os tipos de post
    conteudo_final += f"""
    <br><hr>
    <p><small><i>Post automatizado atualizado em: {agora} (Horário de Brasília)</i></small></p>
    """

    # 6. Publicação Final Garantida
    try:
        logging.info(f"Enviando nova postagem ao Blogger: '{titulo_final}'")
        postar_no_blogger(blog_id, access_token, titulo_final, conteudo_final)
        logging.info("Fluxo diário finalizado com sucesso absoluto!")
    except Exception as erro_final:
        logging.error(f"Falha crítica no envio final: {erro_final}")
        sys.exit(1)

if __name__ == '__main__':
    main()
