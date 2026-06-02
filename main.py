def obter_ultimos_titulos_blogger(blog_id, access_token):
    """Busca os títulos das últimas postagens do blog para evitar duplicidade"""
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?maxResults=10&fetchBodies=false"
    headers = {'Authorization': f'Bearer {access_token}'}
    req = urllib.request.Request(url, headers=headers, method='GET')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            items = res_data.get('items', [])
            return [item['title'].split(" - Atualizado em")[0].strip() for item in items]
    except Exception as e:
        logging.warning(f"Não foi possível buscar posts antigos do Blogger para comparar: {e}")
        return []

def main():
    blog_id = os.getenv('BLOG_ID')
    api_key_gemini = os.getenv('GOOGLE_API_KEY')
    client_id = os.getenv('BLOGGER_CLIENT_ID')
    client_secret = os.getenv('BLOGGER_CLIENT_SECRET')
    refresh_token = os.getenv('BLOGGER_REFRESH_TOKEN')
    
    if not all([blog_id, api_key_gemini, client_id, client_secret, refresh_token]):
        logging.error("ERRO CRÍTICO: Chaves ou Secrets faltando no ambiente.")
        sys.exit(1)
        
    # 1. Autenticação antecipada para podermos ler o histórico do blog
    try:
        logging.info("Gerando token de acesso OAuth2...")
        access_token = obter_access_token(client_id, client_secret, refresh_token)
    except Exception as e:
        sys.exit(1)
        
    # Busca títulos já publicados para usar como filtro anti-duplicação
    titulos_existentes = obter_ultimos_titulos_blogger(blog_id, access_token)
    logging.info(f"Últimos títulos identificados no blog: {titulos_existentes}")

    # 2. Coleta das vagas do RSS
    vagas = buscar_vagas()
    if not vagas:
        logging.warning("Nenhuma vaga encontrada no RSS para processar.")
        return
        
    # Procurar no feed do RSS a primeira vaga que ainda NÃO foi publicada
    vaga_alvo = None
    for v in vagas:
        # Simplifica o título do RSS para comparar (removendo espaços extras)
        titulo_rss_limpo = v['titulo'].strip()
        
        # Verifica se algum post recente no blog contém o título que está no RSS
        ja_existe = any(titulo_rss_limpo in t or t in titulo_rss_limpo for t in titulos_existentes)
        
        if not ja_existe:
            vaga_alvo = v
            break
            
    if not vaga_alvo:
        logging.warning("⚠️ Todas as vagas retornadas pelo RSS já foram publicadas recentemente no blog. Pulando execução para evitar duplicação.")
        return

    # 3. Filtragem e formatação com o Gemini (Apenas se a vaga for inédita!)
    logging.info(f"Processando vaga inédita encontrada: {vaga_alvo['titulo']}")
    dados_vaga = processar_vaga_com_gemini(vaga_alvo, api_key_gemini)
    
    if not dados_vaga.get('e_motorista'):
        logging.warning("A vaga analisada não passou no filtro do Gemini para Motoristas.")
        return
        
    # 4. Preparação dos dados e carimbo de data/hora
    fuso_br = zoneinfo.ZoneInfo("America/Sao_Paulo")
    agora = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M")
    
    # O carimbo no final do título garante que a URL gerada pelo Blogger seja única
    titulo_final = f"{dados_vaga['titulo_otimizado']} - Atualizado em {agora}"
    conteudo_final = f"""
    {dados_vaga['conteudo_html']}
    <br><hr>
    <p><small><i>Post automatizado gerado em: {agora} (Horário de Brasília)</i></small></p>
    """
    
    # 5. Publicação final
    try:
        logging.info("Enviando postagem inédita para o Blogger...")
        postar_no_blogger(blog_id, access_token, titulo_final, conteudo_final)
    except Exception as erro_final:
        logging.error(f"Execução falhou na etapa de publicação: {erro_final}")
        sys.exit(1)

if __name__ == '__main__':
    main()
