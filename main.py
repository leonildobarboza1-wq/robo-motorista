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

# Fontes de Vagas
FONTES_VAGAS = [
    {"nome": "Estradão - Estadão Vagas", "url": "https://estradao.estadao.com.br/feed/"},
    {"nome": "Giro do Caminhoneiro", "url": "https://girodocaminhoneiro.com.br/feed/"},
    {"nome": "Chapa Comigo Vagas", "url": "https://chapacomigo.com.br/feed/"}
]

# Fontes de Notícias
FONTES_NOTICIAS = [
    {"nome": "NTC e Logistica", "url": "https://www.ntcelogistica.org.br/feed/"},
    {"nome": "Fetrancesg Notícias", "url": "https://fetrancesg.com.br/feed/"},
    {"nome": "Estradas.com Informativos", "url": "https://estradas.com.br/feed/"},
    {"nome": "CNT - Confederação Nacional do Transporte", "url": "https://www.cnt.org.br/rss/noticias"},
    {"nome": "Ministério da Infraestrutura", "url": "https://www.gov.br/transportes/pt-br/noticias/RSS"}
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
        print(f"⚠️ Histórico de links inacessível: {e}")
    return links_recentes

def minerar_feed_implacavel(lista_fontes, links_bloqueados):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    fontes_mistas = list(lista_fontes)
    random.shuffle(fontes_mistas)
    
    for fonte in fontes_mistas:
        print(f"🔍 Vasculhando a fonte: {fonte['nome']}...")
        try:
            req = urllib.request.Request(fonte['url'], headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                root = ET.fromstring(response.read())
            
            items = root.findall('.//item')
            if not items:
                continue
                
            random.shuffle(items)
            for item in items:
                title = item.find('title').text if item.find('title') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                
                if not link or not title:
                    continue
                
                if link.strip().lower() in links_bloqueados:
                    print(f" ⏭️ Link já publicado no blog anteriormente: {title}")
                    continue
                
                img_url = ""
                media_content = item.find('{http://search.yahoo.com/mrss/}content')
                if media_content is not None and 'url' in media_content.attrib:
                    img_url = media_content.attrib['url']
                
                print(f"🎯 Conteúdo Inédito Identificado: {title}")
                return title, desc, link, img_url
        except Exception as e:
            print(f"❌ Erro de conexão com {fonte['nome']}: {e}")
            continue
            
    return None, None, None, None

def gerar_corpo_html_ia(titulo, conteudo, link_original, imagem_url, eh_noticia=False):
    """Gera exclusivamente o corpo da mensagem, eliminando erros de quebra de texto"""
    client = genai.Client()
    data_postagem = obter_data_formatada()
    tipo_contexto = "notícia informativa para caminhoneiros" if eh_noticia else "vaga de emprego para motoristas profissionais"
    
    prompt = f"""
    Você é o redator do 'Portal Emprego para Motorista'. 
    Reescreva os dados abaixo em um artigo fluido, profissional e muito bem estruturado em HTML focado em leitura mobile.

    Dados de Origem:
    - Assunto: {titulo}
    - Detalhes: {conteudo}
    
    REGRAS OBRIGATÓRIAS:
    - Retorne APENAS o código HTML do artigo.
    - Comece o texto direto com os parágrafos ou subtítulos explicativos.
    - Use tags como <p>, <h2>, <strong>, <ul>, <li> para organizar.
    - Não repita o título dentro do texto.
    - NÃO use blocos de código com marcação ```html, retorne o código puro diretamente.
    """

    # Injeção manual da data direto via código Python
    linha_data_html = f'<p style="color: #c92a2a; font-size: 14px; font-weight: bold; margin-bottom: 18px; border-bottom: 1px solid #ddd; padding-bottom: 8px;">📅 Publicado no Portal em: {data_postagem}</p>\n'
    
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        corpo_ia = response.text.replace("```html", "").replace("```", "").strip()
        
        # Monta a estrutura final juntando a imagem e a data
        html_final = linha_data_html
        if imagem_url:
            html_final += f'<div style="text-align:center; margin-bottom: 20px;"><img src="{imagem_url}" style="max-width:100%; height:auto; border-radius:6px;"></div><br>\n'
        
        html_final += corpo_ia
        
        # Adiciona botões ou links de rodapé de forma segura
        if not eh_noticia:
            html_final += f"""<br><br><div style="text-align: center;"><a href="{link_original}" target="_blank" rel="noopener" style="background-color: #e63946; color: white; padding: 14px 28px; text-decoration: none; font-weight: bold; border-radius: 6px; display: inline-block; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">👉 CLIQUE AQUI PARA SE CANDIDATAR A ESTA VAGA</a></div><br>"""
        else:
            html_final += f"""<br><br><p style="text-align: center;"><i>Fonte da notícia original: <a href="{link_original}" target="_blank" rel="noopener">Acesse o artigo completo aqui</a></i></p>"""
            
        return html_final
    except Exception as e:
        print(f"❌ Falha na IA: {e}")
        return f"{linha_data_html}<p>Confira os detalhes completos diretamente na fonte oficial: <a href='{link_original}'>Clique aqui</a></p>."

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
        print(f"🎉 Publicação enviada com sucesso ao Blogger: {titulo}")
    except Exception as e:
        print(f"❌ Falha crítica no envio do e-mail: {e}")

if __name__ == "__main__":
    print("🤖 Iniciando varredura à prova de falhas...")
    links_publicados = listar_links_publicados_recentes()
    
    # 1. Tenta vagas
    t, d, l, i = minerar_feed_implacavel(FONTES_VAGAS, links_publicados)
    eh_noticia = False
    
    # 2. Se não houver vaga inédita, busca notícia
    if not t:
        print("⚠️ Nenhuma vaga nova hoje. Buscando notícias do trecho...")
        t, d, l, i = minerar_feed_implacavel(FONTES_NOTICIAS, links_publicados)
        eh_noticia = True
        
    if t:
        # Simplificado: Título vai direto do feed e o corpo vem limpo da IA
        corpo_final = gerar_corpo_html_ia(t, d, l, i, eh_noticia)
        enviar_email_blogger(t, corpo_final)
    else:
        print("🛑 Nenhuma nova URL disponível em nenhuma das fontes.")
