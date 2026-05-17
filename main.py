import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import requests
from bs4 import BeautifulSoup

# Importando as funções que criamos nas etapas anteriores
from scraper import buscar_vagas_motorista
from filtro_ia import analisar_vaga_com_ia

# ==================== CONFIGURAÇÕES OBRIGATÓRIAS ====================
EMAIL_SECRETO_BLOGGER = "leonildobarboza2.motorista2026@blogger.com"
EMAIL_REMETENTE = "leonildobarboza2@gmail.com"
SENHA_REMETENTE = "cztd izxz hjze xccm"

# Servidor oficial do Gmail
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
# ====================================================================

def enviar_para_o_blog(assunto, conteudo_html):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_SECRETO_BLOGGER
    msg['Subject'] = assunto
    msg.attach(MIMEText(conteudo_html, 'html'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        server.sendmail(EMAIL_REMETENTE, EMAIL_SECRETO_BLOGGER, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail de postagem: {e}")
        return False

def buscar_e_postar_noticia_automatico():
    print("\n=== BUSCANDO NOTÍCIAS NO BLOG DO CAMINHONEIRO ===")
    url_feed = "https://blogdocaminhoneiro.com/feed/"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resposta = requests.get(url_feed, headers=headers)
        soup = BeautifulSoup(resposta.text, 'lxml-xml') # Usando o lxml que consertamos!
        
        # Pega a notícia mais recente
        item = soup.find('item')
        if item:
            titulo = item.find('title').text
            link = item.find('link').text
            # O Blogger precisa do marcador [Notícias] no assunto para organizar o menu
            assunto_noticia = f"[Notícias] {titulo}"
            
            # Limpa e pega a descrição da notícia
            descricao = item.find('description').text if item.find('description') else "Clique no botão abaixo para ler a matéria completa."
            if "<![CDATA[" in descricao:
                descricao = descricao.replace("<![CDATA[", "").replace("]]>", "")
            
            corpo_html = f"""
            <html>
                <body>
                    <p>{descricao}</p>
                    <br><br>
                    <p><strong>Quer ler a matéria completa?</strong></p>
                    <p><a href="{link}" target="_blank" style="display:inline-block;padding:10px 20px;background-color:#ff4500;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">Ler Notícia Completa no Blog do Caminhoneiro</a></p>
                    <br>
                    <small>Fonte: Parceria Automática com Blog do Caminhoneiro</small>
                </body>
            </html>
            """
            
            print(f"Encontrada notícia: {titulo}")
            postou = enviar_para_o_blog(assunto_noticia, corpo_html)
            if postou:
                print("✅ Sucesso! Notícia publicada no portal.")
            else:
                print("❌ Falha ao publicar notícia.")
        else:
            print("Nenhuma notícia encontrada no Feed.")
            
    except Exception as e:
        print(f"❌ Erro ao processar notícias: {e}")

def rodar_robo_completo():
    print("=== INICIANDO O ROBÔ EMPREGO PARA MOTORISTA ===")
    
    # 1. PARTE DE VAGAS (Continua funcionando exatamente igual)
    vagas_brutas = buscar_vagas_motorista()
    if not vagas_brutas:
        print("Nenhuma vaga encontrada para processar.")
    else:
        vagas_publicadas = 0
        maximo_vagas_processar = vagas_brutas[:4]
        
        for vaga in maximo_vagas_processar:
            print(f"\nAguardando intervalo de segurança para a IA...")
            time.sleep(4)
            print(f"Analisando: {vaga['titulo']}...")
            analise = analisar_vaga_com_ia(vaga['titulo'], vaga['descricao'])
            
            if analise and analise['valida']:
                print(f"-> Aprovada pela IA! Localizado em: {analise['localizacao']}")
                
                assunto_vaga = f"Vaga de Motorista em {analise['localizacao']} - {vaga['titulo']}"
                conteudo_vaga_html = f"""
                <html>
                    <body>
                        {analise['texto_html']}
                        <br><br>
                        <p><strong>Como se candidatar:</strong></p>
                        <p><a href="{vaga['link']}" target="_blank" style="display:inline-block;padding:10px 20px;background-color:#007bff;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">Ver Vaga Original e Enviar Currículo</a></p>
                        <br>
                        <small>Fonte: Buscador Automático Emprego para Motorista</small>
                    </body>
                </html>
                """
                
                postou = enviar_para_o_blog(assunto_vaga, conteudo_vaga_html)
                if postou:
                    print(f"✅ Sucesso! Vaga publicada: {vaga['titulo']}")
                    vagas_publicadas += 1
                    time.sleep(3)
            else:
                print("-> Reprovada ou descartada pela IA.")
        print(f"\n=== PROCESSO DE VAGAS CONCLUÍDO: {vagas_publicadas} vagas novas! ===")
    
    # 2. PARTE DE NOTÍCIAS (A nova engrenagem automática)
    buscar_e_postar_noticia_automatico()
    
    print("\n=== TODO O PROCESSO FOI CONCLUÍDO COM SUCESSO! ===")

if __name__ == "__main__":
    rodar_robo_completo()
