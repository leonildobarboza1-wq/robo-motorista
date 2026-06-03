import os
import json
import logging

logging.basicConfig(level=logging.INFO)

def chamar_api_gemini_com_json(prompt):
    # (Mantém a lógica da função igual, apenas para garantir a chamada)
    api_key = os.getenv('GOOGLE_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}}
    
    import urllib.request
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=50) as response:
        resultado = json.loads(response.read().decode('utf-8'))
        return json.loads(resultado['candidates'][0]['content']['parts'][0]['text'].strip())

def processar_vaga_com_gemini(vaga, data_postagem):
    prompt = f"""
    Você é um redator profissional. Escreva uma matéria de 20 linhas sobre esta vaga: {vaga['titulo']}.
    Retorne ESTRITAMENTE um JSON com:
    - "titulo_otimizado": Título profissional.
    - "conteudo_html": Um HTML robusto que comece com uma tag de parágrafo. Exemplo: 
      "<p><strong>Data: {data_postagem}</strong></p><p>Oportunidade para motorista profissional...</p>..."
      Não use tags de imagem. Garanta que o texto seja longo e informativo.
    """
    # (Resto da função de chamada da API)

def formatar_noticia_com_gemini(noticia, data_postagem):
    prompt = f"""
    Você é um jornalista de logística. Transforme esta notícia em matéria: {noticia['titulo']}.
    Retorne ESTRITAMENTE um JSON com:
    - "titulo_otimizado": Manchete impactante e única.
    - "conteudo_html": O texto em HTML (mínimo 20 linhas), COM A ESTRUTURA:
      <p>📅 Publicado em: {data_postagem}</p>
      <p>Desenvolvimento da matéria jornalística.</p>
      <p>Fonte original: <a href='{noticia['link']}'>{noticia['fonte_original']}</a>.</p>
      NÃO INSIRA TAGS <img> AQUI.
    """
    try:
        dados = chamar_api_gemini_com_json(prompt)
        return {"titulo_otimizado": dados["titulo_otimizado"], "conteudo_html": dados["conteudo_html"]}
    except:
        return {"titulo_otimizado": noticia['titulo'], "conteudo_html": f"<p>{noticia['descricao']}</p>"}
