import os
import json
import logging
import urllib.request

logging.basicConfig(level=logging.INFO)

def chamar_api_gemini_texto_puro(prompt):
    """Faz a requisição ao Gemini esperando texto/HTML livre, sem travas de JSON"""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não encontrada no ambiente.")
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    
    with urllib.request.urlopen(req, timeout=40) as response:
        resultado = json.loads(response.read().decode('utf-8'))
        texto_resposta = resultado['candidates'][0]['content']['parts'][0]['text']
        return texto_resposta.strip()

def processar_vaga_com_gemini(vaga, data_postagem):
    prompt = f"""
    Você é um redator profissional especializado no setor de transportes e logística.
    Crie um artigo de divulgação de vaga longo, explicativo e atraente.

    REGRAS DE CONTEÚDO (ANTI-PLÁGIO):
    1. O texto final DEVE ter no mínimo 20 linhas de parágrafos bem desenvolvidos.
    2. Mesmo que a descrição original seja curta, EXPANDA o conteúdo. Fale sobre a importância da região, a relevância do motorista para a economia, os desafios e as boas práticas da profissão.
    3. NÃO use palavras do texto original para evitar conteúdo duplicado.

    REGRAS DE FORMATAÇÃO:
    - Escreva a resposta DIRETAMENTE em HTML (use <p>, <strong>, <ul>, <li>).
    - NÃO use blocos de código com ```html. Comece direto no texto.
    - Na PRIMEIRA linha do texto, inclua: <p><strong>📅 Publicado em: {data_postagem}</strong></p>
    - No FINAL do texto, coloque o link: <p>Para se candidatar, acesse o link oficial: <a href='{vaga['link']}' target='_blank'>Clique aqui para ir ao site {vaga['fonte']}</a>.</p>

    Dados da Vaga Original:
    Título: {vaga['titulo']}
    Descrição: {vaga['descricao']}
    Fonte: {vaga['fonte']}
    """
    try:
        conteudo_html = chamar_api_gemini_texto_puro(prompt)
        
        # Limpeza segura na mesma linha para evitar SyntaxError
        conteudo_html = conteudo_html.replace("```html", "").replace("```", "").strip()
        
        return {
            "e_motorista": True, 
            "titulo_otimizado": f"Vaga de Motorista: Oportunidade para Profissional em {vaga['titulo']}", 
            "conteudo_html": conteudo_html
        }
    except Exception as e:
        logging.error(f"Erro no processamento da vaga: {e}")
        return {"e_motorista": False, "titulo_otimizado": "", "conteudo_html": ""}

def formatar_noticia_com_gemini(noticia, data_postagem):
    prompt = f"""
    Você é um jornalista focado em estradas e transporte rodoviário de cargas.
    Sua missão é ler a notícia curta abaixo e escrever um artigo jornalístico completo, profundo e 100% INÉDITO.

    REGRAS DE CONTEÚDO (ANTI-PLÁGIO):
    1. O artigo DEVE ter no mínimo 20 linhas de puro texto descritivo. 
    2. Se a notícia base for curta, contextualize! Explique o que é o evento (ex: Operação Corpus Christi), o impacto disso nas rodovias, traga dicas de segurança para o motorista evitar multas e como planejar a viagem.
    3. Mude totalmente as palavras. Crie uma redação do zero baseada no fato.

    REGRAS DE FORMATAÇÃO:
    - Escreva a resposta DIRETAMENTE em HTML (use <p>, <strong>, <ul>, <li>).
    - NÃO use blocos de código com ```html. Comece direto no texto.
    - A PRIMEIRA linha do texto DEVE ser: <p><strong>📅 Publicado em: {data_postagem}</strong></p>
    - O título do post DEVE vir na primeira linha do seu texto dentro de uma tag especial de comentário formatada exatamente assim: Notícia Base:
    Título: {noticia['titulo']}
    Conteúdo: {noticia['descricao']}
    Fonte: {noticia['fonte_original']}
    """
    try:
        logging.info("Enviando conteúdo para reescrita longa e livre de amarras...")
        conteudo_html = chamar_api_gemini_texto_puro(prompt)
        
        # Limpeza segura na mesma linha para evitar SyntaxError
        conteudo_html = conteudo_html.replace("```html", "").replace("```", "").strip()
        
        titulo_otimizado = f"Informativo para Motoristas: {noticia['titulo']}"
        if "")[0].strip()
                if titulo_extraido:
                    titulo_otimizado = titulo_extraido
            except:
                pass
                
        return {
            "titulo_otimizado": titulo_otimizado,
            "conteudo_html": conteudo_html
        }
    except Exception as e:
        logging.error(f"Erro no processamento da notícia pelo Gemini: {e}")
        return {
            "titulo_otimizado": f"Informativo para Motoristas: {noticia['titulo']}",
            "conteudo_html": f"<p><strong>📅 Publicado em: {data_postagem}</strong></p><p>{noticia['descricao']}</p><p>Confira na fonte: <a href='{noticia['link']}'>{noticia['fonte_original']}</a>.</p>"
        }
