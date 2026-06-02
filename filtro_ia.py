import os
import json
import urllib.request

def analisar_vaga_com_ia(titulo, descricao):
    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    
    if not api_key:
        print("⚠️ Sem GOOGLE_API_KEY. Usando formatação padrão sem IA.")
        return {
            "valida": True,
            "localizacao": "Brasil",
            "texto_html": f"<h3>Oportunidade: {titulo}</h3><p>{descricao}</p>"
        }
        
    # Endpoint oficial do Gemini 1.5 Flash (rápido e econômico para textos)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # Prompt estruturado para forçar o Gemini a responder apenas um JSON puro
    prompt = f"""
    Você é um assistente de recrutamento para um blog de empregos de motoristas.
    Analise a vaga abaixo:
    Título: {titulo}
    Descrição: {descricao}

    Regras:
    1. Se a vaga NÃO for de motorista (ex: entregador de bike, mecânico, ajudante), defina "valida" como false.
    2. Descubra a cidade/estado da vaga. Se não achar, use "Brasil".
    3. Crie um texto formatado em HTML profissional, limpo, destacando Requisitos, Benefícios e Atividades em tópicos (<ul> e <li>). Use títulos <h3>. Não use a tag <html> ou <body>, apenas as tags de conteúdo.

    Responda ESTRITAMENTE em formato JSON com esta estrutura (sem usar blocos de código markdown como ```json):
    {{"valida": true ou false, "localizacao": "Cidade - Estado", "texto_html": "texto aqui"}}
    """

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=15) as response:
            resultado = json.loads(response.read().decode('utf-8'))
            
        texto_resposta = resultado['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Limpa possíveis blocos de marcação que a IA insira por teimosia
        texto_resposta = texto_resposta.replace("```json", "").replace("```", "").strip()
        
        data_json = json.loads(texto_resposta)
        return data_json

    except Exception as e:
        print(f"⚠️ Erro no processamento da IA: {e}")
        # Retorno de segurança caso a IA falhe ou dê erro de cota
        return {
            "valida": True,
            "localizacao": "Brasil",
            "texto_html": f"<h3>{titulo}</h3><p>{descricao}</p>"
        }
