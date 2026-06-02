import os
import time
import random
import smtplib
import urllib.request
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from google import genai

# ==========================================
# CONFIGURAÇÕES DO PORTAL DE VAGAS
# ==========================================
URL_MEU_BLOG = "https://empregomotoristas.blogspot.com"
EMAIL_SECRETO_BLOGGER = os.environ.get("EMAIL_SECRETO_BLOGGER")

GMAIL_REMETENTE = os.environ.get("GMAIL_REMETENTE")
GMAIL_SENHA_APP = os.environ.get("GMAIL_SENHA_APP")

FONTES_VAGAS = [
    {"nome": "Estradão - Estadão Vagas", "url": "https://estradao.estadao.com.br/feed/"},
    {"nome": "Giro do Caminhoneiro", "url": "https://girodocaminhoneiro.com.br/feed/"},
    {"nome": "Chapa Comigo Vagas", "url": "https://chapacomigo.com.br/feed/"}
]

FONTES_NOTICIAS = [
    {"nome": "NTC e Logistica", "url": "https://www.ntcelogistica.org.br/feed/"},
    {"nome": "Fetrancesg Notícias", "url": "https://fetrancesg.com.br/feed/"},
    {"nome": "Estradas.com Informativos", "url": "https://estradas.com.br/feed/"}
]

def obter_data_formatada():
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    hoje = datetime.now()
    return f"{hoje.day} de {meses[hoje.month - 1]} de {hoje.year}"

def listar_links_publicados_recentes():
    links_recentes = set()
    url_feed = f"{URL_MEU_BLOG.rstrip('/')}/feeds/posts/default?max-results=15"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url_feed, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
            namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', namespaces):
                content_element = entry.find('atom:content', namespaces)
                if content_element is not None and content_element.text:
                    texto_post = content_element.text
                    if 'href="' in texto_post:
                        parts = texto_post.split('href="')
                        for part in parts[1:]:
                            link_extraido = part.split('"')[0]
                            if "http" in link_extraido and URL_MEU_BLOG not in link_extraido:
                                links_recentes.add(link_extraido.strip().lower())
    except Exception as e:
        print(f"⚠️ Histórico inacessível: {e}")
    return links_recentes

def minerar_feed_forcado(lista_fontes, links_bloqueados):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    fontes_mistas = list(lista_fontes)
    random.shuffle(fontes_mistas)
    
    for fonte in fontes_mistas:
        try:
            req = urllib.request.Request(fonte['url'], headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                root = ET.fromstring(response.read())
            items = root.findall('.//item')
            if not items: continue
            
            for item in items:
                title = item.find('title').text if item.find('title') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                
                if link and title:
                    img_url = ""
                    media_content = item.find('{http://search.yahoo.com/mrss/}content')
                    if media_content is not None and 'url' in media_content.attrib:
                        img_url = media_content.attrib['url']
                    return title, desc, link, img_url
        except Exception as e:
            continue
    return None, None, None, None

def gerar_corpo_html_ia(titulo, conteudo, link_original, imagem_url, eh_noticia=False):
    client = genai.Client()
    data_postagem = obter_data_formatada()
    
    prompt = f"""
    Você é o redator do 'Portal Emprego para Motorista'. 
    Reescreva os dados abaixo em um artigo fluido e profissional.
    Use APENAS tags simples como <p>, <b> e <br>. Não crie tabelas nem use estilos CSS complexos.
    
    Retorne apenas o texto puro do artigo, sem blocos ```html.
    - Título: {titulo}
    - Conteúdo: {conteudo}
    """

    # HTML simplificado ao extremo para passar direto pelo filtro anti-spam do Blogger
    html_topo = f"<p><b>📅 Publicado no Portal em: {data_postagem}</b></p><br>\n"
    
    if imagem_url:
        html_topo += f'<p><img src="{imagem_url}" style="max-width:100%; height:auto;"></p><br>\n'

    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        corpo_ia = response.text.replace("```html", "").replace("```", "").strip()
        
        html_final = html_topo + corpo_ia
        
        if not eh_noticia:
            html_final += f"""<br><br><p><b>👉 <a href="{link_original}" target="_blank">CLIQUE AQUI PARA SE CANDIDATAR A ESTA VAGA</a></b></p>"""
        else:
            html_final += f"""<br><br><p><i>Fonte original: <a href="{link_original}" target="_blank">Acesse o conteúdo completo aqui</a></i></p>"""
            
        return html_final
    except Exception as e:
        return f"{html_topo}<p>Confira os detalhes completos direto na fonte oficial: <a href='{link_original}'>Clique aqui para acessar</a></p>"

def enviar_email_blogger(titulo, conteudo):
    if not EMAIL_SECRETO_BLOGGER: return
    msg = MIMEMultipart()
    msg['From'] = GMAIL_REMETENTE
    msg['To'] = EMAIL_SECRETO_BLOGGER
    msg['Subject'] = titulo
    msg.attach(MIMEText(conteudo, 'html', 'utf-8'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_REMETENTE, GMAIL_SENHA_APP)
        server.sendmail(GMAIL_REMETENTE, EMAIL_SECRETO_BLOGGER, msg.as_string())
        server.quit()
        print(f"🎉 Sincronização concluída: {titulo}")
    except Exception as e:
        print(f"❌ Falha de envio: {e}")

if __name__ == "__main__":
    links_publicados = listar_links_publicados_recentes()
    t, d, l, i = minerar_feed_forcado(FONTES_VAGAS, links_publicados)
    eh_noticia = False
    
    if not t:
        t, d, l, i = minerar_feed_forcado(FONTES_NOTICIAS, links_publicados)
        eh_noticia = True
        
    if t:
        corpo_final = gerar_corpo_html_ia(t, d, l, i, eh_noticia)
        enviar_email_blogger(t, corpo_final)
