import re

class TextChunker:
    """
    Lớp xử lý việc phân mảnh (chunking) văn bản với các chiến lược khác nhau.
    """
    
    @staticmethod
    def chunk_by_fixed_size(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> list[str]:
        """
        Chia nhỏ văn bản theo độ dài ký tự cố định, có gối đầu (overlap) để giữ ngữ cảnh.
        
        Parameters:
        - text (str): Văn bản thô cần chia nhỏ.
        - chunk_size (int): Độ dài ký tự tối đa của một chunk.
        - chunk_overlap (int): Số ký tự gối đầu giữa các chunk liền kề.
        
        Returns:
        - list[str]: Danh sách các đoạn văn bản sau khi chia.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)
        
        # Nếu văn bản ngắn hơn kích thước chunk, trả về chính nó
        if text_len <= chunk_size:
            return [text]
            
        while start < text_len:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Dịch chuyển con trỏ đọc cho chunk tiếp theo
            start += (chunk_size - chunk_overlap)
            
            # Ngăn vòng lặp vô hạn nếu overlap lớn hơn hoặc bằng chunk_size
            if chunk_size <= chunk_overlap:
                break
                
        return chunks

    @staticmethod
    def chunk_by_sentences(text: str, max_chunk_size: int = 800, chunk_overlap: int = 150) -> list[str]:
        """
        Chia nhỏ văn bản theo đơn vị câu (dựa trên dấu chấm, hỏi, cảm thán),
        đảm bảo không cắt đôi câu ở giữa chừng và gộp các câu lại thành chunk tối đa max_chunk_size.
        """
        if not text:
            return []
            
        # Tách văn bản thành danh sách các câu
        # regex này tìm các dấu kết thúc câu và giữ lại dấu đó
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_len = len(sentence)
            # Nếu câu đơn quá dài vượt max_chunk_size, ta bắt buộc phải cắt câu đó theo ký tự
            if sentence_len > max_chunk_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_length = 0
                # Chia nhỏ câu siêu dài này bằng phương pháp ký tự
                sub_chunks = TextChunker.chunk_by_fixed_size(sentence, max_chunk_size, chunk_overlap)
                chunks.extend(sub_chunks)
                continue
                
            if current_length + sentence_len + 1 > max_chunk_size:
                # Lưu chunk hiện tại
                chunks.append(" ".join(current_chunk))
                # Khởi tạo chunk mới và giữ lại một phần câu cũ làm overlap (nếu có thể)
                # Đơn giản nhất là gối đầu câu cuối cùng của chunk trước sang chunk sau
                if current_chunk:
                    current_chunk = [current_chunk[-1], sentence]
                    current_length = len(current_chunk[0]) + len(sentence) + 1
                else:
                    current_chunk = [sentence]
                    current_length = sentence_len
            else:
                current_chunk.append(sentence)
                current_length += sentence_len + (1 if current_length > 0 else 0)
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
        
    @staticmethod
    def chunk_by_paragraphs(text: str) -> list[str]:
        """
        Chia nhỏ văn bản theo các đoạn văn (phân tách bởi ký tự xuống dòng kép \n\n).
        Phù hợp với tài liệu có cấu trúc ý rõ ràng theo từng đoạn.
        """
        if not text:
            return []
        # Tách theo 2 hoặc nhiều dấu xuống dòng
        paragraphs = re.split(r'\n\s*\n', text)
        # Lọc bỏ các đoạn trống
        return [p.strip() for p in paragraphs if p.strip()]
