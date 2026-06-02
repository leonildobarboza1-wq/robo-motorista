import os
import json
import datetime
from typing import Set, List, Dict, Optional
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

# Suas fontes reais e oficiais
FEEDS_VAGAS = [
    "https://estradao.estadao.com.br/feed/",
    "https://girodocaminhoneiro.com.br/feed/",
    "https://chapacomigo.com.br/feed/"
]

FEEDS_NOTICIAS = [
    "https://www.ntcelogistica.org.br/feed/",
    "https://fetrancesg.com.br/feed/",
    "https://estradas.com.br/feed/"
]

# ==========================================
# INICIALIZAÇÃO DOS SERVIÇOS
# ==========================================
def get_blogger_service():
    """Autentica na API do Blogger utilizando a Conta de Serviço."""
    if not SERVICE_ACCOUNT_JSON:
        raise ValueError("A chave GOOGLE_SERVICE_ACCOUNT_JSON não está configurada nos Secrets.")
    
    info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = service_account.Credentials.from_service_account_info(
        info, 
        scopes=['https://www.googleapis.com/auth/blogger']
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
                # Busca pela tag oculta de controle que injetamos no rodapé
                meta_tag = soup.find("meta", attrs={"name": "original_source"})
                if meta_tag and meta_tag.get("content"):
                    published_urls.add(meta_tag["content"].strip().lower())
                    
    except HttpError as e:
        print(f"⚠️ Aviso ao ler histórico do Blogger: {e}")
    return published_urls

# ==========================================
# MINERAÇÃO COM PLANO B (PRIORIZAÇÃO)
# ==========================================
def parse_feed_list(urls: List[str], exclude_urls: Set[str], tipo: str) -> List[Dict]:
    """Varre uma lista de feeds extraindo dados brutos estruturados."""
    collected = []
    for url in urls:
        print(f"📡 Lendo feed ({tipo}): {url}")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                link = entry.get("link", "").strip()
                
                if not link or link.lower() in exclude_urls:
                    continue
                    
                # Coleta de imagem em destaque no feed de forma segura
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
                    "tipo": tipo  # 'Vaga' or 'Noticia'
                })
        except Exception as e:
            print(f"⚠️ Erro ao processar feed {url}: {e}")
            continue
    return collected

def mine_content(historical_urls: Set[str]) -> Optional[Dict]:
    """
    Varre vagas. Se achar algo inédito, retorna imediatamente.
    Se TODAS as vagas já existirem, ativa o Plano B (Notícias).
    """
    print("🔍 Fase 1: Buscando novas vagas de emprego...")
    vagas_encontradas = parse_feed_list(FEEDS_VAGAS, historical_urls, "Vaga")
    
    if vagas_encontradas:
        print(f"🎯 Nova vaga encontrada! Selecionando item inédito.")
        return vagas_encontradas[0]
        
    print("💤 Nenhuma vaga inédita encontrada. Ativando Plano B (Notícias)...")
    noticias_encontradas = parse_feed_list(FEEDS_NOTICIAS, historical_urls, "Noticia")
    
    if noticias_encontradas:
        print(f"📰 Nova notícia encontrada no Plano B!")
        return noticias_encontradas[0]
        
    print("📭 Nenhum conteúdo inédito em nenhuma das fontes.")
    return None

# ==========================================
# PROCESSAMENTO DE IA E DESIGN COMPONENTES
# ==========================================
def ask_gemini_to_rewrite(gemini_client, item: Dict) -> str:
    """Solicita ao gemini-2.5-flash a reescrita profissional estruturada em HTML básico."""
    prompt = f"""
    Você é o redator oficial do 'Portal Emprego para Motorista'.
    Reescreva o conteúdo abaixo no formato de um artigo de blog atraente, fluido, claro e muito informativo.
    
    Regras de Formatação Obrigatórias:
    1. Retorne APENAS o texto do artigo estruturado com tags HTML básicas e limpas (como <p>, <b>, <ul>, <li>, <h2>).
    2. NÃO inclua tags estruturais globais como <html>, <head> ou <body>.
    3. NÃO retorne blocos de código markdown (proibido usar ```html ou fechar com ```). Comece diretamente no texto estruturado.
    4. Garanta espaçamento agradável entre parágrafos para leitura excelente em telas de smartphones.

    Dados para Base:
    Título: {item['title']}
    Conteúdo Bruto: {item['description']}
    """
    
    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text.replace("```html", "").replace("```", "").strip()

