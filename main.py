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

# Fontes Tradicionais Focadas em Oportunidades Reais (Fase 1)
FEEDS_VAGAS = [
    "https://www.bne.com.br/rss/vagas-de-emprego-para-motorista",
    "https://www.vagas.com.br/vagas-de-motorista.rss",
    "https://TrabalhaBrasil.com.br/rss/vagas-de-emprego-para-motorista"
]

# ==========================================
# INICIALIZAÇÃO DOS SERVIÇOS
# ==========================================
def get_blogger_service():
    """Autentica na API do Blogger utilizando a Conta de Serviço com autoridade direta."""
    if not SERVICE_ACCOUNT_JSON:
        raise ValueError("A chave GOOGLE_SERVICE_ACCOUNT_JSON não está configurada nos Secrets.")
    
    info = json.loads(SERVICE_ACCOUNT_JSON)
    scopes = ['https://www.googleapis.com/auth/blogger']
    
    credentials = service_account.Credentials.from_service_account_info(
        info, 
        scopes=scopes
    )
    return build('blogger', 'v3', credentials=credentials)

def get_gemini_client():
    """Inicializa o SDK oficial google-genai."""
    if not GEMINI_API_KEY:
        raise ValueError("A chave GEMINI_API_KEY não está configurada nos Secrets.")
    return genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# RASTREIO DE HISTÓRICO E DUPLICIDADE
# ==========================================
def fetch_published_urls(blogger_service) -> Set[str]:
    """
    Consome o histórico do blog. Se não encontrar a tag oculta original_source,
    mapeia variações do título para evitar duplicidade de vagas conhecidas.
    """
    published_urls = set()
    try:
        request = blogger_service.posts().list(
            blogId=BLOG_ID, 
            maxResults=30, 
            fields="items(title,content)"
        )
        response = request.execute()
        
        if "items" in response:
            for item in response["items"]:
                content = item.get("content", "")
                soup = BeautifulSoup(content, "html.parser")
                meta_tag = soup.find("meta", attrs={"name": "original_source"})
                
                if meta_tag and meta_tag.get("content"):
                    published_urls.add(meta_tag["content"].strip().lower())
                else:
                    title = item.get("title", "").lower().strip()
                    published_urls.add(title)
                    
    except HttpError as e:
        print(f"⚠️ Aviso ao ler histórico do Blogger: {e}")
    return published_urls

# ==========================================
# MINERAÇÃO MULTI-FASE (VAGAS TRADICIONAIS -> GOOGLE NEWS)
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
                title = entry.get("title", "").strip().lower()
                
                if not link or link.lower() in exclude_urls or title in exclude_urls:
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
    """Varre o Google News RSS em busca de vagas de motorista no Brasil."""
    print(f"📡 Lendo super-feed (Google News Vagas)...")
    termo = '"vaga de motorista"'
    termo_encodado = urllib.parse.quote(termo)
    
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
        
    # LINHA CORRIGIDA AQUI: Mudamos de 'xml' para 'html.parser'
    soup = BeautifulSoup(resposta.text, 'html.parser')
    itens = soup.find_all('item')
    collected = []
    
    for item in itens:
        try:
            link = item.find('link').text.strip() if item.find('link') else ""
            titulo_completo = item.find('title').text.strip() if item.find('title') else "Vaga de Motorista"
            titulo_limpo = titulo_completo.rsplit(" - ", 1)[0] if " - " in titulo_completo else titulo_completo
            
            if not link or link.lower() in exclude_urls or titulo_limpo.lower().strip() in exclude_urls:
                continue
                
            descricao = item.find('description').text.strip() if item.find('description') else ""
            descricao_limpa = BeautifulSoup(descricao, "html.parser").get_text()
            
            collected.append({
                "title": titulo_limpo,
                "description": descricao_limpa,
                "link": link,
                "image": None,
                "tipo": "Vaga"
            })
        except Exception:
            continue
            
    return collected

def mine_content(historical_urls: Set[str]) -> Optional[Dict]:
    """Aplica a lógica de busca focada estritamente em vagas."""
    print("🔍 [Fase 1]: Buscando vagas nos parceiros profissionais...")
    vagas_tradicionais = parse_feed_list(FEEDS_VAGAS, historical_urls, "Vagas")
    if vagas_tradicionais:
        print(f"🎯 Vaga encontrada nos parceiros profissionais!")
        return vagas_tradicionais[0]
        
    print("🔍 [Fase 2]: Parceiros sem novidades. Ativando Varredura Google News...")
    vagas_google = buscar_vagas_google_news(historical_urls)
    if vagas_google:
        print(f"🎯 Nova vaga pescada direto do Google News!")
        return vagas_google[0]
        
    print("📭 Nenhuma vaga inédita encontrada nesta rodada.")
    return None

