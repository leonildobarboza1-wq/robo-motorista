import urllib.request
import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.INFO)

def buscar_vagas():
    url = "https://br.indeed.com/rss?q=motorista&l="
    vagas = []
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        logging.info("Acessando o feed RSS...")
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item'):
            titulo = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            descricao = item.find('description').text if item.find('description') is not None else ''
            
            vagas.append({
                'titulo': titulo,
                'link': link,
                'descricao': descricao
            })
        
        logging.info(f"Sucesso: {len(vagas)} vagas encontradas no RSS.")
        
    except Exception as e:
        logging.error(f"Falha ao acessar RSS: {e}. Ativando fallback estático de segurança.")
        # Fallback estático estruturado
        vagas = [{
            'titulo': 'Vaga de Motorista de Caminhão (Categoria D/E) - Simulada',
            'link': 'https://exemplo.com/vaga-fallback',
            'descricao': 'Necessário experiência em rotas interestaduais, CNH E válida e MOPP atualizado. Benefícios: VA, VR e Plano de Saúde.'
        }]
        
    return vagas
