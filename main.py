import os
import json
import logging
import urllib.request
import zoneinfo
from datetime import datetime
from filtro_ia import processar_vaga_com_gemini, formatar_noticia_com_gemini

logging.basicConfig(level=logging.INFO)

# --- FUNÇÕES DE CONTROLE ---

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
    # Filtro de Higiene: Ignora nossos testes
    palavras_proibidas = ["teste", "testando", "erro", "debug", "exemplo"]
    if any(p in titulo_candidato.lower() for p in palavras_proibidas):
        return True 
        
    tag_buscada = "link-" + link_candidato.replace("https://", "").replace("http://", "").replace("/", "-")[:30]
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?maxResults=5&fields=items(labels)"
    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as response:
            data = json.loads(response.read().decode('utf-8'))
            for post in data.get('items', []):
                if tag_buscada in post.get('labels', []):
                    return True
            return False
    except: return False

def postar_no_blogger(blog_id, access_token, titulo, conteudo, link_origem):
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/?isDraft=false"
    tag_unica = "link-" + link_origem.replace("https://", "").replace("http://", "").replace("/", "-")[:30]
    payload = {
        "kind": "blogger#post",
        "title": titulo,
        "content": conteudo,
        "labels": [tag_unica]
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), 
                                 headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as response:
        logging.info("Post publicado com sucesso!")

# --- BUSCAS E FLUXO (Mantendo as mesmas funções de busca anteriores) ---

def buscar_vagas_bne():
    try:
        url = "https://www.bne.com.br/vagas-de-emprego-para-motorista"
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10) as response:
            return {"titulo": "Motorista Profissional", "link": url, "fonte": "BNE", "descricao": "Vaga nacional"}
    except: return None

def buscar_noticia_nacional():
    try:
        url_feed = "https://estradao.estadao.com.br/feed/"
        with urllib.request.urlopen(urllib.request.Request(url_feed, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10) as response:
            xml = response.read().decode('utf-8')
            item = xml.split('<item>')[1].split('</item>')[0]
            titulo = item.split('<title>')[1].split('</title>')[0].replace('<![CDATA[', '').replace(']]>', '').strip()
            link = item.split('<link>')[1].split('</link>')[0].strip()
            return {"titulo": titulo, "link": link, "fonte_original": "Estradão", "descricao": "Notícia nacional"}
    except: return None

if __name__ == "__main__":
    blog_id = os.getenv('BLOG_ID')
    access_token = obter_token_oauth2()
    agora = datetime.now(zoneinfo.ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M")
    
    # Execução
    vaga = buscar_vagas_bne()
    if vaga and not verificar_se_ja_foi_publicado(blog_id, access_token, vaga['link'], vaga['titulo']):
        dados = processar_vaga_com_gemini(vaga, agora)
        postar_no_blogger(blog_id, access_token, dados['titulo_otimizado'], dados['conteudo_html'], vaga['link'])
    else:
        noticia = buscar_noticia_nacional()
        if noticia and not verificar_se_ja_foi_publicado(blog_id, access_token, noticia['link'], noticia['titulo']):
            dados = formatar_noticia_com_gemini(noticia, agora)
            postar_no_blogger(blog_id, access_token, dados['titulo_otimizado'], dados['conteudo_html'], noticia['link'])
