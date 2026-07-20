import sys
import os
import glob

# Thêm đường dẫn gốc của thư mục StartupPilot để Python hiểu các module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import RAW_DOCS_DIR
from data.parser import DocumentParser
from data.cleaner import TextCleaner
from data.chunker import TextChunker

def test_full_pipeline():
    parser = DocumentParser()
    
    search_patterns = [
        os.path.join(RAW_DOCS_DIR, "*.md"),
        os.path.join(RAW_DOCS_DIR, "*.txt"),
        os.path.join(RAW_DOCS_DIR, "*.pdf"),
        os.path.join(RAW_DOCS_DIR, "*.docx")
    ]
    
    files = []
    for pattern in search_patterns:
        files.extend(glob.glob(pattern))
        
    if not files:
        print(f"[THÔNG BÁO] Không tìm thấy file tài liệu nào trong thư mục:\n=> {RAW_DOCS_DIR}")
        print("Vui lòng bỏ file .pdf, .docx, hoặc .txt vào đó và chạy lại.")
        return

    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)
        print(f"\n{'='*60}\n▶ ĐANG XỬ LÝ: {file_name}\n{'='*60}")
        
        # BƯỚC 1: PARSING
        raw_text = ""
        try:
            if ext in ['.md', '.txt']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
            elif ext == '.pdf':
                raw_text = parser.parse_pdf_to_md(file_path)
            elif ext == '.docx':
                raw_text = parser.parse_docx_to_md(file_path)
                
            print(f"[BƯỚC 1 - PARSER] ✅ Thành công. Độ dài: {len(raw_text)} ký tự.")
        except Exception as e:
            print(f"[BƯỚC 1 - PARSER] ❌ Lỗi: {e}")
            continue
            
        # BƯỚC 2: CLEANING
        cleaned_text = TextCleaner.clean_markdown(raw_text)
        print(f"[BƯỚC 2 - CLEANER] ✅ Đã dọn rác. Độ dài: {len(cleaned_text)} ký tự.")
        
        # BƯỚC 3: CHUNKING
        chunks = TextChunker.chunk_parent_child(cleaned_text, parent_max_len=1200, child_max_len=200)
        print(f"[BƯỚC 3 - CHUNKER] ✅ Đã băm tài liệu thành {len(chunks)} chunk con.")
        
        if chunks:
            print(f"\n--- XEM TRƯỚC {min(5, len(chunks))} CHUNK ĐẦU TIÊN ---")
            for i in range(min(5, len(chunks))):
                print(f"\n[CHUNK {i+1}]")
                print(f"Child ID: {chunks[i]['child_id']}")
                print(f"Child Text:\n{chunks[i]['child_text']}")
                print(f"Parent Text (Ngữ cảnh gốc):\n{chunks[i]['parent_text']}\n" + "-"*40)

if __name__ == "__main__":
    test_full_pipeline()
