import os
import sys
import logging
from datetime import datetime
import zoneinfo

# Importação dos seus módulos coletores
from scrapers_vagas import buscar_indeed, buscar_simplyhired, buscar_jooble, buscar_trabalhabrasil
from scrapers_noticias import buscar_noticia_caminhoneiro
from filtro_ia import processar_vaga_com_gemini, formatar_noticia_com_gemini
from blogger_api import obter_access_token, obter_ultimos_titulos_blogger, postar_no_blogger

logging.basicConfig(level=logging.INFO)

def main():
    # 1. Autenticação e Verificação do Histórico do Blog
    blog_id = os.getenv('BLOG_ID')
    access_token = obter_access_token(
        os.getenv('BLOGGER_CLIENT_ID'), 
        os.getenv('BLOGGER_CLIENT_SECRET'), 
        os.getenv('BLOGGER_REFRESH_TOKEN')
    )
    
    titulos_publicados = obter_ultimos_titulos_blogger(blog_id, access_token)
    
    # 2. Rotação de Sites de Vagas (Ordem de Prioridade)
    lista_fontes_vagas = [buscar_indeed, buscar_simplyhired, buscar_jooble, buscar_trabalhabrasil]
    vaga_selecionada = None
    
    logging.info("Iniciando busca por vagas inéditas...")
    for buscar_fonte in lista_fontes_vagas:
        vagas = buscar_fonte()
        
        # Procura uma vaga que ainda não exista nos últimos títulos do blog
        for v in vagas:
            if v['titulo'].strip() not in titulos_publicados:
                vaga_selecionada = v
                break
        
        if vaga_selecionada:
            logging.info(f"Sucesso! Vaga inédita encontrada na fonte: {buscar_fonte.__name__}")
            break
        else:
            logging.warning(f"Nenhuma vaga nova nas últimas 24h na fonte {buscar_fonte.__name__}. Pulando para a próxima...")

    # 3. Processamento do Conteúdo (Vaga VS Notícia de Reserva)
    fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
    
    if vaga_selecionada:
        # Cenário A: Encontrou vaga -> Processa com Gemini para validar e limpar
        dados = processar_vaga_com_gemini(vaga_selecionada, os.getenv('GOOGLE_API_KEY'))
        if dados.get('e_motorista'):
            titulo_final = f"{dados['titulo_otimizado']} - Vaga Aberta"
            conteudo_final = dados['conteudo_html']
        else:
            vaga_selecionada = None # Reseta se a IA rejeitar os dados
            
    # Se não encontrou vaga OU se a IA rejeitou o formato da vaga capturada
    if not vaga_selecionada:
        logging.warning("🚨 Alerta: Nenhuma vaga inédita encontrada em nenhum site. Ativando reserva de notícias!")
        
        # Busca notícia nos portais de reserva
        noticia = buscar_noticia_caminhoneiro()
        dados_noticia = formatar_noticia_com_gemini(noticia, os.getenv('GOOGLE_API_KEY'))
        
        titulo_final = f"Informativo: {dados_noticia['titulo_otimizado']}"
        conteudo_final = dados_noticia['conteudo_html']

    # 4. Publicação Final Garantida
    conteudo_final += f"<br><hr><p><small>Atualizado em: {agora}</small></p>"
    postar_no_blogger(blog_id, access_token, titulo_final, conteudo_final)
    logging.info("Execução diária concluída com sucesso!")

if __name__ == '__main__':
    main()
