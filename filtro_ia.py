import os
import json
import logging
import urllib.request

logging.basicConfig(level=logging.INFO)

def chamar_api_gemini_texto_puro(prompt):
    """Faz a requisição direta ao Gemini esperando o texto do artigo em HTML"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada no ambiente do GitHub.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    with urllib.request.urlopen(req, timeout=45) as response:
        resultado = json.loads(response.read().decode('utf-8'))
        texto_resposta = resultado['candidates'][0]['content']['parts'][0]['text']
        return texto_resposta.strip()

def processar_vaga_com_gemini(vaga, data_postagem):
    prompt = f"""
    Você é um redator profissional especialista no mercado de transportes rodoviários no Brasil.
    Crie um artigo detalhado, longo e muito atraente para divulgar uma vaga de emprego.

    REGRAS DE CONTEÚDO (ANTI-PLÁGIO):
    1. O texto final DEVE ter no mínimo 20 linhas de parágrafos bem desenvolvidos e profundos.
    2. Fale sobre a importância do motorista para a logística regional, os desafios da rota e boas práticas de segurança.
    3. NÃO copie a descrição original. Use suas próprias palavras para expandir o conteúdo de forma inédita.

    REGRAS DE FORMATAÇÃO:
    - Escreva a resposta DIRETAMENTE em HTML válido (usando <p>, <strong>, <ul>, <li>).
    - NÃO envolva o código em blocos de markdown como ```html. Comece direto no texto.
    - Na PRIMEIRA linha do texto, adicione exatamente isto: <p><strong>📅 Publicado em: {data_postagem}</strong></p>
    - No FINAL do texto, coloque o link: <p>Para se candidatar e ver todos os detalhes, acesse: <a href='{vaga['link']}' target='_blank'>Clique aqui para ir ao site de recrutamento do {vaga['fonte']}</a>.</p>

    Dados Base da Vaga:
    Título: {vaga['titulo']}
    Descrição original: {vaga['descricao']}
    Fonte: {vaga['fonte']}
    """
    try:
        conteudo_html = chamar_api_gemini_texto_puro(prompt)
        conteudo_html = conteudo_html.replace("```html", "").replace("```", "").strip()
        
        # Define o título dinâmico otimizado para a Home do Blog
        titulo_seo = f"Vaga de Motorista: Oportunidade para Profissional - {vaga['titulo']}"
        
        return {
            "e_motorista": True, 
            "titulo_otimizado": titulo_seo, 
            "conteudo_html": conteudo_html
        }
    except Exception as e:
        logging.error(f"Erro no processamento da vaga pelo Gemini: {e}")
        return {"e_motorista": False, "titulo_otimizado": "", "conteudo_html": ""}

def formatar_noticia_com_gemini(noticia, data_postagem):
    prompt = f"""
    Você é um experiente jornalista focado nas rodovias e no transporte de cargas no Brasil.
    Transforme a notícia curta abaixo em um artigo jornalístico completo, profundo e 100% INÉDITO.

    REGRAS DE CONTEÚDO (ANTI-PLÁGIO):
    1. O artigo DEVE ter no mínimo 20 linhas de puro texto descritivo e contextualizado.
    2. Desenvolva o tema! Explique o impacto do assunto na rotina de quem vive no trecho, traga dicas de segurança relacionadas ao fato e como o motorista deve se planejar.
    3. Crie uma redação totalmente nova do zero, evitando penalizações de conteúdo duplicado no Google.

    REGRAS DE FORMATAÇÃO:
    - Escreva a resposta DIRETAMENTE em HTML válido (usando <p>, <strong>, <ul>, <li>).
    - NÃO use blocos de código com ```html. Comece direto no texto.
    - Na PRIMEIRA linha do texto, insira obrigatoriamente: <p><strong>📅 Publicado em: {data_postagem}</strong></p>
    - No final do texto, referencie a fonte: <p>Acompanhe a matéria de referência completa no portal original: <a href='{noticia['link']}' target='_blank'>{noticia['fonte_original']}</a>.</p>

    Notícia Base:
    Título original: {noticia['titulo']}
    Conteúdo extraído: {noticia['descricao']}
    Fonte: {noticia['fonte_original']}
    """
    try:
        logging.info("Enviando conteúdo para reescrita expandida e profunda...")
        conteudo_html = chamar_api_gemini_texto_puro(prompt)
        conteudo_html = conteudo_html.replace("```html", "").replace("```", "").strip()
        
        # Monta o título seguindo o padrão exigido pelo seu layout do Blogger
        titulo_seo = f"Informativo para Motoristas: {noticia['titulo']}"
        
        return {
            "titulo_otimizado": titulo_seo,
            "conteudo_html": conteudo_html
        }
    except Exception as e:
        logging.error(f"Erro no processamento da notícia pelo Gemini: {e}")
        return {
            "titulo_otimizado": f"Informativo para Motoristas: {noticia['titulo']}",
            "conteudo_html": f"<p><strong>📅 Publicado em: {data_postagem}</strong></p><p>{noticia['descricao']}</p><p>Confira na fonte: <a href='{noticia['link']}'>{noticia['fonte_original']}</a>.</p>"
        }
