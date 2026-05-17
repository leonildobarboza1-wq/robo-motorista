import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

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

def enviar_vaga_para_o_blog(titulo, localizacao, conteudo_html, link_original):
    assunto_post = f"Vaga de Motorista em {localizacao} - {titulo}"
    
    corpo_html = f"""
    <html>
        <body>
            {conteudo_html}
            <br><br>
            <p><strong>Como se candidatar:</strong></p>
            <p><a href="{link_original}" target="_blank" style="display:inline-block;padding:10px 20px;background-color:#007bff;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">Ver Vaga Original e Enviar Currículo</a></p>
            <br>
            <small>Fonte: Buscador Automático Emprego para Motorista</small>
        </body>
    </html>
    """
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_SECRETO_BLOGGER
    msg['Subject'] = assunto_post
    msg.attach(MIMEText(corpo_html, 'html'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        server.sendmail(EMAIL_REMETENTE, EMAIL_SECRETO_BLOGGER, msg.as_string())
        server.quit()
        print(f"✅ Sucesso! Vaga publicada: {titulo} em {localizacao}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail de postagem: {e}")
        return False

def rodar_robo_completo():
    print("=== INICIANDO O ROBÔ EMPREGO PARA MOTORISTA ===")
    
    vagas_brutas = buscar_vagas_motorista()
    
    if not vagas_brutas:
        print("Nenhuma vaga encontrada para processar.")
        return
        
    vagas_publicadas = 0
    # LIMITADOR: Vamos processar no máximo 4 vagas por rodada para não estourar a cota da IA
    maximo_vagas_processar = vagas_brutas[:4]
    
    for vaga in maximo_vagas_processar:
        print(f"\nAguardando intervalo de segurança para a IA...")
        time.sleep(4) # Pausa obrigatória para o Gemini não dar erro 429
        
        print(f"Analisando: {vaga['titulo']}...")
        analise = analisar_vaga_com_ia(vaga['titulo'], vaga['descricao'])
        
        if analise and analise['valida']:
            print(f"-> Aprovada pela IA! Localizado em: {analise['localizacao']}")
            
            postou = enviar_vaga_para_o_blog(
                titulo=vaga['titulo'],
                localizacao=analise['localizacao'],
                conteudo_html=analise['texto_html'],
                link_original=vaga['link']
            )
            
            if postou:
                vagas_publicadas += 1
                time.sleep(3)
        else:
            print("-> Reprovada ou descartada pela IA.")
            
    print(f"\n=== PROCESSO CONCLUÍDO: {vagas_publicadas} vagas novas no seu Portal! ===")

if __name__ == "__main__":
    rodar_robo_completo()