# ==========================================
# PROCESSAMENTO DE IA E DESIGN COMPONENTES
# ==========================================
def ask_gemini_to_rewrite(gemini_client, item: Dict) -> str:
    """Solicita ao Gemini a reescrita profissional estruturada em HTML."""
    prompt = f"""
    Você é o redator oficial do 'Portal Emprego para Motorista'.
    Reescreva o conteúdo abaixo no formato de um anúncio de vaga de emprego muito atraente, claro e bem organizado.
    Destaque os requisitos da vaga se eles estiverem disponíveis no texto.
    
    Regras de Formatação Obrigatórias:
    1. Retorne APENAS o texto estruturado com tags HTML básicas e limpas (como <p>, <b>, <ul>, <li>, <h2>).
    2. NÃO inclua tags estruturais globais como <html>, <head> ou <body>.
    3. NÃO retorne blocos de código markdown (proibido usar ```html ou fechar com ```). Comece diretamente no texto.
    """
    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text.replace("```html", "").replace("```", "").strip()

def build_final_html(ai_body: str, item: Dict) -> str:
    """Injeta os elementos visuais de topo, imagem e botão de candidatura."""
    fuso_sp = datetime.timezone(datetime.timedelta(hours=-3))
    data_atual = datetime.datetime.now(fuso_sp)
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    data_formatada = f"{data_atual.day} de {meses_pt[data_atual.month]} de {data_atual.year}"
    
    html_topo = f"""
    <div style="background-color: #f7f9fa; border-left: 4px solid #d90429; padding: 12px 15px; margin-bottom: 22px; font-family: sans-serif; border-radius: 0 4px 4px 0;">
        <span style="color: #2b2d42; font-weight: bold; font-size: 15px;">📅 Publicado em: {data_formatada}</span>
    </div>
    """
    
    html_imagem = ""
    if item.get("image"):
        html_imagem = f"""
        <div style="text-align: center; margin-bottom: 22px;">
            <img src="{item['image']}" alt="Imagem da Vaga" style="max-width: 100%; height: auto; border-radius: 8px;" />
        </div>
        """
        
    html_rodape = f"""
    <hr style="border: 0; border-top: 1px solid #eee; margin: 35px 0;" />
    <div style="text-align: center; margin: 25px 0; font-family: sans-serif;">
        <a href="{item['link']}" target="_blank" rel="noopener noreferrer" 
           style="background-color: #e63946; color: #ffffff; padding: 14px 28px; text-decoration: none; font-weight: bold; border-radius: 6px; display: inline-block; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
            🚀 CLIQUE AQUI PARA SE CANDIDATAR A ESTA VAGA
        </a>
    </div>
    <meta name="original_source" content="{item['link']}" />
    """
    return f"{html_topo}\n{html_imagem}\n{ai_body}\n{html_rodape}"

def send_to_blogger(blogger_service, title: str, html_content: str, label: str):
    """Realiza a postagem direta no painel do Blogger."""
    body = {
        "kind": "blogger#post",
        "title": title,
        "content": html_content,
        "labels": [label]
    }
    try:
        request = blogger_service.posts().insert(blogId=BLOG_ID, body=body)
        response = request.execute()
        print(f"🎉 SUCESSO! Post publicado. URL: {response.get('url')}")
    except HttpError as e:
        print(f"❌ Erro crítico ao publicar no Blogger: {e}")

# ==========================================
# EXECUÇÃO PRINCIPAL
# ==========================================
def main():
    print("⚡ Iniciando execução do robô focado estritamente em vagas...")
    if not BLOG_ID:
        print("❌ Erro fatal: A variável BLOG_ID não foi configurada.")
        return

    blogger = get_blogger_service()
    gemini = get_gemini_client()
    
    history = fetch_published_urls(blogger)
    print(f"💾 Histórico recente: {len(history)} títulos/links mapeados.")
    
    target_item = mine_content(history)
    if not target_item:
        print("🏁 Ciclo finalizado: Nenhuma vaga inédita no mercado no momento.")
        return
        
    print(f"📖 Processando artigo selecionado: {target_item['title']}")
    try:
        ai_text = ask_gemini_to_rewrite(gemini, target_item)
        final_post_html = build_final_html(ai_text, target_item)
        send_to_blogger(blogger, target_item['title'], final_post_html, "Vagas")
    except Exception as err:
        print(f"💥 Falha no processamento: {err}")

if __name__ == "__main__":
    main()
