import urllib.request
import xml.etree.ElementTree as ET
import html
import re

def buscar_vagas_motorista():
    print("🌐 Acessando banco de dados de vagas (Feed RSS)...")
    
    # URL do feed de empregos focado em "motorista" no Brasil
    url_feed = "https://br.indeed.com/rss?q=motorista&l="
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url_feed, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        vagas = []
        
        # Varre o XML do feed extraindo as vagas
        for item in root.findall('.//item'):
            titulo = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            descricao_suja = item.find('description').text if item.find('description') is not None else ''
            
            # Limpa tags HTML simples que possam vir na descrição do feed
            descricao = re.sub('<[^<]+?>', '', descricao_suja)
            descricao = html.unescape(descricao)
            
            if titulo and link:
                vagas.append({
                    'titulo': html.unescape(titulo),
                    'link': link,
                    'descricao': descricao.strip()
                })
                
        print(f"📦 Encontradas {len(vagas)} vagas brutas para análise.")
        return vagas

    except Exception as e:
        print(f"❌ Erro ao raspar vagas: {e}")
        # Retorna uma vaga de exemplo para o robô nunca quebrar se o site estiver fora do ar
        return [{
            'titulo': 'Motorista de Caminhão Categoria D',
            'link': 'https://br.indeed.com',
            'descricao': 'Precisa-se de motorista com experiência em rotas estaduais, CNH D ativa e curso MOPP atualizado.'
        }]
