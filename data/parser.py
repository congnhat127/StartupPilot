import os
from google import genai
from config import GEMINI_API_KEY
try:
    import docx
except ImportError:
    docx = None

class DocumentParser:
    """
    Module xử lý các file tài liệu phức tạp (PDF, DOCX) 
    và chuyển đổi chúng thành định dạng Markdown (.md) chuẩn.
    """
    
    def __init__(self):
        # Khởi tạo Gemini Client để dùng AI phân tích cấu trúc PDF
        if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
            self.client = genai.Client(api_key=GEMINI_API_KEY)
        else:
            self.client = None

    def parse_pdf_to_md(self, pdf_path: str) -> str:
        """
        Sử dụng Gemini AI để đọc file PDF, bảo toàn 100% cấu trúc bảng biểu.
        """
        if not self.client:
            raise ValueError("Cần cấu hình GEMINI_API_KEY trong file .env để dùng tính năng AI parse PDF.")
        
        print(f"Đang phân tích PDF bằng AI Vision: {os.path.basename(pdf_path)}...")
        
        # Upload file PDF lên server Google để AI đọc
        uploaded_file = self.client.files.upload(file=pdf_path)
        
        # Đặt câu lệnh prompt ép AI trả về Markdown sạch sẽ
        prompt = (
            "Trích xuất toàn bộ nội dung của tài liệu PDF này thành định dạng Markdown. "
            "Yêu cầu tối quan trọng: Phải giữ nguyên vẹn tuyệt đối cấu trúc của các bảng biểu dưới dạng Markdown Table. "
            "Nếu có sơ đồ, hãy diễn giải nó. Tuyệt đối không tự bịa thêm thông tin, không giải thích gì thêm, chỉ trả về nội dung Markdown."
        )
        
        # Gọi model gemini-1.5-flash (rất rẻ, nhanh và cực mạnh trong việc đọc tài liệu)
        response = self.client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[uploaded_file, prompt]
        )
        
        # Dọn dẹp xóa file trên server Google để bảo mật
        self.client.files.delete(name=uploaded_file.name)
        
        return response.text

    def parse_docx_to_md(self, docx_path: str) -> str:
        """
        Trích xuất văn bản từ file Word (.docx) sang Markdown cục bộ.
        """
        if not docx:
            raise ImportError("Vui lòng cài đặt thư viện 'python-docx' (pip install python-docx).")
            
        print(f"Đang đọc file DOCX cục bộ: {os.path.basename(docx_path)}...")
        doc = docx.Document(docx_path)
        
        markdown_lines = []
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if text:
                # Chuyển đổi các Heading của Word thành Tiêu đề Markdown (#)
                if paragraph.style.name.startswith('Heading'):
                    level = paragraph.style.name.replace('Heading', '').strip()
                    try:
                        md_level = '#' * int(level)
                        markdown_lines.append(f"\n{md_level} {text}\n")
                    except ValueError:
                        markdown_lines.append(f"\n# {text}\n")
                else:
                    markdown_lines.append(text)
        
        return "\n".join(markdown_lines)
