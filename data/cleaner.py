import re
import unicodedata

class TextCleaner:
    """
    Tiền xử lý và làm sạch văn bản (Markdown) trước khi đưa vào Chunker.
    Bảo vệ cấu trúc bảng biểu và loại bỏ rác (ảnh, khoảng trắng thừa).
    """
    
    @staticmethod
    def clean_markdown(text: str) -> str:
        if not text:
            return ""
            
        # 1. Chuẩn hóa bộ gõ Unicode (Gộp các dấu tiếng Việt rời rạc về dạng chuẩn)
        text = unicodedata.normalize('NFKC', text)
        
        # 2. Xóa bỏ các thẻ hình ảnh Markdown ![alt](url) vì Vector DB không hiểu ảnh
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        
        # 3. Chuẩn hóa khoảng trắng: Biến 3-4 dòng trống liên tiếp thành tối đa 2 dòng trống (\n\n)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 4. Xóa khoảng trắng thừa vô nghĩa ở đầu và cuối mỗi dòng
        text = '\n'.join([line.strip() for line in text.split('\n')])
        
        return text.strip()
        
    @staticmethod
    def protect_markdown_tables(text: str) -> str:
        """
        Xử lý để bảng biểu Markdown không bị vỡ khi Chunk.
        (Mẹo: Thay thế dấu chấm '.' trong bảng thành ký tự đặc biệt tạm thời 
        để hàm chunk_by_sentences không tưởng nhầm hàng của bảng là một câu).
        """
        # Thuật toán này sẽ được gọi bên trong Chunker nếu cần thiết
        pass
