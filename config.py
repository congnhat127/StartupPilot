import os
from dotenv import load_dotenv

# Tải cấu hình từ file .env
load_dotenv()

# Lấy các biến môi trường cấu hình API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Kiểm tra nhanh cấu hình key khi chương trình import file này
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print("[CẢNH BÁO] Chưa cấu hình GEMINI_API_KEY trong file .env!")
