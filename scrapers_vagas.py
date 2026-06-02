import urllib.request
import xml.etree.ElementTree as ET
import json
import logging
import re

logging.basicConfig(level=logging.INFO)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def limpar_html(texto):
    """Remove tags HTML residuais das descrições dos feeds"""
    if not texto: return ""
    return re.sub(r'<[^>]+>', '', texto).strip()

def buscar_indeed():
    """Fonte 1: Indeed Brasil (Via Feed RSS)"""
    url = "https://br.indeed.com/rss?q=motorista&l="
    vagas = []
    try:
        logging.info("Buscando vagas no Indeed...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
            
        for item in root.findall('.//item'):
            vagas.append({
                'titulo': item.find('title').text if item.find('title') is not None else '',
                'link': item.find('link').text if item.find('link') is not None else '',
                'descricao': limpar_html(item.find('description').text) if item.find('description') is not None else '',
                'fonte': 'Indeed'
            })
    except Exception as e:
        logging.error(f"Erro ao buscar no Indeed: {e}")
    return vagas

def buscar_simplyhired():
    """Fonte 2: SimplyHired Brasil (Via Agregador Atom/RSS)"""
    # Nota: SimplyHired utiliza uma estrutura similar ao Indeed por fazerem parte do mesmo grupo
    url = "https://www.simplyhired.com.br/a/jobs/rss/q-motorista"
    vagas = []
    try:
        logging.info("Buscando vagas no SimplyHired...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
            
        for item in root.findall('.//item'):
            vagas.append({
                'titulo': item.find('title').text if item.find('title') is not None else '',
                'link': item.find('link').text if item.find('link') is not None else '',
                'descricao': limpar_html(item.find('description').text) if item.find('description') is not None else '',
                'fonte': 'SimplyHired'
            })
    except Exception as e:
        logging.error(f"Erro ao buscar no SimplyHired: {e}")
    return vagas

def buscar_jooble():
    """Fonte 3: Jooble Brasil (Feed de Empregos Aberto)"""
    url = "https://br.jooble.org/rss/feed/keyword-motorista"
    vagas = []
    try:
        logging.info("Buscando vagas no Jooble...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            root = ET.fromstring(response.read())
            
        for item in root.findall('.//item'):
            vagas.append({
                'titulo': item.find('title').text if item.find('title') is not None else '',
                'link': item.find('link').text if item.find('link') is not None else '',
                'descricao': limpar_html(item.find('description').text) if item.find('description') is not None else '',
                'fonte': 'Jooble'
            })
    except Exception as e:
        logging.error(f"Erro ao buscar no Jooble: {e}")
    return vagas

def buscar_trabalhabrasil():
    """Fonte 4: Trabalha Brasil (Antigo SINE - API Pública/Agregador)"""
    # Usando o endpoint de paginação simplificada que eles expõem publicamente
    url = "https://api.trabalhabrasil.com.br/api/v1/vagas?pesquisa=motorista&pagina=1&quantidade=10"
    vagas = []
    try:
        logging.info("Buscando vagas no Trabalha Brasil...")
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as response:
            dados = json.loads(response.read().decode('utf-8'))
            
        # Mapeia o JSON deles para o nosso padrão de dicionário
        for vaga in dados.get('vagas', []):
            vagas.append({
                'titulo': vaga.get('funcao', 'Vaga de Motorista'),
                'link': f"https://www.trabalhabrasil.com.br/vagas-empregos/{vaga.get('urlVaga', '')}",
                'descricao': f"Vaga em {vaga.get('cidade', '')} - {vaga.get('uf', '')}. Descrição: {vaga.get('descricao', '')}",
                'fonte': 'Trabalha Brasil'
            })
    except Exception as e:
        logging.error(f"Erro ao buscar no Trabalha Brasil: {e}")
    return vagas
