import os
import json
import logging
import urllib.request

logging.basicConfig(level=logging.INFO)

def chamar_api_gemini_com_json(prompt):
    """Faz a requisição ao Gemini exigindo um retorno JSON estrito e seguro"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada no ambiente do GitHub.")
        
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
    
    with urllib.request.urlopen(req, timeout=50) as response:
        resultado = json.loads(response.read().decode('utf-8'))
        texto_resposta = resultado['candidates'][0]['content']['parts'][0]['text']
        return json.loads(texto_resposta.strip())

def processar_vaga_com_gemini(vaga, data_postagem):
    img_vaga = "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=800&auto=format&fit=crop"
    
    prompt = f"""
    Você é un redator profissional sênior focado no mercado de transportes rodoviários.
    Sua tarefa é expandir uma vaga de emprego para motoristas profissionais.

    REGRA CRÍTICA DE TÍTULO (ANTI-REPETIÇÃO):
    - Crie um título dinâmico, chamativo e profissional focado na oportunidade.
    - PROIBIDO começar o título com frases repetitivas como "Vaga de Motorista:", "Oportunidade:", "Contrata-se:" ou "Emprego:".
    - Varie a estrutura! Exemplos bons: "Transportadora abre processo seletivo para profissionais de Categoria E", "Nova oportunidade para Motorista Carreteiro em rotas nacionais", "Procura-se condutor de caminhão pesado com experiência".

    REGRAS DE CONTEÚDO E HTML:
    1. O campo "conteudo_html" deve ser rico, conter no mínimo 20 linhas e usar tags HTML (<p>, <strong>, <ul>, <li>).
    2. Comece com: <p><strong>📅 Publicado em: {data_postagem}</strong></p>
    3. Adicione a imagem: <p align="center"><img src="{img_vaga}" alt="Oportunidade" style="max-width:100%; height:auto; margin:15px 0; border-radius:5px;"></p>
    4. Encerre com o link: <p><strong>📋 Como se candidatar:</strong> Envie seu currículo diretamente através do canal de captação oficial da empresa: <a href='{vaga['link']}' target='_blank'>Clique aqui para acessar o site {vaga['fonte']}</a>.</p>

    Dados da Vaga:
    Título Original: {vaga['titulo']}
    Descrição Original: {vaga['descricao']}

    Retorne ESTRITAMENTE este JSON:
    {{
        "titulo_otimizado": "[Seu título exclusivo, variado e magnético aqui]",
        "conteudo_html": "[Seu HTML completo contendo mais de 20 linhas de texto e o link no final]"
    }}
    """
    try:
        dados = chamar_api_gemini_com_json(prompt)
        return {
            "e_motorista": True,
            "titulo_otimizado": dados["titulo_otimizado"],
            "conteudo_html": dados["conteudo_html"]
        }
    except Exception as e:
        logging.error(f"Erro ao processar vaga: {e}")
        return {"e_motorista": False, "titulo_otimizado": "", "conteudo_html": ""}

def formatar_noticia_com_gemini(noticia, data_postagem):
    img_noticia = noticia.get('url_imagem', 'https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=800&auto=format&fit=crop')
    
    prompt = f"""
    Você é um experiente jornalista especializado em estradas, frotas pesadas e logística brasileira.
    Transforme a notícia base em uma matéria aprofundada, fluida e 100% inédita.

    REGRA CRÍTICA DE TÍTULO (ANTI-REPETIÇÃO):
    - Crie uma manchete jornalística forte, atraente e única sobre o acontecimento.
    - PROIBIDO começar o título com expressões repetitivas como "Informativo para Motoristas:", "Notícia:", "Atenção Caminhoneiros:" ou "Aviso:".
    - Varie o começo! Exemplos: "Rodovias federais terão fiscalização intensa a partir desta semana", "Mercedes-Benz avança nos testes de novos caminhões elétricos", "Restrições de tráfego pesado mudam a rotina nas estradas".

    REGRAS DE CONTEÚDO E HTML:
    1. O campo "conteudo_html" deve ser jornalístico, contextualizado, contendo no mínimo 20 linhas e estruturado em HTML (<p>, <strong>, <ul>, <li>).
    2. Comece com: <p><strong>📅 Publicado em: {data_postagem}</strong></p>
    3. Adicione a imagem: <p align="center"><img src="{img_noticia}" alt="Matéria Rodovias" style="max-width:100%; height:auto; margin:15px 0; border-radius:5px;"></p>
    4. Encerre referenciando a fonte: <p>Texto desenvolvido com informações apuradas originalmente pelo veículo parceiro de imprensa: <a href='{noticia['link']}' target='_blank'>{noticia['fonte_original']}</a>.</p>

    Dados do Fato:
    Título Base: {noticia['titulo']}
    Conteúdo Extraído: {noticia['descricao']}

    Retorne ESTRITAMENTE este JSON:
    {{
        "titulo_otimizado": "[Sua manchete jornalística inédita, chamativa e variada aqui]",
        "conteudo_html": "[Seu artigo longo com mais de 20 linhas em HTML e o link da fonte no final]"
    }}
    """
    try:
        logging.info("Enviando conteúdo para geração de título variado e matéria longa...")
        dados = chamar_api_gemini_com_json(prompt)
        return {
            "titulo_otimizado": dados["titulo_otimizado"],
            "conteudo_html": dados["conteudo_html"]
        }
    except Exception as e:
        logging.error(f"Erro ao processar notícia: {e}")
        html_emergencia = f"""
        <p><strong>📅 Publicado em: {data_postagem}</strong></p>
        <p align="center"><img src="{img_noticia}" style="max-width:100%; border-radius:5px;"></p>
        <p>{noticia['descricao']}</p>
        <p>Acompanhe a cobertura completa direto na fonte: <a href='{noticia['link']}' target='_blank'>{noticia['fonte_original']}</a>.</p>
        """
        return {
            "titulo_otimizado": noticia['titulo'],
            "conteudo_html": html_emergencia
        }
