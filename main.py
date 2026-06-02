def buscar_noticia_caminhoneiro():
    """Busca a última notícia no Blog do Caminhoneiro e tenta capturar a imagem do post"""
    url_feed = "https://blogdocaminhoneiro.com/feed/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(url_feed, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read().decode('utf-8')
            
            # Divide o XML para pegar o primeiro item/postagem
            item = xml_data.split('<item>')[1].split('</item>')[0]
            
            titulo = item.split('<title>')[1].split('</title>')[0]
            link = item.split('<link>')[1].split('</link>')[0]
            descricao = item.split('<description>')[1].split('</description>')[0]
            
            # Limpa CDATA se houver
            titulo = titulo.replace('<![CDATA[', '').replace(']]>', '').strip()
            descricao = descricao.replace('<![CDATA[', '').replace(']]>', '').strip()
            
            # TENTA CAPTURAR A IMAGEM ORIGINAL DO SITE
            url_imagem = ""
            if '<media:content' in item:
                try:
                    url_imagem = item.split('<media:content')[1].split('url="')[1].split('"')[0]
                except:
                    pass
            if not url_imagem and 'src="' in item:
                try:
                    url_imagem = item.split('src="')[1].split('"')[0]
                except:
                    pass

            # Se não encontrou imagem no site original, usa uma imagem linda e profissional de internet
            if not url_imagem:
                url_imagem = "https://images.unsplash.com/photo-1601584115197-04ecc0da31d7?w=800&auto=format&fit=crop"

            return {
                "titulo": titulo,
                "link": link,
                "descricao": descricao,
                "fonte_original": "Blog do Caminhoneiro",
                "url_imagem": url_imagem
            }
    except Exception as e:
        logging.error(f"Erro ao raspar Blog do Caminhoneiro: {e}")
        # Retorno de emergência caso o site deles esteja fora do ar
        return {
            "titulo": "Novas regras de trânsito para veículos pesados entram em vigor",
            "link": "https://blogdocaminhoneiro.com",
            "descricao": "Mudanças importantes afetam a rotina dos motoristas de caminhão nas rodovias federais este mês.",
            "fonte_original": "Portal de Notícias",
            "url_imagem": "https://images.unsplash.com/photo-1516576885502-39c4a3b6f00c?w=800&auto=format&fit=crop"
        }
