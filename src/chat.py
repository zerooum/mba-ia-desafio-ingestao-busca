import questionary
from questionary import Style
from search import search_prompt

# Estilo customizado para a CLI
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),       # Token do marcador de pergunta
    ('question', 'bold'),                # Texto da pergunta
    ('answer', 'fg:#f44336 bold'),       # Resposta selecionada
    ('pointer', 'fg:#673ab7 bold'),      # Ponteiro de seleção
    ('highlighted', 'fg:#673ab7 bold'),  # Opção destacada
    ('selected', 'fg:#cc5454'),          # Opção selecionada
    ('separator', 'fg:#cc5454'),         # Separador
    ('instruction', ''),                 # Instruções do usuário
    ('text', ''),                        # Texto plano
])

def main():
    print("=" * 60)
    print("🔍 BEM-VINDO À CLI DE BUSCA DE EMPRESAS")
    print("=" * 60)
    print()
    
    while True:
        # Escolher tipo de busca
        search_choice = questionary.select(
            "Escolha o tipo de busca:",
            choices=[
                {
                    "name": "🧠 Self Query Retriever (busca inteligente com filtros)",
                    "value": "self_query"
                },
                {
                    "name": "🔎 Similarity Search (busca por similaridade pura)",
                    "value": "similarity"
                },
                {
                    "name": "❌ Sair",
                    "value": "exit"
                }
            ],
            style=custom_style
        ).ask()
        
        if search_choice is None or search_choice == "exit":
            print("\n👋 Encerrando a CLI. Até logo!")
            break
        
        use_self_query = (search_choice == "self_query")
        
        # Receber pergunta do usuário
        question = questionary.text(
            "Digite sua pergunta:",
            validate=lambda text: True if len(text) > 0 else "A pergunta não pode estar vazia!",
            style=custom_style
        ).ask()
        
        if question is None:  # Usuário cancelou (Ctrl+C)
            continue
        
        # Processar pergunta
        print("\n🔍 Processando sua pergunta...\n")
        
        try:
            resp = search_prompt(question, use_self_query)
            
            if not resp:
                print("❌ Não foi possível obter uma resposta. Tente novamente.\n")
                continue
            
            # Exibir resposta
            print("─" * 60)
            print("✨ RESPOSTA:")
            print("─" * 60)
            print(resp["answer"])
            print("─" * 60)
            print()
            
            # Perguntar se deseja ver o contexto
            show_context = questionary.confirm(
                "Deseja ver os documentos de contexto?",
                default=False,
                style=custom_style
            ).ask()
            
            if show_context:
                print("\n" + "=" * 60)
                print("📄 DOCUMENTOS DE CONTEXTO:")
                print("=" * 60)
                for i, doc in enumerate(resp["context"], 1):
                    print(f"\n📌 Documento {i}:")
                    print(f"Conteúdo: {doc.page_content[:200]}...")
                    print(f"Metadata: {doc.metadata}")
                print("=" * 60)
            
            print()
            
        except Exception as e:
            print(f"\n❌ Erro ao processar a pergunta: {str(e)}\n")
        
        # Perguntar se deseja fazer outra pergunta
        another = questionary.confirm(
            "Deseja fazer outra pergunta?",
            default=True,
            style=custom_style
        ).ask()
        
        if not another:
            print("\n👋 Encerrando a CLI. Até logo!")
            break
        
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()