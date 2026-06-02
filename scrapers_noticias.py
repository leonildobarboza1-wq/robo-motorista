import urllib.request
import xml.etree.ElementTree as ET
import logging
import re

logging.basicConfig(level=logging.INFO)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def limpar_html_noticia(texto):
    """Remove tags HTML e sujeiras do texto para entregar limpo ao Gemini"""
    if not texto: return ""
    # Remove tags HTML
    texto_limpo = re.sub(r'<[^>]+>', '', texto)
    # Remove espaços duplos e quebras de linha excessivas
    return " ".join(texto_limpo.split()).strip()

def buscar_noticia_caminhoneiro():
    """
    Varre os 3 portais de notícias em ordem. 
    Retorna a primeira notícia válida que encontrar.
    """
    fontes = [
        {"nome": "Blog do Caminhoneiro", "url": "https://blogdocaminhoneiro.com/feed/"},
        {"nome": "Revista Caminhoneiro", "url": "https://revistacaminhoneiro.com.br/feed/"},
        {"nome": "Estradas.com.br", "url": "https://estradas.com.br/feed/"}
    ]
    
    for fonte in fontes:
        try:
            logging.info(f"Tentando buscar notícia reserva no portal: {fonte['nome']}...")
            req = urllib.request.Request(fonte['url'], headers=HEADERS)
            
            with urllib.request.urlopen(req, timeout=12) as response:
                xml_data = response.read()
                
            root = ET.fromstring(xml_data)
            item = root.find('.//item') # Pega a notícia mais recente do topo (posição 0)
            
            if item is not None:
                titulo = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                
                # Alguns feeds usan 'description', outros usam o 'encoded' do content.
                # Tentamos pegar o que tiver mais texto descritivo.
                descricao = ""
                desc_node = item.find('description')
                if desc_node is not None and desc_node.text:
                    descricao = desc_node.text
                    
                logging.info(f"Sucesso! Notícia capturada de {fonte['nome']}: {titulo[:40]}...")
                
                return {
                    'titulo': titulo.strip(),
                    'link': link.strip(),
                    'descricao': limpar_html_noticia(descricao),
                    'fonte_original': fonte['nome']
                }
                
        except Exception as e:
            logging.error(f"Falha ao ler o feed do {fonte['nome']}: {e}. Tentando próxima fonte de notícias...")
            
    # Fallback crítico se a internet inteira cair (Garante que o robô nunca quebre)
    logging.warning("⚠️ Todas as fontes de notícias falharam. Usando fallback informativo estático.")
    return {
        'titulo': 'Cuidados essenciais com a manutenção do caminhão antes de pegar a estrada',
        'link': 'https://blogdocaminhoneiro.com',
        'descricao': 'Fazer a checagem dos freios, óleo do motor, suspensão e calibração dos pneus evita acidentes e garante uma viagem muito mais segura para os motoristas profissionais pelas rodovias do Brasil.',
        'fonte_original': 'Sistema Interno'
    }
