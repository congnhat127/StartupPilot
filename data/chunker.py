import re
import hashlib

class TextChunker:
    """
    Lớp xử lý việc phân mảnh (chunking) văn bản.
    Đã được nâng cấp lên Semantic Chunking (Cắt theo Ngữ nghĩa Pháp luật Việt Nam).
    Tôn trọng ranh giới Điều, Khoản, Điểm thay vì cắt bừa bãi theo số ký tự.
    """

    @staticmethod
    def chunk_parent_child(text: str, parent_max_len: int = 1500, child_max_len: int = 250) -> list[dict]:
        """
        Chia văn bản luật theo cấu trúc Ngữ nghĩa (Semantic Chunking).
        - Chunk cha (Parent): Toàn bộ 1 'Điều' (Article).
        - Chunk con (Child): Từng 'Khoản' (Clause) bên trong Điều đó.
                             Child sẽ được đính kèm Tiêu đề Điều để giữ trọn ngữ cảnh.
        """
        if not text:
            return []
            
        results = []
        
        # Tách văn bản theo các Điều (Dấu hiệu: bắt đầu bằng "Điều X.")
        # Dùng lookahead (?=...) để giữ lại chữ "Điều" trong kết quả cắt
        articles = re.split(r'(?=(?:^|\n)Điều \d+\.)', text)
        
        # Biến lưu trữ ngữ cảnh Chương/Mục trước đó (nếu có)
        current_chapter_context = ""
        
        for article in articles:
            article = article.strip()
            if not article:
                continue
                
            # Nếu đoạn này KHÔNG bắt đầu bằng "Điều" (Ví dụ: Lời mở đầu, Căn cứ ban hành...)
            # Ta sẽ BỎ QUA hoàn toàn để tránh làm nhiễu dữ liệu RAG.
            if not re.match(r'^Điều \d+\.', article):
                continue

                
            # TỚI ĐÂY: Chắc chắn là một "Điều" luật chuẩn
            parent_text = article
            parent_id = f"parent_{hashlib.md5(parent_text.encode('utf-8')).hexdigest()[:8]}"
            
            # Trích xuất riêng Tiêu đề Điều (Dòng đầu tiên)
            lines = article.split('\n', 1)
            article_title = lines[0].strip()
            
            # Nếu Điều này có nội dung bên dưới
            if len(lines) > 1:
                body = lines[1]
                # Tách nội dung theo Khoản (Dấu hiệu: bắt đầu bằng số và dấu chấm "1. ", "2. ")
                clauses = re.split(r'(?=(?:^|\n)\d+\.\s)', body)
            else:
                clauses = []
                
            # Trường hợp 1: Điều rất ngắn, không chia Khoản (Ví dụ: Điều khoản thi hành)
            if not clauses:
                results.append({
                    "child_id": f"{parent_id}_child_0",
                    "child_text": article_title,
                    "parent_id": parent_id,
                    "parent_text": parent_text
                })
                continue
                
            # Trường hợp 2: Điều có nhiều Khoản
            for c_idx, clause in enumerate(clauses):
                clause = clause.strip()
                if not clause:
                    continue
                    
                # GẮN TIÊU ĐỀ ĐIỀU VÀO TRƯỚC KHOẢN ĐỂ TẠO CHILD TEXT MANG ĐỦ NGỮ CẢNH
                # Ví dụ Child Text: "Điều 2. Người nộp thuế\n1. Người nộp thuế thu nhập cá nhân là..."
                child_text = f"{article_title}\n{clause}"
                
                results.append({
                    "child_id": f"{parent_id}_child_{c_idx}",
                    "child_text": child_text,
                    "parent_id": parent_id,
                    "parent_text": parent_text
                })
                
        return results
