import os
import json
import logging
import urllib.request

logging.basicConfig(level=logging.INFO)

def chamar_api_gemini(prompt):
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada no ambiente.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    with urllib.request.urlopen(req, timeout=40) as response:
        resultado = json.loads(response.read().decode('utf-8'))
        texto_resposta = resultado['candidates'][0]['content']['parts'][0]['text']
        return json.loads(texto_resposta.strip())

def processar_vaga_com_gemini(vaga, data_postagem):
    prompt = f"""
    Você é um redator e recrutador profissional do setor de transportes no Brasil.
    Sua missão é criar um artigo de divulgação de vaga de emprego TOTALMENTE INÉDITO, longo e detalhado, para evitar plágio ou conteúdo duplicado.

    REGRAS CRÍTICAS:
    1. O texto final deve ser extenso, contendo no mínimo 20 linhas de parágrafos explicativos desenvolvidos por você.
    2. NÃO copie a descrição original. Use suas próprias palavras para explicar a importância do cargo, o cenário do mercado na região da vaga e destrinchar os requisitos.
    3. Use tags HTML estruturadas: <p> para parágrafos, <strong> para destaques, <ul> e <li> para listas.

    Dados da Vaga Original:
    Título: {vaga['titulo']}
    Descrição: {vaga['descricao']}
    Fonte de Origem: {vaga['fonte']}

    Retorne ESTRITAMENTE um JSON com esta estrutura (sem markdown):
    {{
        "e_motorista": true,
        "titulo_otimizado": "Título Otimizado para SEO chamando atenção para a vaga",
        "conteudo_html": "<p><strong>📅 Publicado em: {data_postagem}</strong></p><p>Escreva aqui uma introdução detalhada sobre a profissão e o mercado de transporte na região...</p><p>Desenvolva mais parágrafos explicando detalhadamente a oportunidade (garantindo o tamanho longo de pelo menos 20 linhas)...</p><strong>📋 Requisitos e Qualificações Detalhadas:</strong><ul><li>Descreva os requisitos aqui</li></ul><strong>🎁 Benefícios Esperados:</strong><ul><li>Descreva os benefícios</li></ul><p>Para se candidatar e ver mais detalhes, acesse o link oficial do recrutamento: <a href='{vaga['link']}' target='_blank'>Clique aqui para ir ao site {vaga['fonte']}</a>.</p>"
    }}
    """
    try:
        return chamar_api_gemini(prompt)
    except Exception as e:
        logging.error(f"Erro no processamento da vaga pelo Gemini: {e}")
        return {"e_motorista": False, "titulo_otimizado": "", "conteudo_html": ""}

def formatar_noticia_com_gemini(noticia, data_postagem):
    prompt = f"""
    Você é um jornalista de estradas especialista em transporte rodoviário de cargas no Brasil.
    Sua missão é ler a notícia resumida abaixo e escrever um artigo de opinião/jornalístico TOTALMENTE NOVO e expandido, evitando qualquer tipo de plágio.

    REGRAS CRÍTICAS:
    1. O artigo deve ser rico, aprofundado e ter no mínimo 20 linhas de puro texto descritivo escrito por você.
    2. Explique o impacto dessa notícia no dia a dia do caminhoneiro e do motorista profissional. Adicione contexto se necessário.
    3. O título DEVE começar com 'Informativo para Motoristas:' ou 'Vaga de Motorista:' para manter o padrão visual do blog.
    4. Use as tags HTML <p>, <strong>, <ul>, <li>.

    Dados da Notícia Original:
    Título: {noticia['titulo']}
    Conteúdo Base: {noticia['descricao']}
    Fonte: {noticia['fonte_original']}

    Retorne ESTRITAMENTE um JSON com esta estrutura (sem markdown):
    {{
        "titulo_otimizado": "Informativo para Motoristas: Título Impactante para SEO",
        "conteudo_html": "<p><strong>📅 Publicado em: {data_postagem}</strong></p><p>Escreva um parágrafo de introdução contextualizando o leitor...</p><p>Desenvolva a notícia com suas palavras de forma bem explicada e detalhada ao longo de vários parágrafos (mínimo de 20 linhas no total)...</p><p>Analise o impacto real que isso gera nas estradas brasileiras...</p><p>Você pode ler o texto de referência completo direto no portal de origem <a href='{noticia['link']}' target='_blank'>{noticia['fonte_original']}</a>.</p>"
    }}
    """
    try:
        logging.info("Enviando conteúdo para reescrita expandida (Anti-Plágio)...")
        return chamar_api_gemini(prompt)
    except Exception as e:
        logging.error(f"Erro no processamento da notícia pelo Gemini: {e}")
        return {
            "titulo_otimizado": f"Informativo para Motoristas: {noticia['titulo']}",
            "conteudo_html": f"<p><strong>📅 Publicado em: {data_postagem}</strong></p><p>{noticia['descricao']}</p><p>Confira na fonte: <a href='{noticia['link']}'>{noticia['fonte_original']}</a>.</p>"
        }
