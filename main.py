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

# 6 Fontes Ativas e Testadas
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

def listar_titulos_publicados_recentes():
    """Coleta apenas os últimos posts do blog para não repetir o que é muito recente"""
    titulos_recentes = set()
    url_feed = f"{URL_MEU_BLOG.rstrip('/')}/feeds/posts/default?max-results=30"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        req = urllib.request.Request(url_feed, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
            namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', namespaces):
                title_element = entry.find('atom:title', namespaces)
                if title_element is not None and title_element.text:
                    titulos_recentes.add(title_element.text.strip().lower())
    except Exception as e:
        print(f"⚠️ Histórico do blog temporariamente inacessível: {e}")
    return titulos_recentes

def minerar_feed_implacavel(lista_fontes, titulos_bloqueados):
    """Vasculha TODAS as fontes da lista até encontrar uma postagem inédita"""
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
                print(f" Empty: Fonte {fonte['nome']} sem itens no momento.")
                continue
                
            random.shuffle(items)
            for item in items:
                title = item.find('title').text if item.find('title') is not None else ""
                desc = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text if item.find('link') is not None else ""
                
                if not title:
                    continue
                
                # Bloqueio anti-repetição ativa
                if title.strip().lower() in titulos_bloqueados:
                    continue
                
                img_url = ""
                media_content = item.find('{http://search.yahoo.com/mrss/}content')
                if media_content is not None and 'url' in media_content.attrib:
                    img_url = media_content.attrib['url']
                
                print(f"🎯 Conteúdo Inédito Encontrado em '{fonte['nome']}': {title}")
                return title, desc, link, img_url
        except Exception as e:
            print(f"❌ Falha temporária ao ler {fonte['nome']}: {e}")
            continue
            
    return None, None, None, None

def gerar_conteudo_ia(titulo, conteudo, link_original, imagem_url, eh_noticia=False):
    client = genai.Client()
    data_postagem = obter_data_formatada()
    tipo_contexto = "notícia informativa e relevante" if eh_noticia else "vaga de emprego de motorista"
    
    prompt = f"""
    Você é o editor do 'Portal Emprego para Motorista'. 
    Transforme os dados coletados em uma {tipo_contexto} extremamente profissional e organizada em HTML para leitura em celular.

    Dados Coletados:
    - Título original: {titulo}
    - Conteúdo: {conteudo}
    
    REGRAS OBRIGATÓRIAS:
    1. O retorno deve seguir rigidamente a estrutura:
       [TITULO_DO_POST]
       Escreva o título final limpo em português (Sem aspas e sem markdown).
       
       [CORPO_DO_POST]
       Inicie o texto EXATAMENTE com esta linha de data formatada em HTML:
       <p style="color: #666; font-size: 13px; font-style: italic; margin-bottom: 15px;">📅 Publicado em: {data_postagem}</p>
       
       Escreva o restante do artigo usando HTML limpo (<h2>, <p>, <strong>, <ul>, <li>).
    """
    
    if not eh_noticia:
        prompt += f"""
       Organize em tópicos: <h2>📋 Detalhes da Oportunidade</h2>, <h2>🛠️ Requisitos</h2>.
       No final, adicione este botão de candidatura:
       <br><br>
       <div style="text-align: center;">
           <a href="{link_original}" target="_blank" rel="noopener" style="background-color: #e63946; color: white; padding: 14px 28px; text-decoration: none; font-weight: bold; border-radius: 6px; display: inline-block;">👉 CLIQUE AQUI PARA SE CANDIDATAR</a>
       </div>
        """
    else:
        prompt += f"""
       Organize a notícia de forma fluida. No final, coloque:
       <br><br>
       <p><i>Fonte da notícia completa: <a href="{link_original}" target="_blank" rel="noopener">Acesse o portal oficial</a></i></p>
        """

    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        texto = response.text
        if imagem_url and "[CORPO_DO_POST]" in texto:
            tag_img = f'<div style="text-align:center;"><img src="{imagem_url}" style="max-width:100%; height:auto; margin-bottom:20px; border-radius:6px;"></div><br>\n'
            texto = texto.replace("[CORPO_DO_POST]", f"[CORPO_DO_POST]\n{tag_img}")
        return texto
    except Exception as e:
        print(f"❌ Erro na API do Gemini: {e}")
        return f"[TITULO_DO_POST]\nAtualização do Setor de Transportes\n\n[CORPO_DO_POST]\n<p>📅 Publicado em: {data_postagem}</p><br>Confira a matéria completa direto na fonte: <a href='{link_original}'>Clique aqui</a>."

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
        print(f"🎉 Publicado com sucesso: {titulo}")
    except Exception as e:
        print(f"❌ Falha no envio do e-mail: {e}")

if __name__ == "__main__":
    print("🤖 Iniciando varredura inteligente do portal...")
    publicados = listar_titulos_publicados_recentes()
    
    # Executa a busca implacável por vagas
    t, d, l, i = minerar_feed_implacavel(FONTES_VAGAS, publicados)
    eh_noticia = False
    
    # Se falhar em todas as vagas, executa a busca implacável por notícias
    if not t:
        print("⚠️ Nenhuma vaga nova encontrada nos sites parceiros. Ativando Plano B (Notícias)...")
        t, d, l, i = minerar_feed_implacavel(FONTES_NOTICIAS, publicados)
        eh_noticia = True
        
    if t:
        resultado_ia = gerar_conteudo_ia(t, d, l, i, eh_noticia)
        try:
            t_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
            c_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
            enviar_email_blogger(t_final, c_final)
        except Exception as e:
            print(f"⚠️ Erro ao fatiar resposta da IA, enviando padrão: {e}")
            enviar_email_blogger("Informativo Diário - Motorista", resultado_ia)
    else:
        print("🛑 Sistema encerrado: Nenhuma novidade absoluta encontrada em nenhuma das 6 fontes.")
