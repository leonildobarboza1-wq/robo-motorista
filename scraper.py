import requests
from bs4 import BeautifulSoup
import urllib.parse

def buscar_vagas_motorista():
    # Termo de busca que o Google vai varrer na internet inteira do Brasil
    termo = '"vaga de motorista"'
    termo_encodado = urllib.parse.quote(termo)
    
    # URL oficial do Feed do Google News configurado para o Brasil (gl=BR, hl=pt-BR)
    url = f"https://news.google.com/rss/search?q={termo_encodado}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    print(f"Buscando vagas recentes através do servidor do Google...")
    
    try:
        resposta = requests.get(url, headers=headers, timeout=15)
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return []
        
    if resposta.status_code != 200:
        print(f"Erro ao acessar o Google. Status: {resposta.status_code}")
        return []
        
    # Lendo o XML que o Google nos enviou
    soup = BeautifulSoup(resposta.text, 'xml')
    itens = soup.find_all('item')
    
    print(f"Foram encontradas {len(itens)} publicações recentes no Google.")
    
    lista_de_vagas = []
    
    for item in itens:
        try:
            titulo_completo = item.find('title').text.strip() if item.find('title') else "Vaga de Motorista"
            link_original = item.find('link').text.strip() if item.find('link') else ""
            
            # O Google News costuma colocar a fonte no final do título separado por "-"
            # Exemplo: "Vaga para Motorista Categoria D - Empresa XPTO"
            # Vamos separar para ficar mais limpo
            if " - " in titulo_completo:
                partes = titulo_completo.rsplit(" - ", 1)
                titulo = partes[0]
                empresa = partes[1]
            else:
                titulo = titulo_completo
                empresa = "Fonte da Internet"
                
            # Descrição rápida da publicação
            descricao = item.find('description').text.strip() if item.find('description') else ""
            # Limpa qualquer tag HTML que venha junto
            descricao_limpa = BeautifulSoup(descricao, "html.parser").get_text()
            
            dados_vaga = {
                "titulo": titulo,
                "empresa": empresa,
                "localizacao": "Brasil", # O Gemini vai ajustar isso lendo o texto na Etapa 3
                "descricao": descricao_limpa,
                "link": link_original
            }
            
            lista_de_vagas.append(dados_vaga)
            
        except Exception as e:
            continue
            
    return lista_de_vagas

if __name__ == "__main__":
    resultado = buscar_vagas_motorista()
    print("\n--- TESTE DE EXTRAÇÃO GOOGLE ---")
    for i, v in enumerate(resultado[:5], 1): # Mostra as 5 primeiras na tela
        print(f"\nVaga {i}:")
        print(f"Título: {v['titulo']}")
        print(f"Fonte/Empresa: {v['empresa']}")
        print(f"Descrição: {v['descricao'][:120]}...")
        print(f"Link Original: {v['link']}")