# Phân Tích Chuyên Sâu Các Phương Pháp RAG & Chiến Lược Kết Hợp Tối Ưu

Tài liệu này trình bày toàn bộ các phương pháp khả dụng cho từng bước trong quy trình RAG, đề xuất phương pháp tối ưu cho dự án **StartupPilot**, và hướng dẫn cách kiểm thử (evaluate) hiệu quả của từng bước.

---

## 1. BẢNG TỔNG HỢP CÁC PHƯƠNG PHÁP & ĐỀ XUẤT CHO STARTUPPILOT

| Bước thực hiện | Các phương pháp khả dụng | Phương pháp đề xuất cho dự án | Cách thức kiểm tra hiệu quả |
| :--- | :--- | :--- | :--- |
| **Bước 1: Đọc & Tiền xử lý** | 1. Plain Text Parsing (TXT/MD)<br>2. Rule-based PDF Parsing<br>3. OCR Scanning<br>4. AI Layout Parsing (Gemini Vision) | **Plain Text (Markdown do bạn soạn)** kết hợp **AI Layout Parsing** cho tài liệu bảng biểu phức tạp. | Đo chỉ số tỷ lệ lỗi ký tự (CER) và kiểm tra thủ công tính toàn vẹn của cấu trúc bảng biểu. |
| **Bước 2: Phân mảnh (Chunking)** | 1. Character-based<br>2. Token-based<br>3. Sentence-based<br>4. Recursive Character<br>5. Semantic Chunking<br>6. Parent-Child Hierarchical | **Recursive Character Chunking** kết hợp **Parent-Child Hierarchical** (Phân cấp Cha - Con). | Chạy tính năng Dry-run xuất file báo cáo phân mảnh để kiểm tra ranh giới cắt và ngữ cảnh. |
| **Bước 3: Tạo Vector (Embedding)** | 1. Local Models (PhoBERT, BGE)<br>2. API Models (Gemini, OpenAI)<br>3. Hybrid Search (Keyword + Vector) | **API Gemini `text-embedding-004`** kết hợp **Mô hình Reranker** (như Cohere/BGE). | Đo điểm tương đồng Cosine Similarity giữa các nhóm câu đồng nghĩa và trái nghĩa. |
| **Bước 4: Phân bổ dữ liệu DB** | 1. Flat Collection (Gộp chung)<br>2. Multi-collection (Chia bảng)<br>3. Metadata Filtering<br>4. Hybrid Relational-Vector | **Metadata Filtering** kết hợp **Hybrid Relational-Vector DB** (SQLite + ChromaDB). | Đo tốc độ truy vấn (Query Latency) và kiểm tra rò rỉ dữ liệu phân quyền. |

---

## 2. CHI TIẾT TỪNG BƯỚC & ĐỀ XUẤT KẾT HỢP TỐI ƯU

### BƯỚC 1: ĐỌC FILE & TIỀN XỬ LÝ (READ & PREPROCESSING)
*   **Các phương pháp:**
    1.  *Plain Text Parsing (Đọc thô):* Đọc trực tiếp `.txt` hoặc `.md`. Đơn giản nhất nhưng đòi hỏi dữ liệu đầu vào đã được làm sạch sẵn.
    2.  *Rule-based PDF Parsing (PyPDF, PDFMiner):* Dùng thư viện lập trình để trích xuất text từ tọa độ file PDF. Rất hay bị lỗi font tiếng Việt và làm vỡ cấu trúc bảng biểu.
    3.  *OCR-based Parsing (Tesseract):* Chuyển trang tài liệu thành ảnh rồi quét chữ. Dành cho file scan ảnh, tốc độ rất chậm.
    4.  *AI-based Layout Parsing (Gemini Vision, LlamaParse):* Sử dụng trí tuệ nhân tạo đọc hiểu bố cục tài liệu, chuyển đổi hình vẽ, sơ đồ và bảng biểu phức tạp thành định dạng Markdown có cấu trúc.
*   **Đề xuất tối ưu cho StartupPilot:**
    *   Do tài liệu thuế/pháp lý hộ kinh doanh chứa nhiều bảng biểu thuế suất phức tạp, chúng ta sẽ kết hợp **đầu vào Markdown chuẩn (bạn soạn)** và sử dụng **AI-based Layout Parsing** nếu nạp file PDF gốc của Tổng cục Thuế. Bảng biểu phải được bảo toàn dưới dạng định dạng Markdown Table để không làm sai lệch số liệu dòng/cột.
*   **Cách kiểm tra hiệu quả:**
    *   *Phương pháp kiểm tra:* Xuất kết quả đọc file ra file văn bản tạm thời. So sánh đối chiếu thủ công các bảng biểu xem có bị vỡ cấu trúc không, hoặc dùng mã lệnh đếm số từ/số ký tự bị mất/lỗi font.

---

### BƯỚC 2: PHÂN MẢNH TÀI LIỆU (CHUNKING)
*   **Các phương pháp:**
    1.  *Character/Token Chunking:* Cắt đúng số lượng ký tự/token quy định. Nhanh nhưng dễ cắt đôi từ, đôi câu ở giữa.
    2.  *Sentence-based Chunking:* Cắt dựa trên dấu kết thúc câu (`.`, `!`, `?`). Đảm bảo câu nguyên vẹn.
    3.  *Recursive Character Chunking:* Cắt theo danh sách ký tự ưu tiên giảm dần (`\n\n` -> `\n` -> `.` -> ` `). Giúp giữ các đoạn văn gần nhau trong cùng một chunk.
    4.  *Parent-Child (Hierarchical) Chunking:* Chunk cha lớn (800-1000 ký tự) chứa ngữ cảnh rộng, chunk con nhỏ (150-200 ký tự) để tìm kiếm chính xác.
