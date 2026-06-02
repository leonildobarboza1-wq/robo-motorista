import os
import json
import logging
from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)

def obter_cliente():
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não configurada no ambiente do GitHub.")
    return genai.Client(api_key=api_key)

def processar_vaga_com_gemini(vaga, api_key_ignorada=None):
    client = obter_cliente()
    
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
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text.strip())
    except Exception as e:
        logging.error(f"Erro ao processar vaga no Gemini: {e}")
        return {"e_motorista": False, "titulo_otimizado": "", "conteudo_html": ""}

def formatar_noticia_com_gemini(noticia, api_key_ignorada=None):
    client = obter_cliente()
    
    prompt = f"""
    Você é um jornalista especializado no setor de transportes rodoviários no Brasil.
    Reescreva a notícia abaixo em um formato de artigo curto e atraente para caminhoneiros.
    Organize o texto usando parágrafos curtos (<p>) e intertítulos com <strong>.

    Notícia Bruta:
    Título: {noticia['titulo']}
    Conteúdo: {noticia['descricao']}
    Fonte original: {noticia['fonte_original']}
    """
    
    try:
        logging.info("Enviando notícia reserva para o novo SDK do Gemini...")
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return json.loads(response.text.strip())
    except Exception as e:
        logging.error(f"Erro ao reescrever notícia no Gemini Novo: {e}")
        return {
            "titulo_otimizado": noticia['titulo'],
            "conteudo_html": f"<p>{noticia['descricao']}</p><p>Confira na fonte: <a href='{noticia['link']}'>{noticia['fonte_original']}</a>.</p>"
        }
