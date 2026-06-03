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
    prompt = f"Escreva uma matéria detalhada de 300 palavras sobre: {vaga['titulo']}. Retorne JSON com 'titulo_otimizado' e 'conteudo_html' (use <p> e <ul>, sem <img>)."
    try:
        return chamar_api_gemini_com_json(prompt)
    except:
        return {"titulo_otimizado": vaga['titulo'], "conteudo_html": f"<p>Vaga disponível em {vaga['fonte']}.</p>"}

def formatar_noticia_com_gemini(noticia, data_postagem):
    prompt = f"Escreva um artigo detalhado de 300 palavras sobre: {noticia['titulo']}. Retorne JSON com 'titulo_otimizado' e 'conteudo_html' (use <p> e <ul>, sem <img>)."
    try:
        return chamar_api_gemini_com_json(prompt)
    except:
        return {"titulo_otimizado": noticia['titulo'], "conteudo_html": f"<p>Leia mais em: {noticia['link']}</p>"}
