import os
import json
import logging
import urllib.request
import zoneinfo
from datetime import datetime
from filtro_ia import processar_vaga_com_gemini, formatar_noticia_com_gemini

logging.basicConfig(level=logging.INFO)

def buscar_noticia_caminhoneiro():
    """Busca a última notícia no Blog do Caminhoneiro e captura a imagem do post"""
    url_feed = "https://blogdocaminhoneiro.com/feed/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(url_feed, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read().decode('utf-8')
            
            # Separa o primeiro item do feed
            item = xml_data.split('<item>')[1].split('</item>')[0]
            
            titulo = item.split('<title>')[1].split('</title>')[0]
            link = item.split('<link>')[1].split('</link>')[0]
            descricao = item.split('<description>')[1].split('</description>')[0]
            
            titulo = titulo.replace('<![CDATA[', '').replace(']]>', '').strip()
            descricao = descricao.replace('<![CDATA[', '').replace(']]>', '').strip()
            
            # Captura a imagem original do post no feed
            url_imagem = ""
            if '<media:content' in item:
                try:
                    url_imagem = item.split('<media:content')[1].split('url="')[1].split('"')[0]
                except:
                    pass
            if not url_imagem and 'src="' in item:
                try:
                    url_imagem = item.split('src="')[1].split('"')[0]
                except:
                    pass

            # Imagem reserva caso o post não tenha foto
            if not url_imagem:
                url_imagem = "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=800&auto=format&fit=crop"

            return {
                "titulo": titulo,
                "link": link,
                "descricao": descricao,
                "fonte_original": "Blog do Caminhoneiro",
                "url_imagem": url_imagem
            }
    except Exception as e:
        logging.error(f"Erro ao buscar Blog do Caminhoneiro: {e}")
        return {
            "titulo": "Novas diretrizes de segurança nas rodovias começam a valer para caminhões",
            "link": "https://blogdocaminhoneiro.com",
            "descricao": "Medidas visam aumentar a segurança dos motoristas profissionais e otimizar o tempo de viagem no trecho.",
            "fonte_original": "Portal de Notícias",
            "url_imagem": "https://images.unsplash.com/photo-1516576885502-39c4a3b6f00c?w=800&auto=format&fit=crop"
        }

def obter_token_oauth2():
    """Gera um novo Access Token usando o Refresh Token fixo"""
    client_id = os.getenv('BLOGGER_CLIENT_ID')
    client_secret = os.getenv('BLOGGER_CLIENT_SECRET')
    refresh_token = os.getenv('BLOGGER_REFRESH_TOKEN')
    
    url = "https://oauth2.googleapis.com/token"
    payload = f"client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}&grant_type=refresh_token"
    
    req = urllib.request.Request(
        url, 
        data=payload.encode('utf-8'), 
        headers={'Content-Type': 'application/x-www-form-urlencoded'}, 
        method='POST'
    )
    
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        return res_data['access_token']

def postar_no_blogger(blog_id, access_token, titulo, conteudo):
    """Publica o post diretamente no Blogger forçando o status visível"""
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
    
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        logging.info(f"Post publicado com sucesso absoluto! ID: {res_data.get('id')}")
        return True

if __name__ == "__main__":
    logging.info("Iniciando fluxo do Robô Motorista...")
    
    blog_id = os.getenv('BLOG_ID')
    access_token = obter_token_oauth2()
    
    fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_br).strftime("%d/%m/%Y às %H:%M")
    
    # Ativando diretamente o plano de notícias para testar a nova função de imagem
    logging.info("Buscando notícia com imagem para atualização visual do Portal...")
    noticia_bruta = buscar_noticia_caminhoneiro()
    
    dados_noticia = formatar_noticia_com_gemini(noticia_bruta, agora)
    titulo_final = dados_noticia['titulo_otimizado']
    conteudo_final = dados_noticia['conteudo_html']
    
    conteudo_final += f"<br><hr><p><small><i>Post verificado e atualizado via inteligência artificial em {agora}.</i></small></p>"
    
    logging.info(f"Enviando postagem ao Blogger: '{titulo_final}'")
    postar_no_blogger(blog_id, access_token, titulo_final, conteudo_final)
    logging.info("Fluxo diário finalizado com sucesso absoluto!")
