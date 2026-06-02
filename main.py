import os
import json
import datetime
import urllib.parse
import difflib
from typing import Set, List, Dict, Optional, Tuple
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

# Canais de Feeds Profissionais Reais (Fase 1)
FEEDS_PROFISSIONAIS = [
    "https://www.bne.com.br/rss/vagas-de-emprego-para-motorista",
    "https://www.vagas.com.br/vagas-de-motorista.rss",
    "https://TrabalhaBrasil.com.br/rss/vagas-de-emprego-para-motorista"
]

# ==========================================
# INICIALIZAÇÃO DOS SERVIÇOS
# ==========================================
def get_blogger_service():
    if not SERVICE_ACCOUNT_JSON:
        raise ValueError("A chave GOOGLE_SERVICE_ACCOUNT_JSON não está configurada nos Secrets.")
    info = json.loads(SERVICE_ACCOUNT_JSON)
    credentials = service_account.Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/blogger']
    )
    return build('blogger', 'v3', credentials=credentials)

def get_gemini_client():
    if not GEMINI_API_KEY:
        raise ValueError("A chave GEMINI_API_KEY não está configurada nos Secrets.")
    return genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# RASTREIO DE HISTÓRICO AVANÇADO
# ==========================================
def fetch_published_urls(blogger_service) -> Tuple[Set[str], List[str]]:
    """
    Coleta o histórico duplo do blog: URLs originais (da meta tag) 
    e títulos limpos dos últimos 30 posts para análise de similaridade.
    """
    published_urls = set()
    published_titles = []
    try:
        request = blogger_service.posts().list(
            blogId=BLOG_ID, 
            maxResults=30, 
            fields="items(title,content)"
        )
        response = request.execute()
        
        if "items" in response:
            for item in response["items"]:
                title = item.get("title", "").strip().lower()
                if title:
                    published_titles.append(title)
                
                content = item.get("content", "")
                soup = BeautifulSoup(content, "html.parser")
                meta_tag = soup.find("meta", attrs={"name": "original_source"})
                if meta_tag and meta_tag.get("content"):
                    published_urls.add(meta_tag["content"].strip().lower())
                    
    except HttpError as e:
        print(f"⚠️ [HISTÓRICO] Aviso ao ler banco de dados do Blogger: {e}")
        
    return published_urls, published_titles

# ==========================================
# REGRAS DE FILTRAGEM E INTELIGÊNCIA DE TÍTULO
# ==========================================
def is_duplicate_title(new_title: str, historical_titles: List[str], threshold: float = 0.85) -> bool:
    """
    Utiliza a biblioteca nativa difflib para checar se o título da vaga 
    é 85% ou mais idêntico a algum título que já foi publicado no blog.
    """
    new_title_clean = new_title.strip().lower()
    for hist_title in historical_titles:
        similarity = difflib.SequenceMatcher(None, new_title_clean, hist_title).ratio()
        if similarity >= threshold:
            print(f"   [BLOQUEADO] Título muito similar ({similarity*100:.1f}%): '{new_title}' com '{hist_title}'")
            return True
    return False

# ==========================================
# MINERAÇÃO MULTI-FASE E MINERAÇÃO DE GOOGLE NEWS
# ==========================================
def parse_feed_list(urls: List[str], historical_urls: Set[str], historical_titles: List[str]) -> List[Dict]:
    """Varre feeds RSS aplicando o filtro inteligente de duplicidade por URL e similaridade de Título."""
    collected = []
    for url in urls:
        print(f"📡 [FASE 1] Minerando feed profissional: {url}")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                link = entry.get("link", "").strip()
                title = entry.get("title", "Sem título")
                
                if not link:
                    continue
                    
                if link.lower() in historical_urls:
                    print(f"   [BLOQUEADO] URL idêntica já publicada: {link}")
                    continue
                    
                if is_duplicate_title(title, historical_titles):
                    continue
                    
                collected.append({
                    "title": title,
                    "description": entry.get("summary", entry.get("description", "")),
                    "link": link,
                    "origem": "Feed Profissional"
                })
        except Exception as e:
            print(f"⚠️ Erro ao processar o feed {url}: {e}")
            continue
    return collected

