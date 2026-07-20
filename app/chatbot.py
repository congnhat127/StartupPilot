import os
import sys
from google import genai

# Đảm bảo import được các module từ thư mục gốc
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config import GEMINI_API_KEY
from tools.rag_search import LegalRAGSearch
from utils.pii_masker import PIIMasker

class StartupPilotBot:
    """
    Lớp Agent chính: Điểm giao tiếp cuối cùng gộp toàn bộ các quy trình:
    1. Masking (Bảo mật PII)
    2. Retrieval (Tìm luật bằng RAG)
    3. Augmented (Tạo Prompt)
    4. Generation (Gọi LLM sinh câu trả lời)
    """
    def __init__(self):
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            raise ValueError("Thiếu GEMINI_API_KEY trong file .env")
            
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Khởi tạo bộ máy tìm kiếm (Chữ R)
        self.search_engine = LegalRAGSearch()
        
        # Thiết lập tính cách của Bot (System Instruction)
        self.system_instruction = """Bạn là StartupPilot - một chuyên gia tư vấn Pháp lý và Thuế chuyên nghiệp tại Việt Nam.
Nhiệm vụ của bạn là trả lời các câu hỏi của người dùng DỰA TRÊN NGỮ CẢNH (Văn bản luật) được cung cấp.
- Nếu ngữ cảnh không chứa câu trả lời, hãy nói rõ là bạn không tìm thấy thông tin, KHÔNG ĐƯỢC TỰ BỊA ĐẶT (Hallucination).
- Luôn trích dẫn rõ ràng bạn đang lấy thông tin từ Điều nào, Khoản nào.
- Trình bày câu trả lời lịch sự, rõ ràng, dễ hiểu, sử dụng định dạng danh sách (bullet points) để dễ đọc."""

    def ask(self, user_question: str) -> str:
        # BƯỚC 1: CHE MỜ DỮ LIỆU NHẠY CẢM (PII Masking)
        safe_question = PIIMasker.mask_all(user_question)
        print(f"\n[Hệ thống] Đã qua màng lọc an ninh: '{safe_question}'")
        
        # BƯỚC 2: TRUY XUẤT LUẬT (Retrieval)
        print("[Hệ thống] Đang quét các văn bản luật liên quan (Hybrid Search)...")
        contexts = self.search_engine.hybrid_search(safe_question, top_k=3)
        
        if not contexts:
            return "Xin lỗi, tôi không tìm thấy tài liệu luật nào liên quan đến câu hỏi của bạn."
            
        # BƯỚC 3: TĂNG CƯỜNG PROMPT (Augmented)
        context_text = ""
        for i, ctx in enumerate(contexts):
            context_text += f"\n--- ĐIỀU LUẬT TÌM THẤY {i+1} ---\n{ctx['parent_text']}\n"
            
        final_prompt = f"""NGỮ CẢNH PHÁP LÝ TỪ CƠ SỞ DỮ LIỆU:
{context_text}

CÂU HỎI CỦA NGƯỜI DÙNG: {safe_question}

Hãy đóng vai chuyên gia pháp lý, trả lời câu hỏi trên một cách chi tiết và chính xác DỰA VÀO Ngữ cảnh pháp lý đã cho."""
        
        # BƯỚC 4: SINH CÂU TRẢ LỜI (Generation)
        print("[Hệ thống] Đang đọc luật và soạn câu trả lời...")
        response = self.client.models.generate_content(
            model="gemini-2.5-flash", # Dùng model chat tiên tiến
            contents=final_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                temperature=0.3 # Tăng lên 0.3 để tránh lỗi lặp từ (Repetition Loop)
            )
        )
        
        return response.text

# ==========================================
# GIAO DIỆN CHAT TRÊN TERMINAL
# ==========================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🤖 ĐANG KHỞI ĐỘNG STARTUP PILOT - TRỢ LÝ PHÁP LÝ AI...")
    bot = StartupPilotBot()
    print("✅ KHỞI ĐỘNG THÀNH CÔNG!")
    print("="*60)
    
    while True:
        question = input("\n👤 BẠN: ")
        
        if question.lower() in ['exit', 'quit', 'thoát', 'q']:
            print("Tạm biệt! Hẹn gặp lại.")
            break
            
        if not question.strip():
            continue
            
        answer = bot.ask(question)
        print(f"\n⚖️  STARTUP PILOT:\n{answer}")
        print("-" * 60)
