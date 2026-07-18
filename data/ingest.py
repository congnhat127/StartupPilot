import os
import sys
import json
import sqlite3
import pickle
import hashlib
import chromadb
from google import genai
from rank_bm25 import BM25Okapi

# Đảm bảo import được các module từ thư mục gốc
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config import RAW_DOCS_DIR, VECTOR_DB_DIR, BM25_INDEX_PATH, SQLITE_DB_PATH, GEMINI_API_KEY
from data.parser import DocumentParser
from data.cleaner import TextCleaner
from data.chunker import TextChunker

# ==========================================
# KHỞI TẠO CÁC KẾT NỐI (DB, API)
# ==========================================
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    raise ValueError("Thiếu GEMINI_API_KEY. Vui lòng kiểm tra lại file .env")

client = genai.Client(api_key=GEMINI_API_KEY)

# Khởi tạo ChromaDB
chroma_client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
collection = chroma_client.get_or_create_collection(name="legal_docs")

# Khởi tạo SQLite (Lưu Chunk Cha và Cache Embedding)
conn = sqlite3.connect(SQLITE_DB_PATH)
conn.execute('PRAGMA journal_mode=WAL;')  # Bật chế độ WAL để truy xuất đồng thời tốt hơn
cursor = conn.cursor()

# Tạo bảng lưu Chunk Cha (Trích xuất nguyên vẹn cho RAG)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS parent_chunks (
        parent_id TEXT PRIMARY KEY,
        parent_text TEXT,
        legal_source TEXT,
        effective_date TEXT,
        expired_date TEXT,
        status TEXT
    )
''')

# Tạo bảng Cache để tránh tốn tiền gọi API Gemini cho các đoạn văn bản đã từng nhúng (Embedding)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS embedding_cache (
        text_hash TEXT PRIMARY KEY,
        embedding TEXT
    )
''')
conn.commit()


# ==========================================
# CÁC HÀM XỬ LÝ
# ==========================================
def get_embedding_with_cache(text: str) -> list[float]:
    """
    Tạo Vector từ văn bản. Có sử dụng Cache SQLite dựa trên mã băm MD5 của văn bản.
    """
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    
    # 1. Kiểm tra trong Cache
    cursor.execute('SELECT embedding FROM embedding_cache WHERE text_hash = ?', (text_hash,))
    row = cursor.fetchone()
    if row:
        return json.loads(row[0])
    import time
    
    # Nghỉ 1 giây để tránh lỗi 429 Quota Exceeded (Giới hạn 100 request/phút của bản Free)
    time.sleep(1)
    
    # 2. Nếu không có, gọi API Gemini
    response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=text
    )
    embedding = response.embeddings[0].values
    
    # 3. Lưu vào Cache
    cursor.execute('INSERT INTO embedding_cache VALUES (?, ?)', (text_hash, json.dumps(embedding)))
    conn.commit()
    
    return embedding


def extract_metadata_from_filename(filename: str) -> dict:
    """
    Hàm giả lập trích xuất metadata từ tên file.
    Trong thực tế, ta có thể dùng Regex hoặc LLM để trích xuất ngày hiệu lực từ nội dung.
    """
    return {
        "legal_source": filename,
        "effective_date": "2020-01-01", # Giả định
        "expired_date": "2099-12-31",   # Giả định
        "status": "active"              # Giả định
    }


def ingest_documents():
    """
    Luồng Ingestion Pipeline chính.
    """
    parser = DocumentParser()
    bm25_corpus = []
    bm25_metadata = []
    
    files = [f for f in os.listdir(RAW_DOCS_DIR) if f.endswith(('.pdf', '.docx', '.md', '.txt'))]
    if not files:
        print(f"Không tìm thấy tài liệu nào trong {RAW_DOCS_DIR}")
        return

    for filename in files:
        file_path = os.path.join(RAW_DOCS_DIR, filename)
        print(f"\n🚀 Bắt đầu xử lý file: {filename}")
        
        # 1. Phân tích văn bản thô (Parser)
        if filename.endswith(".pdf"):
            raw_text = parser.parse_pdf_to_md(file_path)
        elif filename.endswith(".docx"):
            raw_text = parser.parse_docx_to_md(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
                
        # 2. Dọn rác văn bản (Cleaner)
        clean_text = TextCleaner.clean_markdown(raw_text)
        
        # 3. Gán Metadata
        doc_metadata = extract_metadata_from_filename(filename)
        
        # 4. Phân rã văn bản thành các Chunk Cha-Con (Chunker)
        chunks = TextChunker.chunk_parent_child(clean_text)
        print(f"   -> Đã tạo {len(chunks)} chunk con (từ các chunk cha tương ứng).")
        
        # 5. Lưu vào Database (Xử lý theo batch để tối ưu tốc độ)
        batch_size = 50
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            
            for item in batch:
                child_id = item["child_id"]
                child_text = item["child_text"]
                parent_id = item["parent_id"]
                parent_text = item["parent_text"]
                
                # A. Lưu Chunk Cha vào SQLite (bỏ qua nếu đã tồn tại)
                cursor.execute(
                    'INSERT OR IGNORE INTO parent_chunks VALUES (?, ?, ?, ?, ?, ?)', 
                    (parent_id, parent_text, doc_metadata["legal_source"], 
                     doc_metadata["effective_date"], doc_metadata["expired_date"], doc_metadata["status"])
                )
                
                # Chuẩn bị dữ liệu cho ChromaDB
                ids.append(child_id)
                documents.append(child_text)
                
                # Tạo Vector Embedding (có dùng cache)
                embeddings.append(get_embedding_with_cache(child_text))
                
                # Gắn metadata cho Chunk Con (BẮT BUỘC phải lưu parent_id để truy xuất ngược lại)
                meta = doc_metadata.copy()
                meta["parent_id"] = parent_id
                metadatas.append(meta)
                
                # Chuẩn bị dữ liệu cho BM25
                bm25_corpus.append(child_text)
                bm25_metadata.append({"child_id": child_id, "parent_id": parent_id, **doc_metadata})
            
            # Lưu các thay đổi xuống SQLite
            conn.commit()
            
            # B. Cập nhật vào ChromaDB
            collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            print(f"   -> Đã đưa batch {i//batch_size + 1} ({len(batch)} chunks) vào Vector DB.")
            
    # 6. Tạo chỉ mục tìm kiếm từ khóa BM25 và lưu xuống file
    if bm25_corpus:
        print("\n⏳ Đang tạo chỉ mục BM25...")
        # Tách từ đơn giản (Tokenization) bằng khoảng trắng. Với Tiếng Việt, có thể nâng cấp thư viện Underthesea sau.
        tokenized_corpus = [doc.lower().split() for doc in bm25_corpus]
        bm25 = BM25Okapi(tokenized_corpus)
        
        with open(BM25_INDEX_PATH, "wb") as f:
            pickle.dump({"bm25": bm25, "metadata": bm25_metadata, "corpus": bm25_corpus}, f)
        print(f"✅ Đã lưu BM25 index với {len(bm25_corpus)} tài liệu tại: {BM25_INDEX_PATH}")
        
    print("\n🎉 HOÀN TẤT QUÁ TRÌNH NẠP DỮ LIỆU!")

if __name__ == "__main__":
    ingest_documents()
    conn.close()