def build_final_html(ai_body: str, item: Dict) -> str:
    """Injeta os elementos visuais de topo, imagem e rodapé exigidos."""
    # Tratamento de fuso horário travado no Horário de Brasília (UTC-3)
    fuso_sp = datetime.timezone(datetime.timedelta(hours=-3))
    data_atual = datetime.datetime.now(fuso_sp)
    
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    data_formatada = f"{data_atual.day} de {meses_pt[data_atual.month]} de {data_atual.year}"
    
    # 1. Componente de Topo: Data com design elegante e leve (Estilo inline seguro)
    html_topo = f"""
    <div style="background-color: #f7f9fa; border-left: 4px solid #d90429; padding: 12px 15px; margin-bottom: 22px; font-family: sans-serif; border-radius: 0 4px 4px 0;">
        <span style="color: #2b2d42; font-weight: bold; font-size: 15px;">📅 Publicado em: {data_formatada}</span>
    </div>
    """
    
    # 2. Imagem Destacada (Caso o feed forneça)
    html_imagem = ""
    if item.get("image"):
        html_imagem = f"""
        <div style="text-align: center; margin-bottom: 22px;">
            <img src="{item['image']}" alt="Imagem em destaque" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 3px 10px rgba(0,0,0,0.15);" />
        </div>
        """
        
    # 3. Componente de Rodapé: Botão de ação robusto e responsivo + Meta tag oculta de controle de duplicados
    texto_botao = "🚀 CLIQUE AQUI PARA SE CANDIDATAR A ESTA VAGA" if item["tipo"] == "Vaga" else "🔗 LER NOTÍCIA COMPLETA NA FONTE"
    cor_botao = "#e63946" if item["tipo"] == "Vaga" else "#1d3557"
    
    html_rodape = f"""
    <hr style="border: 0; border-top: 1px solid #eee; margin: 35px 0;" />
    <div style="text-align: center; margin: 25px 0; font-family: sans-serif;">
        <a href="{item['link']}" target="_blank" rel="noopener noreferrer" 
           style="background-color: {cor_botao}; color: #ffffff; padding: 14px 28px; text-decoration: none; font-weight: bold; border-radius: 6px; display: inline-block; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
            {texto_botao}
        </a>
    </div>
    <meta name="original_source" content="{item['link']}" />
    """
    
    return f"{html_topo}\n{html_imagem}\n{ai_body}\n{html_rodape}"

# ==========================================
# PUBLICADOR OFICIAL VIA API
# ==========================================
def send_to_blogger(blogger_service, title: str, html_content: str, label: str):
    """Realiza a postagem direta no painel do Blogger via requisição JSON estruturada."""
    body = {
        "kind": "blogger#post",
        "title": title,
        "content": html_content,
        "labels": [label]  # Alimenta dinamicamente o marcador 'Vaga' ou 'Noticia'
    }
    
    try:
        request = blogger_service.posts().insert(blogId=BLOG_ID, body=body)
        response = request.execute()
        print(f"🎉 SUCESSO TOTAL! Post publicado via API oficial. URL: {response.get('url')}")
    except HttpError as e:
        print(f"❌ Erro crítico ao publicar na API do Blogger: {e}")

# ==========================================
# EXECUÇÃO DA ROTINA (MAIN)
# ==========================================
def main():
    print("⚡ Iniciando execução do robô profissional via API Google Blogger...")
    
    if not BLOG_ID:
        print("❌ Erro fatal: A variável BLOG_ID não foi encontrada.")
        return

    # Instancia clientes oficiais
    blogger = get_blogger_service()
    gemini = get_gemini_client()
    
    # 1. Carrega histórico de rastreio (Filtro inteligente inteligente)
    history = fetch_published_urls(blogger)
    print(f"💾 Histórico carregado com sucesso: {len(history)} links rastreados eletronicamente.")
    
    # 2. Executa mineração lógica (Vagas primeiro, Notícias se faltar vaga)
    target_item = mine_content(history)
    
    if not target_item:
        print("🏁 Ciclo finalizado: Sem novos conteúdos para postar nesta rodada.")
        return
        
    print(f"📖 Processando artigo selecionado: {target_item['title']}")
    
    try:
        # 3. Transforma o conteúdo usando IA
        ai_text = ask_gemini_to_rewrite(gemini, target_item)
        
        # 4. Envelopa com o novo layout estruturado
        final_post_html = build_final_html(ai_text, target_item)
        
        # 5. Publica nativamente com a etiqueta correta (Alimenta as abas automaticamente)
        send_to_blogger(
            blogger_service=blogger,
            title=target_item['title'],
            html_content=final_post_html,
            label=target_item['tipo']
        )
        
    except Exception as err:
        print(f"💥 Falha no processamento deste item: {err}")

if __name__ == "__main__":
    main()
