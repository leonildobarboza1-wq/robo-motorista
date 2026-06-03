import os
import json
import logging
import urllib.request

def chamar_api_gemini_com_json(prompt):
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        logging.error("GOOGLE_API_KEY não configurada!")
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}], 
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7}
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=50) as response:
        resultado = json.loads(response.read().decode('utf-8'))
        texto = resultado['candidates'][0]['content']['parts'][0]['text'].strip()
        return json.loads(texto)

def processar_vaga_com_gemini(vaga, data_postagem):
    prompt = f"Escreva uma matéria detalhada de 300 palavras sobre: {vaga['titulo']}. Retorne JSON com 'titulo_otimizado' e 'conteudo_html' (use <p> e <ul>, sem <img>)."
    try:
        dados = chamar_api_gemini_com_json(prompt)
        conteudo_final = f"<p>📅 Publicado em: {data_postagem}</p><p>{dados['conteudo_html']}</p><hr /><p><strong>Fonte da Vaga:</strong> <a href='{vaga['link']}' target='_blank'>{vaga['fonte']}</a></p>"
        return {"titulo_otimizado": dados["titulo_otimizado"], "conteudo_html": conteudo_final}
    except Exception as e:
        logging.error(f"Erro na IA: {e}")
        return None

def formatar_noticia_com_gemini(noticia, data_postagem):
    prompt = f"Escreva um artigo detalhado de 300 palavras sobre: {noticia['titulo']}. Retorne JSON com 'titulo_otimizado' e 'conteudo_html' (use <p> e <ul>, sem <img>)."
    try:
        dados = chamar_api_gemini_com_json(prompt)
        conteudo_final = f"<p>📅 Publicado em: {data_postagem}</p><p>{dados['conteudo_html']}</p><hr /><p><strong>Fonte original:</strong> <a href='{noticia['link']}' target='_blank'>{noticia['fonte_original']}</a></p>"
        return {"titulo_otimizado": dados["titulo_otimizado"], "conteudo_html": conteudo_final}
    except Exception as e:
        logging.error(f"Erro na IA: {e}")
        return None
