import os
import json
import logging
import urllib.request

logging.basicConfig(level=logging.INFO)

def chamar_api_gemini_texto_puro(prompt):
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
    # Para vagas, usamos uma imagem padrão de alta qualidade focada em contratação/caminhão
    img_vaga = "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=800&auto=format&fit=crop"
    
    prompt = f"""
    Você é um redator profissional especialista no mercado de transportes rodoviários no Brasil.
    Crie um artigo detalhado, longo e muito atraente para divulgar uma vaga de emprego.

    REGRAS DE CONTEÚDO (ANTI-PLÁGIO):
    1. O texto final DEVE ter no mínimo 20 linhas de parágrafos bem desenvolvidos e profundos.
    2. Fale sobre a importância do motorista para a logística regional, os desafios da rota e boas práticas de segurança.
    3. NÃO copie a descrição original. Use suas próprias palavras.

    REGRAS DE FORMATAÇÃO:
    - Escreva a resposta DIRETAMENTE em HTML válido (usando <p>, <strong>, <ul>, <li>).
    - NÃO envolva o código em blocos de markdown. Comece direto no texto.
    - Na PRIMEIRA linha do texto, adicione exatamente isto: <p><strong>📅 Publicado em: {data_postagem}</strong></p>
    - Logo após a data, coloque a imagem da vaga centralizada com esta estrutura: <p align="center"><img src="{img_vaga}" alt="Vaga de Motorista" style="max-width:100%; height:auto; margin:15px 0; border-radius:5px;"></p>
    - No FINAL do texto, coloque o link: <p>Para se candidatar, acesse: <a href='{vaga['link']}' target='_blank'>Clique aqui para ir ao site do {vaga['fonte']}</a>.</p>

    Dados Base da Vaga:
    Título: {vaga['titulo']}
    Descrição original: {vaga['descricao']}
    Fonte: {vaga['fonte']}
    """
    try:
        conteudo_html = chamar_api_gemini_texto_puro(prompt)
        conteudo_html = conteudo_html.replace("```html", "").replace("```", "").strip()
        titulo_seo = f"Vaga de Motorista: Oportunidade para Profissional - {vaga['titulo']}"
        
        return {"e_motorista": True, "titulo_otimizado": titulo_seo, "conteudo_html": conteudo_html}
    except Exception as e:
        logging.error(f"Erro na vaga pelo Gemini: {e}")
        return {"e_motorista": False, "titulo_otimizado": "", "conteudo_html": ""}

def formatar_noticia_com_gemini(noticia, data_postagem):
    # Recupera a imagem que capturamos do site original ou a padrão
    img_noticia = noticia.get('url_imagem', 'https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=800&auto=format&fit=crop')
    
    prompt = f"""
    Você é um experiente jornalista focado nas rodovias e no transporte de cargas no Brasil.
    Transforme a notícia curta abaixo em um artigo jornalístico completo, profundo e 100% INÉDITO.

    REGRAS DE CONTEÚDO (ANTI-PLÁGIO):
    1. O artigo DEVE ter no mínimo 20 linhas de puro texto descritivo e contextualizado.
    2. Desenvolva o tema! Explique o impacto do assunto na rotina de quem vive no trecho.
    3. Crie uma redação totalmente nova do zero.

    REGRAS DE FORMATAÇÃO:
    - Escreva a resposta DIRETAMENTE em HTML válido (usando <p>, <strong>, <ul>, <li>).
    - NÃO use blocos de código markdown.
    - Na PRIMEIRA linha do texto, insira: <p><strong>📅 Publicado em: {data_postagem}</strong></p>
    - Logo após a data, coloque a imagem da notícia centralizada: <p align="center"><img src="{img_noticia}" alt="Notícia Caminhão" style="max-width:100%; height:auto; margin:15px 0; border-radius:5px;"></p>
    - No final do texto: <p>Acompanhe a matéria completa no portal original: <a href='{noticia['link']}' target='_blank'>{noticia['fonte_original']}</a>.</p>

    Notícia Base:
    Título original: {noticia['titulo']}
    Conteúdo extraído: {noticia['descricao']}
    """
    try:
        logging.info("Enviando conteúdo para reescrita expandida com imagem...")
        conteudo_html = chamar_api_gemini_texto_puro(prompt)
        conteudo_html = conteudo_html.replace("```html", "").replace("```", "").strip()
        titulo_seo = f"Informativo para Motoristas: {noticia['titulo']}"
        
        return {"titulo_otimizado": titulo_seo, "conteudo_html": conteudo_html}
    except Exception as e:
        logging.error(f"Erro na notícia pelo Gemini: {e}")
        return {
            "titulo_otimizado": f"Informativo para Motoristas: {noticia['titulo']}",
            "conteudo_html": f"<p><strong>📅 Publicado em: {data_postagem}</strong></p><p align=\"center\"><img src=\"{img_noticia}\" style=\"max-width:100%;\"></p><p>{noticia['descricao']}</p>"
        }
