import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_postgres import PGVector
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# Validate required environment variables
for k in ('OPENAI_API_KEY', 'OPENAI_EMBEDDING_MODEL', 'DATABASE_URL', 'PG_VECTOR_COLLECTION_NAME'):
    v = os.getenv(k)
    if not v:
        raise ValueError(f"Environment variable {k} is not defined.")

PROMPT_TEMPLATE = """
CONTEXT:
{context}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{input}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

def get_vector_store():
    embeddings = OpenAIEmbeddings(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        model=os.getenv('OPENAI_EMBEDDING_MODEL')
    )
    
    store = PGVector(
        embeddings=embeddings,
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
        connection=os.getenv("DATABASE_URL"),
        use_jsonb=True,
    )
    
    return store

def get_self_query_retriever():
    metadata_field_info = [
        AttributeInfo(
            name="min_revenue",
            description=(
                "Valor mínimo de faturamento (em Reais) das empresas neste chunk. "
                "Para encontrar empresas com faturamento INFERIOR a um valor X, use: min_revenue < X. "
                "Para encontrar empresas com faturamento SUPERIOR a um valor X, use: min_revenue > X. "
                "Para encontrar empresas em uma faixa específica, combine min_revenue e max_revenue."
            ),
            type="float",
        ),
        AttributeInfo(
            name="max_revenue",
            description=(
                "Valor máximo de faturamento (em Reais) das empresas neste chunk. "
                "Para encontrar empresas com faturamento INFERIOR a um valor X, use: max_revenue < X. "
                "Para encontrar empresas com faturamento SUPERIOR a um valor X, use: max_revenue > X. "
                "Para encontrar empresas em uma faixa específica, combine min_revenue e max_revenue."
            ),
            type="float",
        ),
        AttributeInfo(
            name="file_name",
            description="O nome do arquivo PDF do qual este chunk foi extraído.",
            type="string",
        ),
        AttributeInfo(
            name="creation_date",
            description="A data em formato ISO de quando este documento foi ingerido no sistema.",
            type="string",
        ),
    ]
    
    document_content_description = (
        "Informações sobre empresas brasileiras incluindo seus nomes, faturamento anual (em R$) e ano de fundação. "
        "Cada chunk contém dados de uma ou mais empresas. Use os metadados min_revenue e max_revenue para filtrar por faixa de faturamento."
    )
    
    # Initialize LLM for query construction
    llm = ChatOpenAI(
        temperature=0,
        model=os.getenv('OPENAI_CHAT_MODEL', 'gpt-3.5-turbo'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    # Get vector store
    vectorstore = get_vector_store()
    
    # Create SelfQueryRetriever
    retriever = SelfQueryRetriever.from_llm(
        llm=llm,
        vectorstore=vectorstore,
        document_contents=document_content_description,
        metadata_field_info=metadata_field_info,
        verbose=True,
        enable_limit=True,
    )
    
    return retriever

def search_prompt(question=None, use_self_query=True):
    if not question:
        raise ValueError("Question cannot be empty")
    
    if use_self_query:
        retriever = get_self_query_retriever()
    else:
        vectorstore = get_vector_store()
        retriever = vectorstore.as_retriever(search_kwargs={"k": 10})
    
    llm = ChatOpenAI(
        temperature=0,
        model=os.getenv('OPENAI_CHAT_MODEL', 'gpt-5-nano'),
        openai_api_key=os.getenv('OPENAI_API_KEY')
    )
    
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    
    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

    response = retrieval_chain.invoke({"input": question})
    
    return {
        "answer": response["answer"],
        "context": response["context"],
        "question": question
    }