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
    Você é um redator profissional sênior focado no setor de transportes roroviários no Brasil.
    Sua tarefa é extrair e expandir as informações de uma vaga de emprego para motorista.

    REGRAS CRÍTICAS DE CONTEÚDO (ANTI-PLÁGIO E EXTENSÃO):
    1. O campo "conteudo_html" DEVE ser longo e detalhado, contendo no mínimo 20 linhas completas de texto.
    2. Desenvolva parágrafos longos explicando o mercado na região, a importância da responsabilidade do motorista de caminhão e dicas profissionais. Não copie a descrição original.
    3. Monte a estrutura obrigatoriamente usando tags HTML: <p>, <strong>, <ul>, <li>.

    REGRAS DE MONTAGEM DO HTML:
    - Inicie com: <p><strong>📅 Publicado em: {data_postagem}</strong></p>
    - Logo abaixo insira a imagem: <p align="center"><img src="{img_vaga}" alt="Vaga Motorista" style="max-width:100%; height:auto; margin:15px 0; border-radius:5px;"></p>
    - Desenvolva o texto longo (mínimo 20 linhas).
    - No encerramento insira o link exatamente assim: <p><strong>📋 Como se candidatar:</strong> Para enviar seu currículo e verificar todos os detalhes, acesse o link de recrutamento oficial: <a href='{vaga['link']}' target='_blank'>Clique aqui para ir ao site {vaga['fonte']}</a>.</p>

    Dados da Vaga:
    Título: {vaga['titulo']}
    Descrição: {vaga['descricao']}

    Retorne ESTRITAMENTE um objeto JSON válido com duas chaves textuais:
    {{
        "titulo_otimizado": "Vaga de Motorista: Oportunidade para Profissional - [Título Otimizado aqui]",
        "conteudo_html": "[Insira aqui todo o HTML montado conforme as instruções acima, garantindo mais de 20 linhas de leitura]"
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
        logging.error(f"Erro ao processar vaga estruturada: {e}")
        return {"e_motorista": False, "titulo_otimizado": "", "conteudo_html": ""}

def formatar_noticia_com_gemini(noticia, data_postagem):
    img_noticia = noticia.get('url_imagem', 'https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=800&auto=format&fit=crop')
    
    prompt = f"""
    Você é um jornalista focado em logística pesada e estradas brasileiras.
    Sua missão é criar uma matéria jornalística aprofundada, 100% INÉDITA e rica em conteúdo com base em um fato rápido.

    REGRAS CRÍTICAS DE CONTEÚDO (ANTI-PLÁGIO E EXTENSÃO):
    1. O texto dentro de "conteudo_html" DEVE ter no mínimo 20 linhas de extensão estruturada.
    2. Crie uma introdução rica, explique o contexto do evento nas rodovias, traga recomendações de segurança da PRF para caminhoneiros e faça uma análise do impacto no frete ou na viagem. Não replique frases da fonte.
    3. Formate rigorosamente usando tags HTML: <p>, <strong>, <ul>, <li>.

    REGRAS DE MONTAGEM DO HTML:
    - Inicie com: <p><strong>📅 Publicado em: {data_postagem}</strong></p>
    - Logo abaixo insira a imagem centralizada: <p align="center"><img src="{img_noticia}" alt="Notícia Transporte" style="max-width:100%; height:auto; margin:15px 0; border-radius:5px;"></p>
    - Insira o texto expandido jornalístico (mínimo de 20 linhas de leitura).
    - No final, insira o link da fonte obrigatoriamente assim: <p>Compilado e adaptado a partir da matéria original disponível no portal de notícias: <a href='{noticia['link']}' target='_blank'>{noticia['fonte_original']}</a>.</p>

    Dados do Fato Original:
    Título: {noticia['titulo']}
    Conteúdo base: {noticia['descricao']}

    Retorne ESTRITAMENTE um objeto JSON válido com duas chaves textuais:
    {{
        "titulo_otimizado": "Informativo para Motoristas: [Título Otimizado Impactante Aqui]",
        "conteudo_html": "[Insira aqui todo o HTML gerado conforme as regras acima, contendo obrigatoriamente o texto longo de 20 linhas e o link da fonte no final]"
    }}
    """
    try:
        logging.info("Enviando notícia para processamento estruturado JSON...")
        dados = chamar_api_gemini_com_json(prompt)
        return {
            "titulo_otimizado": dados["titulo_otimizado"],
            "conteudo_html": dados["conteudo_html"]
        }
    except Exception as e:
        logging.error(f"Erro ao processar notícia estruturada: {e}")
        # Retorno seguro completo em caso de falha da IA
        html_emergencia = f"""
        <p><strong>📅 Publicado em: {data_postagem}</strong></p>
        <p align="center"><img src="{img_noticia}" style="max-width:100%; border-radius:5px;"></p>
        <p>{noticia['descricao']}</p>
        <p>Acompanhe a matéria de referência completa no portal original: <a href='{noticia['link']}' target='_blank'>{noticia['fonte_original']}</a>.</p>
        """
        return {
            "titulo_otimizado": f"Informativo para Motoristas: {noticia['titulo']}",
            "conteudo_html": html_emergencia
        }
