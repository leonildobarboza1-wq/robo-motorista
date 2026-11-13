import urllib.request
import xml.etree.ElementTree as ET
import logging
import re

logging.basicConfig(level=logging.INFO)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8'
}

def limpar_html_noticia(texto):
    """Remove tags HTML e sujeiras do texto para entregar limpo ao Gemini."""
    if not texto:
        return ""
    texto_limpo = re.sub(r'<[^>]+>', '', texto)
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
            logging.info(f"Tentando buscar notícia no portal: {fonte['nome']}...")
            req = urllib.request.Request(fonte['url'], headers=HEADERS)

            with urllib.request.urlopen(req, timeout=15) as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)
            itens = root.findall('.//item')

            for item in itens[:3]:
                titulo_node = item.find('title')
                link_node = item.find('link')
                desc_node = item.find('description')

                titulo = titulo_node.text.strip() if (titulo_node is not None and titulo_node.text) else ''
                link = link_node.text.strip() if (link_node is not None and link_node.text) else ''
                descricao = desc_node.text if (desc_node is not None and desc_node.text) else ''

                if titulo and link:
                    logging.info(f"Sucesso! Notícia capturada de {fonte['nome']}: {titulo[:40]}...")
                    return {
                        'titulo': titulo,
                        'link': link,
                        'descricao': limpar_html_noticia(descricao),
                        'fonte_original': fonte['nome']
                    }

        except Exception as e:
            logging.error(f"Falha ao ler o feed do {fonte['nome']}: {e}. Tentando próxima fonte...")

    logging.warning("Todas as fontes de notícias falharam. Usando fallback informativo estático.")
    return {
        'titulo': 'Cuidados essenciais com a manutenção do caminhão antes de pegar a estrada',
        'link': 'https://blogdocaminhoneiro.com',
        'descricao': 'Fazer a checagem dos freios, óleo do motor, suspensão e calibração dos pneus evita acidentes e garante uma viagem muito mais segura para os motoristas profissionais pelas rodovias do Brasil.',
        'fonte_original': 'Sistema Interno'
    }
