import os
import json
import datetime
import urllib.parse
from typing import Set, List, Dict, Optional
import requests
import feedparser
from bs4 import BeautifulSoup
from google import genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ========================================== 
# CONFIGURAÇÕES E AMBIENTE
# ==========================================
BLOG_ID = os.environ.get("BLOG_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

# Fontes Tradicionais (Fase 1)
FEEDS_VAGAS = [
    "https://estradao.estadao.com.br/feed/",
    "https://girodocaminhoneiro.com.br/feed/",
    "https://chapacomigo.com.br/feed/"
]

# Fontes de Notícias Gerais (Fase 3 - Plano B)
FEEDS_NOTICIAS = [
    "https://www.ntcelogistica.org.br/feed/",
    "https://fetrancesg.com.br/feed/",
    "https://estradas.com.br/feed/"
]

# ==========================================
# INICIALIZAÇÃO DOS SERVIÇOS
# ==========================================
def get_blogger_service():
    """Autentica na API do Blogger utilizando a Conta de Serviço com autoridade direta."""
    if not SERVICE_ACCOUNT_JSON:
        raise ValueError("A chave GOOGLE_SERVICE_ACCOUNT_JSON não está configurada nos Secrets.")
    
    info = json.loads(SERVICE_ACCOUNT_JSON)
    
    # Escopo oficial exigido para gerenciamento completo do blog
    scopes = ['https://www.googleapis.com/auth/blogger']
    
    credentials = service_account.Credentials.from_service_account_info(
        info, 
        scopes=scopes
    )
    
    # Constrói o serviço da API ignorando travas de convites pendentes de interface
    return build('blogger', 'v3', credentials=credentials)

# ==========================================
# RASTREIO DE HISTÓRICO E DUPLICIDADE
# ==========================================
def fetch_published_urls(blogger_service) -> Set[str]:
    """
    Consome o histórico do blog através da API oficial e extrai com precisão 
    as URLs originais mapeadas na tag oculta para evitar republicação.
    """
    published_urls = set()
    try:
        request = blogger_service.posts().list(
            blogId=BLOG_ID, 
            maxResults=30, 
            fields="items(content)"
        )
        response = request.execute()
        
        if "items" in response:
            for item in response["items"]:
                content = item.get("content", "")
                soup = BeautifulSoup(content, "html.parser")
                meta_tag = soup.find("meta", attrs={"name": "original_source"})
                if meta_tag and meta_tag.get("content"):
                    published_urls.add(meta_tag["content"].strip().lower())
                    
    except HttpError as e:
        print(f"⚠️ Aviso ao ler histórico do Blogger: {e}")
    return published_urls

# ==========================================
# MINERAÇÃO MULTI-FASE (VAGAS -> GOOGLE NEWS -> NOTÍCIAS)
# ==========================================
def parse_feed_list(urls: List[str], exclude_urls: Set[str], tipo: str) -> List[Dict]:
    """Varre uma lista de feeds tradicionais extraindo dados brutos estruturados."""
    collected = []
    for url in urls:
        print(f"📡 Lendo feed tradicional ({tipo}): {url}")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                link = entry.get("link", "").strip()
                
                if not link or link.lower() in exclude_urls:
                    continue
                    
                image_url = None
                if "media_content" in entry and entry.media_content:
                    image_url = entry.media_content[0].get("url")
                elif "enclosure" in entry:
                    image_url = entry.enclosure.get("url")
                    
                collected.append({
                    "title": entry.get("title", "Sem título"),
                    "description": entry.get("summary", entry.get("description", "")),
                    "link": link,
                    "image": image_url,
                    "tipo": tipo
                })
        except Exception as e:
            print(f"⚠️ Erro ao processar feed {url}: {e}")
            continue
    return collected

def buscar_vagas_google_news(exclude_urls: Set[str]) -> List[Dict]:
    """
    Fase 2: Varre o Google News RSS em busca de vagas de motorista no Brasil inteiro
    e retorna os dados formatados para o padrão do robô.
    """
    print(f"📡 Lendo super-feed (Google News Vagas)...")
    termo = '"vaga de motorista"'
    termo_encodado = urllib.parse.quote(termo)
    
    # URL dividida de forma segura para evitar quebras de linha no GitHub
    url = (
        f"https://news.google.com/rss/search?"
        f"q={termo_encodado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    )
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    try:
        resposta = requests.get(url, headers=headers, timeout=15)
        if resposta.status_code != 200:
            print(f"⚠️ Erro ao acessar o Google News. Status: {resposta.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ Erro de conexão com o Google News: {e}")
        return []
        
    soup = BeautifulSoup(resposta.text, 'xml')
    itens = soup.find_all('item')
    collected = []
    
    for item in itens:
        try:
            link = item.find('link').text.strip() if item.find('link') else ""
            if not link or link.lower() in exclude_urls:
                continue
                
            titulo_completo = item.find('title').text.strip() if item.find('title') else "Vaga de Motorista"
            titulo = titulo_completo.rsplit(" - ", 1)[0] if " - " in titulo_completo else titulo_completo
            
            descricao = item.find('description').text.strip() if item.find('description') else ""
            descricao_limpa = BeautifulSoup(descricao, "html.parser").get_text()
            
            collected.append({
                "title": titulo,
                "description": descricao_limpa,
                "link": link,
                "image": None,
                "tipo": "Vaga"
            })
        except Exception:
            continue
            
    return collected
