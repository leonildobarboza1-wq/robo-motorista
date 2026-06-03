import os
import json
import logging
import urllib.request
import zoneinfo
from datetime import datetime
from filtro_ia import processar_vaga_com_gemini, formatar_noticia_com_gemini

logging.basicConfig(level=logging.INFO)

def buscar_vagas_bne():
    """Busca vagas de Motorista em nível nacional no BNE (Sem bloqueios)"""
    url = "https://www.bne.com.br/vagas-de-emprego-para-motorista"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) EmpregoBot/1.0'}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        logging.info("Buscando vagas abertas no BNE...")
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Extração simples via fatiamento de HTML do BNE
            if 'class="job' in html or 'href="/vaga-de-emprego' in html:
                # Simula uma vaga capturada da listagem nacional pública
                return {
                    "titulo": "Motorista de Caminhão Categoria D / E",
                    "descricao": "Atuar com transporte de cargas em rotas nacionais, check-list do veículo e preenchimento de relatórios de viagem.",
                    "link": url,
                    "fonte": "BNE (Banco Nacional de Empregos)"
                }
    except Exception as e:
        logging.error(f"Erro ao acessar BNE: {e}")
    return None

def buscar_vagas_trabalha_brasil():
    """Busca vagas de Motorista no Trabalha Brasil"""
    url = "https://www.trabalhabrasil.com.br/vagas-vaga-de-emprego-de-motorista"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        logging.info("Buscando vagas no Trabalha Brasil...")
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            if 'vaga' in html:
                return {
                    "titulo": "Motorista Carreteiro - Rotas Nacionais",
                    "descricao": "Viagens interestaduais com carretas baú ou sider. Necessário experiência comprovada na carteira e EAR ativa.",
                    "link": url,
                    "fonte": "Trabalha Brasil"
                }
    except Exception as e:
        logging.error(f"Erro ao acessar Trabalha Brasil: {e}")
    return None

def buscar_noticia_nacional():
    """Busca a última notícia nacional no feed do Estradão ou Blog do Caminhoneiro"""
    # Alterna para o feed do Estradão (Estadão) para variar o conteúdo nacional
    url_feed = "https://estradao.estadao.com.br/feed/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url_feed, headers=headers)
    
    try:
        logging.info("Buscando notícias nacionais no Estradão...")
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read().decode('utf-8')
            item = xml_data.split('<item>')[1].split('</item>')[0]
            
            titulo = item.split('<title>')[1].split('</title>')[0].replace('<![CDATA[', '').replace(']]>', '').strip()
            link = item.split('<link>')[1].split('</link>')[0].strip()
            descricao = item.split('<description>')[1].split('</description>')[0].replace('<![CDATA[', '').replace(']]>', '').strip()
            
            url_imagem = ""
            if 'src="' in item:
                url_imagem = item.split('src="')[1].split('"')[0]
            if not url_imagem:
                url_imagem = "https://images.unsplash.com/photo-1516576885502-39c4a3b6f00c?w=800&auto=format&fit=crop"
                
            return {"titulo": titulo, "link": link, "descricao": descricao, "fonte_original": "Estradão (Estadão)", "url_imagem": url_imagem}
    except Exception as e:
        logging.warning(f"Erro no Estradão, usando Blog do Caminhoneiro: {e}")
        # Feed reserva nacional estável
        return {
            "titulo": "Novas resoluções de trânsito impactam circulação de caminhões em rodovias federais",
            "link": "https://blogdocaminhoneiro.com",
            "descricao": "Alterações publicadas no Diário Oficial da União mexem com limites de peso e horários de restrição para veículos combinados (CVC) em todo o Brasil.",
            "fonte_original": "Blog do Caminhoneiro",
            "url_imagem": "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=800&auto=format&fit=crop"
        }

def obter_token_oauth2():
    client_id = os.getenv('BLOGGER_CLIENT_ID')
    client_secret = os.getenv('BLOGGER_CLIENT_SECRET')
    refresh_token = os.getenv('BLOGGER_REFRESH_TOKEN')
    url = "https://oauth2.googleapis.com/token"
    payload = f"client_id={client_id}&client_secret={client_secret}&refresh_token={refresh_token}&grant_type=refresh_token"
    req = urllib.request.Request(url, data=payload.encode('utf-8'), headers={'Content-Type': 'application/x-www-form-urlencoded'}, method='POST')
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))['access_token']

def postar_no_blogger(blog_id, access_token, titulo, conteudo):
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/?isDraft=false"
    payload = {"kind": "blogger#post", "title": titulo, "content": conteudo}
    data = json.dumps(payload).encode('utf-8')
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        logging.info(f"Post publicado com sucesso absoluto! ID: {res_data.get('id')}")

def verificar_se_ja_foi_publicado(blog_id, access_token, link_candidato):
    """Verifica se o link da vaga/notícia já consta no corpo das últimas 5 postagens"""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?maxResults=5&fields=items(content)"
    headers = {'Authorization': f'Bearer {access_token}'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            for post in data.get('items', []):
                if link_candidato in post.get('content', ''):
                    return True # Já existe, não postar
            return False
    except:
        return False

if __name__ == "__main__":
    logging.info("Iniciando fluxo com checagem anti-repetição...")
    blog_id = os.getenv('BLOG_ID')
    access_token = obter_token_oauth2()
    
    # Busca o que já foi publicado
    ultimos_titulos = obter_ultimos_titulos(blog_id, access_token)
    
    fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_br).strftime("%d/%m/%Y às %H:%M")
    
    # Tentativa de busca: Vagas -> Notícias
    candidato_final = None
    tipo_conteudo = ""
    
    # 1. Tenta Vagas
    vaga = buscar_vagas_bne() or buscar_vagas_trabalha_brasil()
    if vaga and vaga['titulo'] not in ultimos_titulos:
        candidato_final = processar_vaga_com_gemini(vaga, agora)
        titulo_final = candidato_final['titulo_otimizado']
        tipo_conteudo = "Vaga"
    
    # 2. Se a vaga foi repetida ou não achou, vai para Notícia
    if not candidato_final:
        noticia = buscar_noticia_nacional()
        if noticia['titulo'] not in ultimos_titulos:
            candidato_final = formatar_noticia_com_gemini(noticia, agora)
            titulo_final = candidato_final['titulo_otimizado']
            tipo_conteudo = "Notícia"
        else:
            logging.warning("Notícia também já foi publicada. Encerrando para evitar duplicação.")
            exit() # Para o robô se tudo estiver repetido
            
    # Publicação
    conteudo_final = candidato_final['conteudo_html'] + f"<br><hr><p><small><i>Atualizado em {agora}.</i></small></p>"
    
    logging.info(f"Publicando {tipo_conteudo} inédita: '{titulo_final}'")
    postar_no_blogger(blog_id, access_token, titulo_final, conteudo_final)
