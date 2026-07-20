import os
import sys
import pickle
import sqlite3
import chromadb
from google import genai
from rank_bm25 import BM25Okapi # Cần thiết để giải mã file pickle của BM25

# Đảm bảo import được các module từ thư mục gốc
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config import VECTOR_DB_DIR, BM25_INDEX_PATH, SQLITE_DB_PATH, GEMINI_API_KEY

class LegalRAGSearch:
    """
    Lớp xử lý việc tìm kiếm (Retrieval) theo cơ chế Hybrid Search:
    Kết hợp giữa Semantic Search (Vector) và Keyword Search (BM25).
    Triệu hồi Parent Text từ SQLite và loại bỏ các Parent trùng lặp.
    """
    def __init__(self):
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            raise ValueError("Thiếu GEMINI_API_KEY. Vui lòng kiểm tra lại file .env")
            
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        
        # 1. Khởi tạo kết nối Vector DB (ChromaDB)
        self.chroma_client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        self.collection = self.chroma_client.get_collection(name="legal_docs")
        
        # 2. Tải mô hình BM25 (Keyword Search)
        try:
            with open(BM25_INDEX_PATH, "rb") as f:
                bm25_data = pickle.load(f)
                self.bm25 = bm25_data["bm25"]
                self.bm25_metadata = bm25_data["metadata"]
        except Exception as e:
            print(f"Không thể tải BM25 Index. Lỗi: {e}")
            self.bm25 = None
            
        # 3. Kết nối SQLite để lấy Parent Text
        self.conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
    def _get_query_embedding(self, query: str) -> list[float]:
        """Tạo vector cho câu hỏi của người dùng"""
        response = self.client.models.embed_content(
            model="gemini-embedding-2",
            contents=query
        )
        return response.embeddings[0].values
        
    def _vector_search(self, query: str, top_k: int = 10) -> list[dict]:
        """Tìm kiếm bằng Vector (Ý nghĩa/Ngữ nghĩa)"""
        query_vector = self._get_query_embedding(query)
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        
        search_results = []
        for i in range(len(results['ids'][0])):
            search_results.append({
                "child_id": results['ids'][0][i],
                "parent_id": results['metadatas'][0][i]['parent_id'],
                # Đổi khoảng cách (distance) thành điểm (score) - Càng lớn càng tốt
                "score": 1.0 / (results['distances'][0][i] + 0.001)
            })
        return search_results
        
    def _keyword_search(self, query: str, top_k: int = 10) -> list[dict]:
        """Tìm kiếm bằng BM25 (Từ khóa chính xác)"""
        if not self.bm25:
            return []
            
        # Tokenize câu hỏi (Tương tự như lúc Ingest)
        tokenized_query = query.lower().split()
        
        # Lấy điểm số BM25 cho tất cả tài liệu
        doc_scores = self.bm25.get_scores(tokenized_query)
        
        # Sắp xếp và lấy top K index có điểm cao nhất
        top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
        
        search_results = []
        for idx in top_indices:
            score = doc_scores[idx]
            if score > 0: # Bỏ qua các tài liệu không chứa bất kỳ từ khóa nào
                search_results.append({
                    "child_id": self.bm25_metadata[idx]["child_id"],
                    "parent_id": self.bm25_metadata[idx]["parent_id"],
                    "score": score
                })
        return search_results
        
    def hybrid_search(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Gộp kết quả từ Vector và BM25 (dùng Reciprocal Rank Fusion - RRF).
        Lấy Parent Text từ SQLite và đảm bảo không có Parent bị trùng lặp.
        """
        # 1. Lấy kết quả từ 2 nhánh (Lấy nhiều hơn để có dải trộn tốt)
        vector_results = self._vector_search(query, top_k=top_k * 2)
        keyword_results = self._keyword_search(query, top_k=top_k * 2)
        
        # 2. Trộn và tính điểm RRF (Reciprocal Rank Fusion)
        rrf_scores = {}
        k_constant = 60 # Hằng số k tiêu chuẩn cho RRF
        
        # Cộng điểm RRF từ nhánh Vector
        for rank, item in enumerate(vector_results):
            child_id = item["child_id"]
            if child_id not in rrf_scores:
                rrf_scores[child_id] = {"score": 0, "parent_id": item["parent_id"]}
            rrf_scores[child_id]["score"] += 1.0 / (k_constant + rank + 1)
            
        # Cộng điểm RRF từ nhánh Keyword (BM25)
        for rank, item in enumerate(keyword_results):
            child_id = item["child_id"]
            if child_id not in rrf_scores:
                rrf_scores[child_id] = {"score": 0, "parent_id": item["parent_id"]}
            rrf_scores[child_id]["score"] += 1.0 / (k_constant + rank + 1)
            
        # 3. Sắp xếp Child Chunks dựa trên tổng điểm RRF
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        
        # 4. Truy xuất Parent Text từ SQLite
        final_contexts = []
        seen_parents = set()
        
        for child_id, data in sorted_results:
            parent_id = data["parent_id"]
            
            # TRÁNH TRÙNG LẶP NGUYÊN TẮC: Nếu Điều X đã có trong danh sách, bỏ qua các Khoản khác của Điều X.
            if parent_id in seen_parents:
                continue
                
            self.cursor.execute("SELECT parent_text, legal_source FROM parent_chunks WHERE parent_id = ?", (parent_id,))
            row = self.cursor.fetchone()
            
            if row:
                final_contexts.append({
                    "parent_id": parent_id,
                    "parent_text": row[0],
                    "source": row[1],
                    "rrf_score": data["score"]
                })
                seen_parents.add(parent_id)
                
            # Đủ số lượng Ngữ cảnh Cha mong muốn thì dừng
            if len(final_contexts) >= top_k:
                break
                
        return final_contexts

# ==========================================
# KHU VỰC TEST NHANH (Sẽ chạy nếu gọi trực tiếp file này)
# ==========================================
if __name__ == "__main__":
    searcher = LegalRAGSearch()
    
    queries = [
        "Cá nhân không cư trú thì có phải nộp thuế thu nhập cá nhân không?", # Câu hỏi định nghĩa tổng quát
        "Nghị quyết số 203/2025/QH15" # Câu hỏi thiên về số hiệu văn bản (BM25 sẽ ăn điểm)
    ]
    
    for q in queries:
        print(f"\n❓ CÂU HỎI: '{q}'\n" + "="*70)
        results = searcher.hybrid_search(q, top_k=3)
        
        for i, res in enumerate(results):
            print(f"🏆 [TOP {i+1}] - Điểm RRF (Hybrid): {res['rrf_score']:.4f}")
            flat_parent = res['parent_text'].replace('\n', ' ')
            preview = flat_parent[:200] + "..." if len(flat_parent) > 200 else flat_parent
            print(f"📚 Điều luật (Parent Text):\n   {preview}")
            print("-" * 70)
