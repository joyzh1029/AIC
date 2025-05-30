# 문서들을 HuggingFace 임베딩으로 벡터화한 뒤,
# FAISS를 통해 유사도 검색이 가능한 인덱스를 생성

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

def build_vectorstore(docs):
    return FAISS.from_documents(docs, HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ))