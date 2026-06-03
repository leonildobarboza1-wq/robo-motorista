import os
import json
import logging
import urllib.request
import zoneinfo
from datetime import datetime
from filtro_ia import processar_vaga_com_gemini, formatar_noticia_com_gemini

logging.basicConfig(level=logging.INFO)

# --- FUNÇÕES DE API E BUSCA ---

def obter_token_oauth2():
    client_id = os.getenv('BLOGGER_CLIENT_ID')
    client_secret = os.getenv('BLOGGER_CLIENT_SECRET')
    refresh_token = os.getenv('BLOGGER_REFRESH_TOKEN')
    url = "https://oauth2.googleapis.com/token"
    payload = f"client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}&grant_type=refresh_token"
    req = urllib.request.Request(url, data=payload.encode('utf-8'), headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))['access_token']

    def verificar_se_ja_foi_publicado(blog_id, access_token, link_candidato, titulo_candidato):
    # 1. Ignora automaticamente títulos que contenham palavras de teste
    palavras_proibidas = ["testeee", "testandooo", "errooo", "debugeee", "exemplooo"]
    if any(p in titulo_candidato.lower() for p in palavras_proibidas):
        return True # Trata como se já tivesse sido publicado para o robô pular
        
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?maxResults=5&fields=items(labels,title)"
    headers = {'Authorization': f'Bearer {access_token}'}
    # ... resto da função de checagem de etiquetas continua igual ...
    
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?maxResults=5&fields=items(content)"
    headers = {'Authorization': f'Bearer {access_token}'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            for post in data.get('items', []):
                if link_candidato in post.get('content', ''):
                    return True
            return False
    except:
        return False

# --- FUNÇÕES DE BUSCA DE DADOS ---

def buscar_vagas_bne():
    url = "https://www.bne.com.br/vagas-de-emprego-para-motorista"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as response:
            return {"titulo": "Motorista Categoria D/E", "link": url, "fonte": "BNE", "descricao": "Vaga nacional"}
    except: return None

def buscar_vagas_trabalha_brasil():
    url = "https://www.trabalhabrasil.com.br/vagas-vaga-de-emprego-de-motorista"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15) as response:
            return {"titulo": "Motorista Carreteiro", "link": url, "fonte": "Trabalha Brasil", "descricao": "Vaga nacional"}
    except: return None

def buscar_noticia_nacional():
    url_feed = "https://estradao.estadao.com.br/feed/"
    try:
        with urllib.request.urlopen(urllib.request.Request(url_feed, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15) as response:
            xml = response.read().decode('utf-8')
            item = xml.split('<item>')[1].split('</item>')[0]
            titulo = item.split('<title>')[1].split('</title>')[0].replace('<![CDATA[', '').replace(']]>', '').strip()
            link = item.split('<link>')[1].split('</link>')[0].strip()
            return {"titulo": titulo, "link": link, "fonte_original": "Estradão", "descricao": "Notícia nacional", "url_imagem": ""}
    except:
        return {"titulo": "Notícia do Setor", "link": "https://blogdocaminhoneiro.com", "fonte_original": "Blog do Caminhoneiro", "descricao": "Notícia de trânsito", "url_imagem": ""}

# --- FLUXO PRINCIPAL ---

def postar_no_blogger(blog_id, access_token, titulo, conteudo):
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/?isDraft=false"
    payload = {"kind": "blogger#post", "title": titulo, "content": conteudo}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as response:
        logging.info("Post publicado!")

if __name__ == "__main__":
    blog_id = os.getenv('BLOG_ID')
    access_token = obter_token_oauth2()
    agora = datetime.now(zoneinfo.ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M")
    
    # Tentativa de Vaga
    vaga = buscar_vagas_bne() or buscar_vagas_trabalha_brasil()
    if vaga and not verificar_se_ja_foi_publicado(blog_id, access_token, vaga['link']):
        dados = processar_vaga_com_gemini(vaga, agora)
        conteudo = dados['conteudo_html'] + f""
        postar_no_blogger(blog_id, access_token, dados['titulo_otimizado'], conteudo)
    else:
        # Tentativa de Notícia
        noticia = buscar_noticia_nacional()
        if not verificar_se_ja_foi_publicado(blog_id, access_token, noticia['link']):
            dados = formatar_noticia_com_gemini(noticia, agora)
            conteudo = dados['conteudo_html'] + f""
            postar_no_blogger(blog_id, access_token, dados['titulo_otimizado'], conteudo)
        else:
            logging.info("Nenhum conteúdo inédito encontrado.")
