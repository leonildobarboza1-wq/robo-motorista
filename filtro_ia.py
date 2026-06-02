import os
import json
import logging
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)

def processar_vaga_com_gemini(vaga, api_key):
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não configurada no ambiente.")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Você é um assistente especialista em recrutamento e seleção de motoristas profissionais no Brasil.
    Analise os dados abaixo e identifique se a vaga é REALMENTE para motoristas profissionais (Caminhão, Ônibus, Carreta, Entrega, Van, etc.).
    Se NÃO for uma vaga de motorista, retorne a chave "e_motorista" como false.
    Se FOR, extraia os dados e formate o corpo em HTML limpo (use apenas tags como <p>, <ul>, <li>, <strong>).

    Dados da vaga:
    Título original: {vaga['titulo']}
    Descrição original: {vaga['descricao']}
    Link original: {vaga['link']}

    Sua resposta deve ser estritamente um JSON com a seguinte estrutura, sem blocos de código markdown:
    {{
        "e_motorista": true ou false,
        "titulo_otimizado": "Título claro com Cidade/UF se houver",
        "conteudo_html": "HTML limpo detalhando Requisitos, Atividades e Benefícios e incluindo o link original para candidatura."
    }}
    """
    
    try:
        # Configuração para forçar resposta em formato JSON
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        resultado = json.loads(response.text.strip())
        return resultado
    except Exception as e:
        logging.error(f"Erro ao processar vaga no Gemini: {e}")
        return {"e_motorista": False, "titulo_otimizado": "", "conteudo_html": ""}