*   **Đề xuất kết hợp tối ưu (Hybrid Strategy):**
    *   **Kết hợp Parent-Child + Recursive Character Chunking:**
        *   *Cách chạy:* Chúng ta chia tài liệu thành các **Chunk cha** chứa toàn bộ một điều khoản/quy chế thuế hoàn chỉnh (để LLM đọc không bị mất ý đầu ý cuối).
        *   Bên trong mỗi chunk cha, ta chia thành nhiều **Chunk con** cực nhỏ (mỗi chunk chỉ gồm 1-2 câu quy định cụ thể).
        *   Khi người dùng hỏi, Vector DB sẽ so khớp và tìm ra **Chunk con** tương đồng nhất, nhưng khi gửi thông tin cho LLM trả lời, ta sẽ truy xuất và gửi toàn bộ **Chunk cha** chứa chunk con đó.
*   **Cách kiểm tra hiệu quả:**
    *   *Phương pháp kiểm tra:* Chạy tính năng **Dry-run xuất báo cáo**. Chúng ta mở file báo cáo chunking để kiểm tra xem ranh giới cắt của các chunk con có nằm đúng điểm kết thúc câu không, và kiểm tra xem chunk cha có bao trọn vẹn ngữ cảnh của chunk con không.

---

### BƯỚC 3: GỌI MODEL TẠO VECTOR (EMBEDDING)
*   **Các phương pháp:**
    1.  *Local Models (PhoBERT, BGE-M3):* Chạy hoàn toàn offline trên máy tính, bảo mật tuyệt đối cho dữ liệu doanh nghiệp nhưng tốc độ phụ thuộc vào GPU cục bộ.
    2.  *API-based Models (Gemini `text-embedding-004`):* Tốc độ phản hồi nhanh, chất lượng mô hình tốt nhất hiện tại, xử lý đa ngôn ngữ xuất sắc.
    3.  *Hybrid Search (Từ khóa + Vector):* Kết hợp tìm kiếm từ khóa truyền thống (BM25) và tìm kiếm Vector ngữ nghĩa để bổ trợ cho nhau.
*   **Đề xuất kết hợp tối ưu (Hybrid Strategy):**
    *   **Kết hợp Gemini Embedding API + Reranking (Xếp hạng lại):**
        *   Chúng ta dùng `text-embedding-004` để tìm kiếm nhanh ra Top 10 đoạn văn có độ tương đồng vector cao nhất.
        *   Sau đó, dùng một mô hình **Reranker** (chạy cục bộ hoặc qua API như Cohere Rerank) để so sánh sâu sắc tính logic giữa câu hỏi của người dùng và Top 10 đoạn văn đó. Reranker sẽ sắp xếp lại thứ tự ưu tiên và lọc ra Top 3 tốt nhất gửi cho LLM. Phương pháp này giúp lọc bỏ các chunk trùng từ khóa nhưng mang nghĩa phủ định.
*   **Cách kiểm tra hiệu quả:**
    *   *Phương pháp kiểm tra:* Lập trình một hàm đo khoảng cách Cosine. Lấy 3 câu đồng nghĩa (Ví dụ: *"Nộp thuế môn bài ở đâu?"*, *"Địa điểm nộp lệ phí môn bài"*, *"Nơi đóng thuế môn bài"*) và kiểm tra xem điểm số tương đồng giữa chúng có đạt trên 0.85 hay không. Đồng thời lấy 1 câu trái nghĩa và kiểm tra xem điểm tương đồng có thấp hay không.

---

### BƯỚC 4: PHÂN BỔ DỮ LIỆU TRONG VECTOR DATABASE (DB PARTITIONING)
*   **Các phương pháp:**
    1.  *Flat Collection:* Cho tất cả dữ liệu vào 1 bảng duy nhất.
    2.  *Multi-collection:* Tạo nhiều bảng riêng biệt (Bảng luật thuế, Bảng đăng ký kinh doanh, Bảng dữ liệu người dùng).
    3.  *Metadata Filtering:* Lưu chung một bảng nhưng lọc truy vấn dựa trên thẻ tag siêu dữ liệu.
    4.  *Hybrid Relational-Vector DB:* Lưu dữ liệu cấu trúc (SQL) riêng và dữ liệu văn bản (Vector DB) riêng.
*   **Đề xuất kết hợp tối ưu (Hybrid Strategy):**
    *   **Kết hợp Metadata Filtering + Hybrid Relational-Vector DB:**
        *   Thông tin doanh thu, ngành nghề và số tiền tính thuế của người dùng được lưu vào cơ sở dữ liệu quan hệ truyền thống **SQLite** (đảm bảo tính chính xác 100% khi tính toán).
        *   Các tài liệu văn bản luật pháp, thông tư thuế được lưu vào **ChromaDB** (Vector DB), mỗi chunk được gắn chặt metadata: `{"doc_type": "thue" | "phap_ly", "legal_source": "Thong_tu_40"}`.
        *   Khi truy vấn, Agent Core sẽ quyết định: tra cứu chính xác thông tin người dùng từ SQL, hoặc gọi RAG truy xuất tài liệu từ ChromaDB kèm bộ lọc metadata để loại bỏ nhiễu từ các văn bản khác chủ đề.
*   **Cách kiểm tra hiệu quả:**
    *   *Phương pháp kiểm tra:* Gửi một câu hỏi thuộc chủ đề Thuế nhưng áp bộ lọc metadata là `doc_type: "phap_ly"`. Hệ thống phải trả về kết quả trống hoặc không liên quan đến thuế. Điều này chứng minh bộ lọc hoạt động chính xác 100%, bảo mật dữ liệu phân vùng thành công.
