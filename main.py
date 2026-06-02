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
    """NOVO: Captura os links reais das fontes para evitar descartar títulos duplicados com conteúdos diferentes"""
    links_recentes = set()
    url_feed = f"{URL_MEU_BLOG.rstrip('/')}/feeds/posts/default?max-results=15"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url_feed, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
            namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
            
            # Varre o feed do Blogger procurando por links de referência guardados nas postagens
            for entry in root.findall('atom:entry', namespaces):
                # Como o blogger não guarda o link original de forma nativa, analisamos o conteúdo do post
                content_element = entry.find('atom:content', namespaces)
                if content_element is not None and content_element.text:
                    texto_post = content_element.text
                    # Se encontrarmos o link original que o robô injeta no botão de candidatura, bloqueamos ele
                    if 'href="' in texto_post:
                        parts = texto_post.split('href="')
                        for part in parts[1:]:
                            link_extraido = part.split('"')[0]
                            if "http" in link_extraido and URL_MEU_BLOG not in link_extraido:
                                links_recentes.add(link_extraido.strip().lower())
    except Exception as e:
        print(f"⚠️ Histórico compacto de links inacessível: {e}")
    return links_recentes

def minerar_feed_implacavel(lista_fontes, links_bloqueados):
    """NOVO: Filtra e valida o conteúdo comparando as URLs exclusivas"""
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
                
                # MUDANÇA CRUCIAL: O robô agora barra apenas se o LINK exato já foi publicado
                if link.strip().lower() in links_bloqueados:
                    print(f" ⏭️ Pulando link já existente: {title}")
                    continue
                
                img_url = ""
                media_content = item.find('{http://search.yahoo.com/mrss/}content')
                if media_content is not None and 'url' in media_content.attrib:
                    img_url = media_content.attrib['url']
                
                print(f"🎯 Oportunidade/Notícia Inédita Identificada: {title}")
                return title, desc, link, img_url
        except Exception as e:
            print(f"❌ Erro de conexão com {fonte['nome']}: {e}")
            continue
            
    return None, None, None, None

def gerar_conteudo_ia(titulo, conteudo, link_original, imagem_url, eh_noticia=False):
    client = genai.Client()
    data_postagem = obter_data_formatada()
    tipo_contexto = "notícia informativa" if eh_noticia else "vaga de emprego para motoristas"
    
    prompt = f"""
    Você é o editor principal do 'Portal Emprego para Motorista'.
    Monte um artigo limpo, profissional e muito bem diagramado em HTML focado em leitura mobile.

    Dados Brutos:
    - Título: {titulo}
    - Conteúdo original: {conteudo}
    
    REGRAS DE RETORNO:
    O seu texto de resposta deve usar obrigatoriamente a estrutura de tags abaixo:
    [TITULO_DO_POST]
    Crie o título limpo aqui.
    
    [CORPO_DO_POST]
    Texto formatado em HTML.
    """

    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        texto_ia = response.text
        
        linha_data_html = f'<p style="color: #c92a2a; font-size: 14px; font-weight: bold; margin-bottom: 18px; border-bottom: 1px solid #ddd; padding-bottom: 8px;">📅 Publicado no Portal em: {data_postagem}</p>\n'
        
        if "[CORPO_DO_POST]" in texto_ia:
            texto_ia = texto_ia.replace("[CORPO_DO_POST]", f"[CORPO_DO_POST]\n{linha_data_html}")
            
            if imagem_url:
                tag_img = f'<div style="text-align:center; margin-bottom: 15px;"><img src="{imagem_url}" style="max-width:100%; height:auto; border-radius:6px;"></div><br>\n'
                texto_ia = texto_ia.replace(linha_data_html, f"{linha_data_html}{tag_img}")
                
        if not eh_noticia and "[CORPO_DO_POST]" in texto_ia:
            botao_candidatura = f"""<br><br><div style="text-align: center;"><a href="{link_original}" target="_blank" rel="noopener" style="background-color: #e63946; color: white; padding: 14px 28px; text-decoration: none; font-weight: bold; border-radius: 6px; display: inline-block; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">👉 CLIQUE AQUI PARA SE CANDIDATAR A ESTA VAGA</a></div><br>"""
            texto_ia += botao_candidatura
        elif eh_noticia and "[CORPO_DO_POST]" in texto_ia:
            link_noticia = f"""<br><br><p style="text-align: center;"><i>Fonte da notícia original: <a href="{link_original}" target="_blank" rel="noopener">Acesse o artigo completo aqui</a></i></p>"""
            texto_ia += link_noticia

        return texto_ia
    except Exception as e:
        print(f"❌ Falha na IA: {e}")
        return f"[TITULO_DO_POST]\nInformativo do Trecho Diário\n\n[CORPO_DO_POST]\n{linha_data_html}<p>Confira os detalhes completos diretamente na fonte oficial: <a href='{link_original}'>Clique aqui</a></p>."

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
    print("🤖 Iniciando varredura baseada em URLs exclusivas...")
    links_publicados = listar_links_publicados_recentes()
    
    # 1. Tenta buscar vagas inéditas por URL
    t, d, l, i = minerar_feed_implacavel(FONTES_VAGAS, links_publicados)
    eh_noticia = False
    
    # 2. Se falhar, vai para as notícias
    if not t:
        print("⚠️ Nenhuma URL de vaga nova capturada. Ativando Plano B (Notícias)...")
        t, d, l, i = minerar_feed_implacavel(FONTES_NOTICIAS, links_publicados)
        eh_noticia = True
        
    if t:
        resultado_ia = gerar_conteudo_ia(t, d, l, i, eh_noticia)
        try:
            t_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
            c_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
            enviar_email_blogger(t_final, c_final)
        except Exception as e:
            print(f"⚠️ Erro ao quebrar tags da IA, enviando raw: {e}")
            enviar_email_blogger("Atualização - Portal do Motorista", resultado_ia)
    else:
        print("🛑 Sistema encerrado: Nenhuma URL nova restou nas fontes hoje.")
