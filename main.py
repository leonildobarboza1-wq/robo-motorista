def main():
    print("🧪 [MODO TESTE FORÇADO] Iniciando injeção direta no Blogger...")
    
    if not BLOG_ID:
        print("❌ [ERRO] Variável BLOG_ID ausente.")
        return

    try:
        blogger = get_blogger_service()
        
        # Criando um payload estático para testar a comunicação com a API
        vaga_teste = {
            "title": "Vaga de Teste Forçado - Motorista - " + datetime.datetime.now().strftime("%H:%M"),
            "description": "Esta é uma postagem de teste para validar se a API do Blogger está recebendo dados.",
            "link": "https://google.com",
            "tipo": "Vaga"
        }
        
        print("🤖 Gerando HTML de teste...")
        html_final = build_final_html("<p>Texto de teste forçado para garantir que o Blogger aceita o robô.</p>", vaga_teste)
        
        print("📤 Enviando diretamente para o Blogger...")
        send_to_blogger(blogger, vaga_teste['title'], html_final)
        
    except Exception as e:
        print(f"💥 ERRO LOCALIZADO: O teste falhou devido a: {e}")

if __name__ == "__main__":
    main()
