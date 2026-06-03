import os
import json
import logging
import urllib.request
import zoneinfo
from datetime import datetime
from filtro_ia import processar_vaga_com_gemini, formatar_noticia_com_gemini

logging.basicConfig(level=logging.INFO)

# --- FUNÇÕES DE CONTROLE ---
# (Mantenha suas funções obter_token_oauth2 e verificar_se_ja_foi_publicado aqui)

def postar_no_blogger(blog_id, access_token, titulo, conteudo):
    # TRAVA DE SEGURANÇA: Se o conteúdo for um erro ou curto demais, não posta.
    if len(conteudo) < 300 or "temporariamente indisponível" in conteudo:
        logging.error(f"Postagem abortada: Conteúdo curto ou com erro. Título: {titulo}")
        return
    
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/?isDraft=false"
    payload = {"kind": "blogger#post", "title": titulo, "content": conteudo}
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), 
                                 headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as response:
        logging.info("Post publicado com sucesso!")

# --- FLUXO PRINCIPAL ---
if __name__ == "__main__":
    blog_id = os.getenv('BLOG_ID')
    access_token = obter_token_oauth2()
    agora = datetime.now(zoneinfo.ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y às %H:%M")
    
    vaga = buscar_vagas_bne()
    if vaga and not verificar_se_ja_foi_publicado(blog_id, access_token, vaga['link'], vaga['titulo']):
        dados = processar_vaga_com_gemini(vaga, agora)
        # SÓ POSTA SE TIVER TÍTULO E CONTEÚDO REAL
        if dados and dados.get('titulo_otimizado') and len(dados.get('conteudo_html', '')) > 300:
            postar_no_blogger(blog_id, access_token, dados['titulo_otimizado'], dados['conteudo_html'])
        else:
            logging.warning("IA retornou dados inválidos, pulando postagem.")
