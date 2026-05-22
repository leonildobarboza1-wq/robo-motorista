from google import genai
import os

# CONFIGURAÇÃO: O Python agora pega a chave do "cofre" seguro do GitHub Actions
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")

def analisar_vaga_com_ia(titulo_vaga, descricao_vaga):
    if not GEMINI_API_KEY:
        print("⚠️ ERRO: A chave do Gemini não foi encontrada nas variáveis de ambiente!")
        return None

    # Inicializa o cliente do Gemini
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Criamos o prompt (as ordens que a IA deve seguir estritamente)
    prompt_interno = f"""
    Você é um assistente especializado em recrutamento de motoristas profissionais no Brasil.
    Sua missão é analisar a vaga abaixo e fazer três coisas:
    1. Validar se a vaga é REALMENTE para motorista profissional (Caminhão, Carreta, Ônibus, Van, Carro, Guindaste, Empilhadeira, etc.).
       - REJEITE IMEDIATAMENTE: Entregadores de aplicativo (Ifood, Uber Eats, Rappi), entregadores de bicicleta, motoboys, ajudantes de carga ou vagas onde o foco não seja dirigir.
    2. Descobrir a Cidade e o Estado da vaga lendo o texto. Se não achar, defina como "Brasil".
    3. Se a vaga for válida, reescrever a descrição formatando em HTML simples (use apenas tags como <p>, <strong>, <ul>, <li>). Deixe o texto limpo, corrigindo erros de português e destacando os requisitos (CNH, experiência, etc.).

    Dados da Vaga:
    Título: {titulo_vaga}
    Texto/Descrição: {descricao_vaga}

    Sua resposta deve ser EXATAMENTE no formato abaixo, separando as informações por "|||". Não adicione nenhuma outra palavra fora do formato:
    STATUS ||| CIDADE_ESTADO ||| DESCRICAO_HTML

    Exemplo de resposta para vaga VÁLIDA:
    ACEITA ||| Cuiabá - MT ||| <p>Vaga para motorista de caminhão pesado...</p>

    Exemplo de resposta para vaga INVÁLIDA:
    REJEITADA ||| Ignorar ||| Ignorar
    """

    try:
        # Usamos o modelo 'gemini-2.5-flash' que é super rápido e gratuito
        resposta = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_interno,
        )
        
        texto_ia = resposta.text.strip()
        
        # Separamos os pedaços que a IA mandou usando o "|||"
        partes = texto_ia.split("|||")
        
        if len(partes) >= 3:
            status = partes[0].strip()
            localidade = partes[1].strip()
            html_formatado = partes[2].strip()
            
            if status == "ACEITA":
                return {
                    "valida": True,
                    "localizacao": localidade,
                    "texto_html": html_formatado
                }
                
        return {"valida": False}
        
    except Exception as e:
        print(f"Erro ao conversar com o Gemini: {e}")
        return {"valida": False}

# Bloco de teste rápido
if __name__ == "__main__":
    print("Testando o cérebro do robô com uma vaga falsa...")
    # Teste com uma vaga de Cuiabá que pegamos no Google
    resultado = analisar_vaga_com_ia(
        "Prefeitura de Cuiabá oferta vaga de motorista de caminhão guindaste pesado",
        "Prefeitura de Cuiabá oferta vaga de motorista de caminhão guindaste pesado com munck."
    )
    print("\nResultado do teste da IA:")
    print(resultado)
