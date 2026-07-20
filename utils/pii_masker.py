import re

class PIIMasker:
    """
    Công cụ ẩn danh dữ liệu cá nhân (PII - Personally Identifiable Information).
    Đóng vai trò "Người gác cổng", chặn không cho dữ liệu nhạy cảm của khách hàng
    hoặc công ty lọt ra ngoài Internet (gửi lên API của LLM).
    """
    
    @staticmethod
    def mask_email(text: str) -> str:
        """Che mờ địa chỉ Email"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.sub(pattern, '[EMAIL_ĐÃ_CHE]', text)

    @staticmethod
    def mask_phone(text: str) -> str:
        """
        Che mờ số điện thoại Việt Nam.
        Hỗ trợ các định dạng: 0912345678, 0912 345 678, 0912.345.678, 0912-345-678
        Bắt đầu bằng 0, tiếp theo là 3,5,7,8,9 và đúng 10 số.
        """
        pattern = r'\b0[35789](?:[\s.-]*\d){8}\b'
        return re.sub(pattern, '[SĐT_ĐÃ_CHE]', text)

    @staticmethod
    def mask_cccd(text: str) -> str:
        """Che mờ số Căn cước công dân (CCCD Việt Nam luôn có đúng 12 chữ số)"""
        pattern = r'\b\d{12}\b'
        return re.sub(pattern, '[CCCD_ĐÃ_CHE]', text)
        
    @staticmethod
    def mask_tax_code(text: str) -> str:
        """
        Che mờ Mã số thuế (MST).
        MST doanh nghiệp/cá nhân thường là 10 chữ số. 
        Đôi khi có thêm hậu tố chi nhánh "-XXX" (vd: 0101234567-001).
        """
        pattern = r'\b\d{10}(?:-\d{3})?\b'
        return re.sub(pattern, '[MST_ĐÃ_CHE]', text)

    @staticmethod
    def mask_all(text: str) -> str:
        """
        Thực thi che mờ toàn bộ.
        Lưu ý: Thứ tự quét rất quan trọng để không bị xung đột Regex.
        """
        if not text:
            return text
            
        text = PIIMasker.mask_email(text)
        # Bắt SĐT (10 số, có đầu số quy định) trước
        text = PIIMasker.mask_phone(text)   
        # Bắt CCCD (12 số)
        text = PIIMasker.mask_cccd(text)    
        # Bắt các chuỗi 10 số còn lại (hoặc 13 số có dấu -) làm MST
        text = PIIMasker.mask_tax_code(text)
        
        return text

# ==========================================
# KHU VỰC TEST NHANH 
# ==========================================
if __name__ == "__main__":
    test_text = """
    Chào luật sư, tôi tên là Nguyễn Văn A.
    Căn cước công dân số: 079012345678 cấp tại CA TP.HCM.
    Mã số thuế cá nhân của tôi là 0102030405. Doanh nghiệp tôi là 0102030405-001.
    Liên hệ với tôi qua số điện thoại 0912 345 678 hoặc email nguyenvana123@gmail.com.
    Câu hỏi: Tôi có cần nộp thuế không?
    """
    
    print("--- TRƯỚC KHI CHE (CÓ NGUY CƠ LỘ DỮ LIỆU) ---")
    print(test_text)
    
    print("\n--- SAU KHI QUA CHỐT CHẶN PII_MASKER ---")
    masked_text = PIIMasker.mask_all(test_text)
    print(masked_text)
