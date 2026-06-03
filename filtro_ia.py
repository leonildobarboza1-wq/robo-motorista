def chamar_api_gemini_com_json(prompt):
    api_key = os.getenv('GOOGLE_API_KEY')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    # Aumentamos o temp para a IA ser mais criativa
    payload = {
        "contents": [{"parts": [{"text": prompt}]}], 
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7}
    }
    # ... (resto da função de request permanece igual)

def processar_vaga_com_gemini(vaga, data_postagem):
    prompt = f"""
    Escreva uma matéria detalhada sobre esta vaga de emprego: {vaga['titulo']}.
    O texto deve ter pelo menos 200 palavras. Use parágrafos longos, fale sobre a importância da função, 
    dicas de segurança na estrada e habilidades valorizadas.
    Retorne ESTRITAMENTE um JSON com:
    - "titulo_otimizado": "Vaga: Motorista Profissional - Oportunidade em {vaga['fonte']}"
    - "conteudo_html": "<p>📅 Publicado em: {data_postagem}</p><p>Oportunidades para motoristas estão em alta...</p><p>...</p>"
    """
    # ... (chama a API)
