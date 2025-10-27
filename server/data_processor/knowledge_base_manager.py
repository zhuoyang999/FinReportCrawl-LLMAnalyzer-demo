import os
import chromadb
import pdfplumber
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions

class KnowledgeBaseManager:
    def __init__(self, db_path="chroma_db", model_name='moka-ai/m3e-base'):
        """
        初始化知识库管理器。

        :param db_path: ChromaDB数据库的存储路径。
        :param model_name: 用于生成文本嵌入的预训练模型名称。
        """
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)

    def _extract_text_from_pdf(self, pdf_path):
        """从PDF文件中提取文本。"""
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    def _split_text(self, text, chunk_size=500, chunk_overlap=50):
        """将长文本分割成较小的块。"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - chunk_overlap
        return chunks

    def add_pdf_to_collection(self, pdf_path, collection_name):
        """
        处理单个PDF文件并将其内容添加到指定的集合中。

        :param pdf_path: PDF文件的路径。
        :param collection_name: 要添加到的集合的名称。
        """
        collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )
        
        text = self._extract_text_from_pdf(pdf_path)
        if not text:
            print(f"Warning: Could not extract text from {pdf_path}")
            return

        chunks = self._split_text(text)
        
        # 使用PDF文件名作为文档ID的一部分，以确保唯一性
        pdf_filename = os.path.basename(pdf_path)
        ids = [f"{pdf_filename}_{i}" for i in range(len(chunks))]
        
        collection.add(
            documents=chunks,
            ids=ids
        )
        print(f"Successfully added {len(chunks)} chunks from {pdf_filename} to collection '{collection_name}'.")

    def query(self, collection_name, query_text, n_results=3):
        """
        在指定的集合中查询与给定文本最相关的文档块。

        :param collection_name: 要查询的集合名称。
        :param query_text: 查询文本。
        :param n_results: 返回结果的数量。
        :return: 查询结果。
        """
        collection = self.client.get_collection(name=collection_name, embedding_function=self.embedding_function)
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        return results

if __name__ == '__main__':
    # 示例用法
    manager = KnowledgeBaseManager()
    
    # 假设我们有一个名为 "annual_reports" 的集合
    collection_name = "annual_reports"
    
    # 将单个PDF添加到集合中
    # pdf_file = "path/to/your/report.pdf"
    # manager.add_pdf_to_collection(pdf_file, collection_name)
    
    # 查询示例
    # query = "公司的主要经营风险是什么？"
    # search_results = manager.query(collection_name, query)
    # print("Query Results:", search_results)