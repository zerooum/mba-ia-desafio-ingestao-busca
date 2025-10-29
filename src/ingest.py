import os
import re
from pathlib import Path
from decimal import Decimal, InvalidOperation
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

load_dotenv()
for k in ('OPENAI_API_KEY','OPENAI_EMBEDDING_MODEL', 'PDF_PATH'):
    v = os.getenv(k)
    if not v:
        raise ValueError(f"A variável de ambiente {k} não está definida.")

file_name = os.getenv('PDF_PATH')
creation_date = datetime.now().isoformat()
path_pdf = Path(__file__).parent.parent / file_name


def ingest_pdf():
    documents = read_pdf()
    sorted_documents = sort_documents_by_revenue(documents)
    split_docs = split_documents(sorted_documents)
    generate_embeddings(split_docs)
    
def read_pdf():
    documents = PyPDFLoader(str(path_pdf)).load()
    # Remove header, será informado no system prompt
    # Nome da empresa Faturamento Ano de fundação
    return remove_header(documents)

def remove_header(documents):
    for doc in documents:
        lines = doc.page_content.split("\n")
        doc.page_content = "\n".join(lines[1:])
    return documents

def extract_revenue(line):
    """
    Extrai o valor do faturamento de uma linha do documento.
    Formato esperado: Nome da empresa TIPO R$ valor ANO
    Exemplo: Aliança Esportes ME R$ 4.485.320.049,16 2002
    
    Retorna Decimal para manter precisão exata em valores monetários.
    Lança exceção se não conseguir extrair ou converter o valor.
    """
    # Pattern para capturar o valor monetário - deve ter pelo menos um dígito seguido de vírgula e centavos
    pattern = r'R\$\s*([\d.,]+,\d{2})'
    match = re.search(pattern, line)
    
    if not match:
        raise ValueError(f"Valor monetário não encontrado na linha: '{line}'")
    
    value_str = match.group(1).replace('.', '').replace(',', '.')
    
    try:
        revenue = Decimal(value_str)
        if revenue <= 0:
            raise ValueError(f"Valor monetário inválido ou zero: R$ {value_str}")
        return revenue
    except (ValueError, InvalidOperation) as e:
        raise ValueError(f"Erro ao converter valor monetário '{match.group(1)}' na linha: '{line}'. Erro: {str(e)}")

def sort_documents_by_revenue(documents):
    """
    Ordena todos os documentos por faturamento globalmente (do menor para o maior).
    """
    all_lines_with_revenue = []
    
    for doc in documents:
        lines = doc.page_content.split('\n')
        
        for line in lines:
            if line.strip() and 'R$' in line:
                revenue = extract_revenue(line)
                all_lines_with_revenue.append((line, revenue))
            elif line.strip():  # Linhas não vazias sem faturamento
                raise ValueError(f"Linhas sem faturamento não são permitidas: '{line}'")
    
    all_lines_with_revenue.sort(key=lambda x: x[1], reverse=False)
    sorted_lines = [line for line, _ in all_lines_with_revenue]
    
    # Cria um novo documento com todo o conteúdo ordenado
    if not documents:
        raise ValueError("Lista de documentos está vazia")
    
    try:
        first_doc = documents[0]
        first_doc.page_content = '\n'.join(sorted_lines)
        return  [first_doc]
    except (IndexError, AttributeError) as e:
        raise RuntimeError(f"Erro ao criar documento ordenado: {str(e)}")

def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )

    split_docs = text_splitter.split_documents(documents)
    
    # Sobrescreve os metadados existentes no chunk com os novos metadados
    for doc in split_docs:
        revenues = []
        lines = doc.page_content.split('\n')
        
        for line in lines:
            if line.strip() and 'R$' in line:
                try:
                    revenue = extract_revenue(line)
                    revenues.append(revenue)
                except ValueError:
                    raise ValueError(f"Erro ao extrair revenue na linha: '{line}'")
        
        if revenues:
            doc.metadata = {
                'min_revenue': float(min(revenues)),
                'max_revenue': float(max(revenues)),
                'file_name': file_name,
                'creation_date': creation_date
            }
        else:
            raise ValueError("Chunk sem valores de revenue não são permitidos.")

    return split_docs

def generate_embeddings(documents):
    embeddings = OpenAIEmbeddings(openai_api_key=os.getenv('OPENAI_API_KEY'),
                                  model=os.getenv('OPENAI_EMBEDDING_MODEL'))
    
    store = PGVector(
        embeddings=embeddings,
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
        connection=os.getenv("DATABASE_URL"),
        pre_delete_collection=True,
        use_jsonb=True,
    )

    store.add_documents(documents=documents)

if __name__ == "__main__":
    ingest_pdf()

