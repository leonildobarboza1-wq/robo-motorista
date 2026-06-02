import os
import json
import logging
import urllib.request

logging.basicConfig(level=logging.INFO)

def chamar_api_gemini(prompt):
    """Faz uma requisição HTTP direta para a API estável do Gemini v1beta"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada no ambiente.")
        
    # Usando o endpoint HTTP oficial e direto para o modelo estável
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
    req = urllib.request.Request(
        url, 
        data=data, 
        headers={'Content-Type': 'application/json'}, 
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=30) as response:
        resultado = json.loads(response.read().decode('utf-8'))
        # Extrai o texto da resposta estruturada do Google
        texto_resposta = resultado['candidates'][0]['content']['parts'][0]['text']
        return json.loads(texto_resposta.strip())

def processar_vaga_com_gemini(vaga, api_key_ignorada=None):
    prompt = f"""
    Você é um recrutador especialista no setor de transportes no Brasil.
    Analise os dados e identifique se a vaga é REALMENTE para motoristas profissionais.
    Se NÃO for, retorne a chave "e_motorista" como false.
    Se FOR, formate o corpo em HTML limpo.

    Dados da vaga:
    Título original: {vaga['titulo']}
    Descrição original: {vaga['descricao']}
    Link original: {vaga['link']}
    Fonte: {vaga['fonte']}

    Retorne um JSON estruturado:
    {{
        "e_motorista": true,
        "titulo_otimizado": "Vaga de Motorista...",
        "conteudo_html": "Conteúdo formatado"
    }}
    """
    try:
        return chamar_api_gemini(prompt)
    except Exception as e:
        logging.error(f"Erro no processamento da vaga pelo Gemini: {e}")
        return {"e_motorista": False, "titulo_otimizado": "", "conteudo_html": ""}

def formatar_noticia_com_gemini(noticia, api_key_ignorada=None):
    prompt = f"""
    Você é um jornalista especializado no setor de transportes rodoviários no Brasil.
    Reescreva a notícia de forma atraente para o nosso blog de caminhoneiros.
    O título obrigatoriamente DEVE começar com "Vaga de Motorista ou Informativo:" para manter o padrão visual.

    Notícia Bruta:
    Título: {noticia['titulo']}
    Conteúdo: {noticia['descricao']}
    Fonte original: {noticia['fonte_original']}

    Retorne um JSON estruturado:
    {{
        "titulo_otimizado": "Informativo para Motoristas: Título Otimizado SEO",
        "conteudo_html": "Texto reescrito em parágrafos HTML"
    }}
    """
    try:
        logging.info("Enviando notícia para a API direta do Gemini...")
        return chamar_api_gemini(prompt)
    except Exception as e:
        logging.error(f"Erro no processamento da notícia pelo Gemini: {e}")
        return {
            "titulo_otimizado": f"Informativo para Motoristas: {noticia['titulo']}",
            "conteudo_html": f"<p>{noticia['descricao']}</p><p>Confira na fonte: <a href='{noticia['link']}'>{noticia['fonte_original']}</a>.</p>"
        }
