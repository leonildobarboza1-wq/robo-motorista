import os
import json
import logging

def chamar_api_gemini_com_json(prompt):
    api_key = os.getenv('GOOGLE_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}], 
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7}
    }
    import urllib.request
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=50) as response:
        resultado = json.loads(response.read().decode('utf-8'))
        return json.loads(resultado['candidates'][0]['content']['parts'][0]['text'].strip())

def processar_vaga_com_gemini(vaga, data_postagem):
    prompt = f"""
    Escreva uma matéria detalhada sobre esta vaga: {vaga['titulo']}.
    Siga estas regras:
    - O texto deve ter pelo menos 300 palavras.
    - Fale sobre a importância da função, segurança rodoviária e habilidades necessárias.
    - Use HTML puro com parágrafos <p> e tópicos <ul>/<li>.
    - NÃO use tags <img>.
    Retorne ESTRITAMENTE um JSON:
    {{"titulo_otimizado": "Título atrativo", "conteudo_html": "<p>...</p>"}}
    """
    # ... (o resto da função de chamada da API)

def formatar_noticia_com_gemini(noticia, data_postagem):
    prompt = f"""
    Transforme esta notícia em um artigo detalhado de pelo menos 250 palavras: {noticia['titulo']}.
    Retorne ESTRITAMENTE um JSON com:
    - "titulo_otimizado": "Notícia: {noticia['titulo']}"
    - "conteudo_html": "<p>📅 Publicado em: {data_postagem}</p><p>Desenvolvimento completo da matéria...</p>"
    """
    try:
        return chamar_api_gemini_com_json(prompt)
    except:
        return {"titulo_otimizado": noticia['titulo'], "conteudo_html": f"<p>Leia mais sobre: {noticia['titulo']}.</p>"}
