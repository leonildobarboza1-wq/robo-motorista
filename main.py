import os
import time
import random
import smtplib
import urllib.request
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai

# ==========================================
# CONFIGURAÇÕES DO PORTAL DE VAGAS
# ==========================================
URL_MEU_BLOG = "https://empregomotoristas.blogspot.com"
EMAIL_SECRETO_BLOGGER = os.environ.get("EMAIL_SECRETO_BLOGGER") # Seu e-mail @blogger.com salvo no GitHub

# Configurações do seu Gmail que envia os dados
GMAIL_REMETENTE = os.environ.get("GMAIL_REMETENTE")
GMAIL_SENHA_APP = os.environ.get("GMAIL_SENHA_APP")

# Fontes de vagas e notícias do setor no Brasil
FONTES_VAGAS = [
    {"nome": "Blog do Caminhoneiro - Vagas", "url": "https://blogdocaminhoneiro.com/category/vagas-de-emprego/feed/"},
    {"nome": "Estradão - Estadão", "url": "https://estradao.estadao.com.br/feed/"},
    {"nome": "Mundo do Caminhão", "url": "https://blog.mundodocaminhao.com.br/feed/"},
    {"nome": "Frota Cia", "url": "https://www.frotacia.com.br/feed/"}
]

def listar_titulos_publicados_recentes():
    """Lê o feed do seu próprio blog para saber o que já foi publicado e evitar duplicidade"""
    titulos_recentes = set()
    url_feed = f"{URL_MEU_BLOG.rstrip('/')}/feeds/posts/default"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        req = urllib.request.Request(url_feed, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            
            # O Blogger usa o padrão Atom XML, as tags usam namespaces
            namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
            for entry in root.findall('atom:entry', namespaces):
                title_element = entry.find('atom:title', namespaces)
                if title_element is not None and title_element.text:
                    titulos_recentes.add(title_element.text.strip().lower())
        print(f"📚 Histórico do seu blog lido com sucesso. {len(titulos_recentes)} títulos monitorados.")
    except Exception as e:
        print(f"⚠️ Não foi possível ler o histórico do seu blog (pode ser porque está sem posts ou instável): {e}")
    return titulos_recentes

def buscar_vaga_incondicional(titulos_bloqueados):
    """Varre as fontes de transporte atrás de uma vaga que ainda não foi postada no seu site"""
    print("🎲 Iniciando mineração de vagas anti-duplicação...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml;q=0.9, */*;q=0.8'
    }
    
    fontes_aleatorias = list(FONTES_VAGAS)
    random.shuffle(fontes_aleatorias)
    
    for fonte in fontes_aleatorias:
        try:
            req = urllib.request.Request(fonte['url'], headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                root = ET.fromstring(response.read())
            
            items = root.findall('.//item')
            if not items:
                continue
                
            random.shuffle(items)
            for item in items:
                title = item.find('title').text
                desc = item.find('description').text if item.find('description') is not None else ""
                link = item.find('link').text
                
                if not title:
                    continue
                    
                # A mágica acontece aqui: se o título já existir no seu blog, ele ignora na hora!
                if title.strip().lower() in titulos_bloqueados:
                    print(f"Busca ⏭️ Pulando vaga já existente no seu blog: {title}")
                    continue
                
                # Coleta imagem caso exista no feed original
                img_url = ""
                media_content = item.find('{http://search.yahoo.com/mrss/}content')
                if media_content is not None and 'url' in media_content.attrib:
                    img_url = media_content.attrib['url']
                if not img_url:
                    enclosure = item.find('enclosure')
                    if enclosure is not None and 'url' in enclosure.attrib:
                        img_url = enclosure.attrib['url']
                
                print(f"🎯 Vaga Nova Encontrada: {title}")
                return title, desc, link, img_url
        except Exception as e:
            print(f"❌ Erro na leitura da fonte '{fonte['nome']}': {e}")
            continue
            
    return None, None, None, None

def gerar_conteudo_ia(titulo, conteudo, link_original, imagem_url):
    """Usa o Gemini 2.5 Flash para formatar a vaga com o novo padrão profissional"""
    print("🧠 IA (Gemini 2.5 Flash) processando e estruturando o texto...")
    client = genai.Client()
    
    prompt = f"""
    Você é o recrutador-chefe do 'Portal Emprego para Motorista'. 
    Transforme os dados brutos abaixo em um anúncio de emprego limpo, profissional e muito fácil de ler no celular por motoristas de caminhão e carreta.

    Dados Coletados:
    - Título: {titulo}
    - Detalhes: {conteudo}
    
    REGRAS DE FORMATAÇÃO:
    1. O retorno deve ter EXATAMENTE esta estrutura de tags de marcação para o nosso sistema separar:
       [TITULO_DO_POST]
       Escreva um título claro e direto em português (Ex: Vaga para Motorista de Truck em Guarulhos - SP). Sem aspas e sem usar markdown.
       
       [CORPO_DO_POST]
       Organize as informações em HTML limpo. Use tags como <h2>, <p>, <strong>, <ul>, <li> para criar seções bem definidas:
       - <h2>📋 Detalhes da Oportunidade</h2>
       - <h2>🛠️ Requisitos para o Cargo</h2>
       - <h2>💰 Benefícios Oferecidos</h2> (se houver no texto)
       
    2. No final do [CORPO_DO_POST], coloque exatamente este botão vermelho elegante de candidatura:
       <br><br>
       <div style="text-align: center;">
           <a href="{link_original}" target="_blank" rel="noopener" style="background-color: #e63946; color: white; padding: 14px 28px; text-decoration: none; font-weight: bold; border-radius: 6px; display: inline-block; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">👉 CLIQUE AQUI PARA SE CANDIDATAR A ESTA VAGA</a>
       </div>
       <br>
       <p style="text-align: center; color: #777; font-size: 11px;"><i>Informações extraídas diretamente da fonte oficial: {link_original}</i></p>
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        texto_gerado = response.text
        
        # Se houver imagem da empresa/vaga, insere centralizada no topo do post
        if imagem_url and "[CORPO_DO_POST]" in texto_gerado:
            tag_imagem = f'<div style="text-align:center;"><img src="{imagem_url}" style="max-width:100%; height:auto; margin-bottom:20px; border-radius:6px;"></div><br>\n'
            texto_gerado = texto_gerado.replace("[CORPO_DO_POST]", f"[CORPO_DO_POST]\n{tag_imagem}")
            
        return texto_gerado
    except Exception as e:
        print(f"❌ Erro na API do Gemini: {e}")
        return f"[TITULO_DO_POST]\nOportunidade de Emprego para Motorista\n\n[CORPO_DO_POST]\nConfira os detalhes da vaga diretamente na fonte oficial: <a href='{link_original}'>Clique aqui para acessar</a>."

def enviar_email_blogger(titulo, conteudo):
    """Envia o conteúdo formatado via e-mail silencioso para publicar no Blogger"""
    if not EMAIL_SECRETO_BLOGGER:
        print("❌ Erro: EMAIL_SECRETO_BLOGGER não configurado nas variáveis do GitHub.")
        return

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
        print(f"🎉 Sucesso! Vaga inédita enviada para o Blogger: {titulo}")
    except Exception as e:
        print(f"❌ Falha no envio do e-mail de postagem: {e}")

if __name__ == "__main__":
    # 1. Lê o que já está publicado no seu blog
    vagas_no_blog = listar_titulos_publicados_recentes()
    
    # 2. Busca uma vaga nova que não esteja na lista anterior
    orig_titulo, orig_desc, orig_link, orig_img = buscar_vaga_incondicional(vagas_no_blog)
    
    # 3. Processa e envia
    if orig_titulo:
        resultado_ia = gerar_conteudo_ia(orig_titulo, orig_desc, orig_link, orig_img)
        try:
            t_final = resultado_ia.split("[TITULO_DO_POST]")[1].split("[CORPO_DO_POST]")[0].strip()
            c_final = resultado_ia.split("[CORPO_DO_POST]")[1].strip()
            enviar_email_blogger(t_final, c_final)
        except Exception as e:
            print(f"⚠️ Erro ao separar título/corpo, enviando bruto: {e}")
            enviar_email_blogger("Oportunidade de Trabalho - Motorista", resultado_ia)
    else:
        print("🛑 Concluído. Nenhuma vaga nova ou diferente foi encontrada nas últimas horas.")