def buscar_vagas_google_news(termo_busca: str, historical_urls: Set[str], historical_titles: List[str], identificador_fase: str) -> List[Dict]:
    """Busca dinamicamente termos no Google News RSS transformando em dicionários de vagas estruturados."""
    termo_encodado = urllib.parse.quote(termo_busca)
    rss_url = f"https://news.google.com/rss/search?q={termo_encodado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    print(f"🔍 [{identificador_fase}] Buscando no Google News por: '{termo_busca}'")
    try:
        feed = feedparser.parse(rss_url)
        collected = []
        
        for entry in feed.entries:
            link = entry.get("link", "").strip()
            title = entry.get("title", "Sem título")
            
            if " - " in title:
                title = title.split(" - ")[0].strip()
                
            if not link:
                continue
                
            if link.lower() in historical_urls:
                print(f"   [BLOQUEADO] URL do Google News já publicada: {link}")
                continue
                
            if is_duplicate_title(title, historical_titles):
                continue
                
            collected.append({
                "title": title,
                "description": entry.get("summary", entry.get("description", "")),
                "link": link,
                "origem": f"Google News ({termo_busca})"
            })
        return collected
    except Exception as e:
        print(f"⚠️ Erro ao acessar o Google News na {identificador_fase}: {e}")
        return []

# ==========================================
# INTELIGÊNCIA ARTIFICIAL (GEMINI)
# ==========================================
def ask_gemini_to_rewrite(gemini_client, item: Dict) -> str:
    """Solicita ao gemini-2.5-flash o enriquecimento e reconstrução da vaga de motorista."""
    prompt = f"""
    Você é um assistente de RH especialista em recrutamento de motoristas profissionais. 
    Sua missão é transformar a oferta de emprego recebida em um artigo completo e altamente atrativo para trabalhadores do setor de transportes.

    ⚠️ DIRETRIZ CRÍTICA DE SOBREVIVÊNCIA DO ARTIGO:
    Se a descrição enviada abaixo for muito curta, vaga ou contiver apenas trechos de notícias fragmentadas, você NÃO DEVE falhar nem retornar vazio. 
    Use sua inteligência de mercado para deduzir o escopo padrão do cargo com base no título da vaga e preencha o artigo estruturando:
    1. Requisitos comuns esperados para esse tipo de motorista (Ex: CNH específica, MOPP se for carga perigosa, experiência em estradas, etc.).
    2. Adicione uma seção exclusiva chamada "💡 Dica de Ouro para se destacar na entrevista desta vaga", fornecendo conselhos práticos de comportamento, segurança defensiva ou pontualidade.

    Regras estritas de Formatação:
    - Retorne APENAS o corpo do texto formatado com tags HTML semânticas e limpas (<p>, <b>, <ul>, <li>, <h2>).
    - Não use tags estruturais como <html>, <head> ou <body>.
    - Proibido o uso de blocos de código ou markdown (nunca inclua ```html). Comece direto no texto.

    Dados Coletados da Vaga:
    Título: {item['title']}
    Descrição Bruta: {item['description']}
    """
    
    print(f"🤖 Acionando Gemini-2.5-Flash para enriquecer a vaga: '{item['title']}'")
    response = gemini_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    texto_gerado = response.text.strip()
    if not texto_gerado:
        raise ValueError("O Gemini retornou uma resposta vazia.")
        
    return texto_gerado.replace("```html", "").replace("```", "").strip()

def build_final_html(ai_body: str, item: Dict) -> str:
    """Acopla componentes de UI modernos, data localizada e tags ocultas de rastreamento."""
    fuso_brasilia = datetime.timezone(datetime.timedelta(hours=-3))
    data_atual = datetime.datetime.now(fuso_brasilia)
    
    meses_pt = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
        7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    data_formatada = f"{data_atual.day} de {meses_pt[data_atual.month]} de {data_atual.year}"
    
    html_topo = f"""
    <div style="background-color: #f8f9fa; border-left: 4px solid #28a745; padding: 12px 16px; margin-bottom: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; border-radius: 0 6px 6px 0;">
        <span style="color: #495057; font-weight: bold; font-size: 14px;">📅 Vaga Atualizada em: {data_formatada}</span>
    </div>
    """
    
    html_rodape = f"""
    <hr style="border: 0; border-top: 1px solid #e9ecef; margin: 30px 0;" />
    <div style="text-align: center; margin: 25px 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <p style="color: #6c757d; font-size: 14px; margin-bottom: 15px;">Interessado? Veja os detalhes da candidatura e envie seu currículo diretamente na página oficial:</p>
        <a href="{item['link']}" target="_blank" rel="noopener noreferrer" 
           style="background-color: #28a745; color: #ffffff; padding: 14px 28px; text-decoration: none; font-weight: bold; border-radius: 4px; display: inline-block; font-size: 16px; box-shadow: 0 4px 6px rgba(40, 167, 69, 0.15); transition: background-color 0.2s;">
            👉 Quero Me Candidatar à Vaga
        </a>
    </div>
    <meta name="original_source" content="{item['link']}" />
    """
    return f"{html_topo}\n{ai_body}\n{html_rodape}"

