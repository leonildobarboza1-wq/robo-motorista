import os
import json
import logging
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)

def configurar_gemini(api_key):
    """Inicializa e configura a API do Gemini"""
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não configurada no ambiente do GitHub.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def processar_vaga_com_gemini(vaga, api_key):
    """
    Analisa a vaga capturada, valida se é de motorista
    e gera uma formatação HTML profissional.
    """
    model = configurar_gemini(api_key)
    
    prompt = f"""
    Você é um recrutador especialista no setor de transportes e logística no Brasil.
    Analise os dados abaixo e identifique se a vaga é REALMENTE para motoristas profissionais (caminhão, ônibus, carreta, entregas, etc.).
    Se NÃO for uma vaga de motorista, retorne a chave "e_motorista" como false.
    Se FOR, extraia os dados e formate o corpo em HTML limpo.

    Dados da vaga:
    Título original: {vaga['titulo']}
    Descrição original: {vaga['descricao']}
    Link original: {vaga['link']}
    Fonte: {vaga['fonte']}

    Sua resposta deve ser estritamente um JSON com a seguinte estrutura (sem blocos de código markdown como ```json):
    {{
        "e_motorista": true,
        "titulo_otimizado": "Título da Vaga Otimizado para SEO (Ex: Motorista de Caminhão Carreta - São Paulo/SP)",
        "conteudo_html": "<p>Insira uma introdução chamando o candidato.</p><strong>Requisitos:</strong><ul><li>Item</li></ul><strong>Benefícios:</strong><ul><li>Item</li></ul><p>Para se candidatar, <a href='{vaga['link']}' target='_blank'>clique aqui para acessar a vaga original no {vaga['fonte']}</a>.</p>"
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text.strip())
    except Exception as e:
        logging.error(f"Erro ao processar vaga no Gemini: {e}")
        return {"e_motorista": False, "titulo_otimizado": "", "conteudo_html": ""}


def formatar_noticia_com_gemini(noticia, api_key):
    """
    Lê uma notícia bruta capturada dos portais e reescreve
    em formato de artigo informativo amigável e otimizado para SEO.
    """
    model = configurar_gemini(api_key)
    
    prompt = f"""
    Você é um jornalista especializado no setor de transportes rodoviários de cargas e passageiros no Brasil.
    Sua missão é pegar a notícia bruta abaixo e reescrevê-la em um formato de artigo curto, dinâmico e muito atraente para motoristas e caminhoneiros que acessam o nosso blog de empregos.

    Notícia Bruta:
    Título: {noticia['titulo']}
    Conteúdo extraído: {noticia['descricao']}
    Fonte original: {noticia['fonte_original']}

    Diretrizes do Artigo:
    - O tom deve ser informativo, amigável e focado no dia a dia das estradas.
    - Organize o texto usando parágrafos curtos (<p>) e intertítulos com a tag <strong>.
    - No final do texto, inclua obrigatoriamente um link referenciando o portal original.

    Sua resposta deve ser estritamente um JSON com a seguinte estrutura (sem blocos de código markdown como ```json):
    {{
        "titulo_otimizado": "Título impactante focado em SEO para o Blog de Caminhoneiros",
        "conteudo_html": "<p>Parágrafo inicial engajador explicando a novidade...</p><strong>Destaques da notícia:</strong><p>Mais detalhes importantes...</p><p>Fique por dentro de mais detalhes lendo a matéria completa no <a href='{noticia['link']}' target='_blank'>{noticia['fonte_original']}</a>.</p>"
    }}
    """
    
    try:
        logging.info("Enviando notícia reserva para formatação no Gemini...")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text.strip())
    except Exception as e:
        logging.error(f"Erro ao reescrever notícia no Gemini: {e}")
        # Fallback estruturado caso a IA falhe em responder o JSON
        return {
            "titulo_otimizado": noticia['titulo'],
            "conteudo_html": f"<p>{noticia['descricao']}</p><p>Confira a matéria completa na fonte oficial: <a href='{noticia['link']}'>{noticia['fonte_original']}</a>.</p>"
        }
