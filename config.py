import os
from dotenv import load_dotenv

# Cấu hình các đường dẫn hệ thống
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Tải cấu hình từ file .env với đường dẫn tuyệt đối (Ép ghi đè)
load_dotenv(os.path.join(BASE_DIR, ".env"), override=True)

# Lấy các biến môi trường cấu hình API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Cấu hình các đường dẫn hệ thống
RAW_DOCS_DIR = os.path.join(BASE_DIR, "data", "raw_documents")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "data", "vector_db")
BM25_INDEX_PATH = os.path.join(VECTOR_DB_DIR, "bm25_index.pkl")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "data", "database.sqlite")

# Đảm bảo các thư mục luôn tồn tại
os.makedirs(RAW_DOCS_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# Kiểm tra nhanh cấu hình key khi chương trình import file này
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print("[CẢNH BÁO] Chưa cấu hình GEMINI_API_KEY trong file .env!")