# ==========================================
# PUBLICADOR OFICIAL VIA API
# ==========================================
def send_to_blogger(blogger_service, title: str, html_content: str):
    body = {
        "kind": "blogger#post",
        "title": title,
        "content": html_content,
        "labels": ["Vagas", "Vaga de Motorista"]
    }
    try:
        request = blogger_service.posts().insert(blogId=BLOG_ID, body=body)
        response = request.execute()
        print(f"🎉 [SUCESSO] Post publicado nativamente no Blogger! URL: {response.get('url')}")
    except HttpError as e:
        print(f"❌ [ERRO CRÍTICO] Falha ao injetar post na API do Blogger: {e}")

# ==========================================
# CONTROLADOR PRINCIPAL DA ROTINA
# ==========================================
def main():
    print("🚀 [START] Iniciando o robô agregador inteligente de motoristas...")
    
    if not BLOG_ID:
        print("❌ [ERRO] Variável BLOG_ID ausente no ambiente.")
        return

    blogger = get_blogger_service()
    gemini = get_gemini_client()
    
    print("📥 Coletando histórico de postagens recentes...")
    historical_urls, historical_titles = fetch_published_urls(blogger)
    print(f"📊 Histórico ativo carregado: {len(historical_urls)} URLs e {len(historical_titles)} títulos mapeados.")
    
    vaga_selecionada = None
    
    # FASE 1: Canais Profissionais Reais
    vagas_fase1 = parse_feed_list(FEEDS_PROFISSIONAIS, historical_urls, historical_titles)
    if vagas_fase1:
        print(f"🔥 [FASE 1] Sucesso! Encontradas {len(vagas_fase1)} vagas limpas. Selecionando a primeira.")
        vaga_selecionada = vagas_fase1[0]
        
    # FASE 2: Fallback Estrito Google News (Termo Exato)
    if not vaga_selecionada:
        print("💤 [FASE 1] Zero vagas inéditas nos feeds. Ativando FASE 2...")
        vagas_fase2 = buscar_vagas_google_news('"vaga de motorista"', historical_urls, historical_titles, "FASE 2")
        if vagas_fase2:
            print(f"🎯 [FASE 2] Sucesso! Capturada vaga em Google News Estrito.")
            vaga_selecionada = vagas_fase2[0]

    # FASE 3: Fallback de Segurança Máxima (Termos Amplificados de Urgência)
    if not vaga_selecionada:
        print("⚠️ [FASE 2] Sem resultados limpos no termo estrito. Ativando FASE 3 (Garantia de Postagem)...")
        termos_fallback = [
            "emprego motorista categoria D",
            "contrata-se motorista",
            "vagas motorista CNH E"
        ]
        
        for termo in termos_fallback:
            vagas_fase3 = buscar_vagas_google_news(termo, historical_urls, historical_titles, "FASE 3")
            if vagas_fase3:
                print(f"⚡ [FASE 3] Sucesso absoluto! Vaga localizada usando o termo amplo: '{termo}'")
                vaga_selecionada = vagas_fase3[0]
                break

    # ETAPA FINAL: GERAÇÃO E ENTREGA
    if vaga_selecionada:
        try:
            artigo_html_bruto = ask_gemini_to_rewrite(gemini, vaga_selecionada)
            post_completo_html = build_final_html(artigo_html_bruto, vaga_selecionada)
            send_to_blogger(blogger, vaga_selecionada['title'], post_completo_html)
            
        except Exception as err:
            print(f"💥 [FALHA] Não foi possível processar a vaga '{vaga_selecionada['title']}': {err}")
    else:
        print("📭 [FINALIZADO] Todas as fontes de contingência foram exauridas e nenhuma nova oportunidade foi encontrada.")

if __name__ == "__main__":
    main()
