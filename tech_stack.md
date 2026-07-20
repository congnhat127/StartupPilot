# Bách Khoa Toàn Thư Công Nghệ (Tech Stack Rationale)

Tài liệu này lưu trữ lý do sâu xa, ưu điểm và nhược điểm của việc lựa chọn các công nghệ, thư viện đang được sử dụng trong dự án AI Legal & Tax Agent.

---

## 1. Hệ Quản Trị Cơ Sở Dữ Liệu Vector (Vector Database)
**Lựa chọn:** `chromadb`
*   **ChromaDB là gì?** Là một cơ sở dữ liệu lưu trữ các dãy số (Vector) thay vì chữ viết (Text). Nó cho phép tìm kiếm theo "Ý nghĩa" (Semantic Search) thay vì đếm từ khóa.
*   **Ưu điểm:**
    *   *Serverless / Local:* Chạy trực tiếp trên máy tính/ổ cứng mà không cần cài đặt Docker hay máy chủ (rất nhẹ nhàng cho MVP).
    *   *Tích hợp Python tuyệt vời:* Lập trình siêu nhanh, hỗ trợ tốt Metadata Filtering (lọc theo ngày/hiệu lực).
*   **Nhược điểm:** Hiệu năng giảm khi lượng vector lên tới hàng chục triệu (Lúc đó sẽ cần đổi sang Qdrant hoặc Milvus).
*   **Công nghệ bị loại bỏ:** Pinecone (phải kết nối mạng, rò rỉ dữ liệu lên Cloud), Qdrant/Milvus (quá nặng nề cho bản MVP).

---

## 2. Tìm Kiếm Từ Khóa (Keyword / Sparse Search)
**Lựa chọn:** `rank_bm25`
*   **BM25 là gì?** Là thuật toán tìm kiếm từ khóa kinh điển, là "trái tim" của Elasticsearch. Nó tìm chữ khớp chính xác nhưng có chấm điểm thông minh (loại bỏ từ phổ biến, thưởng điểm từ hiếm).
*   **Lý do sử dụng:** Vector Database cực dốt trong việc tìm các con số hoặc mã luật chính xác (VD: "Thông tư 40" và "Thông tư 41" có vector ý nghĩa rất giống nhau). Thư viện `rank_bm25` chạy nội bộ bằng Python sẽ giải quyết lỗ hổng này.
*   **Ưu điểm:** Nhẹ, chạy nội bộ bằng CPU cực nhanh, tìm chính xác 100% các mã số luật, điều khoản.
*   **Nhược điểm:** Chỉ bắt được chữ khớp chính xác, không hiểu từ đồng nghĩa.
*   **Công nghệ bị loại bỏ / Tương lai:** 
    *   *SPLADE:* Thuật toán AI thế hệ mới thông minh hơn BM25 nhưng quá nặng, yêu cầu GPU để chạy.
    *   *Elasticsearch:* Giải pháp chuẩn Enterprise nhưng đòi hỏi phải cài thêm Java Server cồng kềnh.

---

## 3. Backend Framework (Khung phần mềm API)
**Lựa chọn:** `fastapi` & `uvicorn`
*   **Tại sao lại chọn?** Hệ thống RAG và LLM phải mất nhiều giây để xử lý. Nếu dùng Framework đồng bộ (như Flask/Django cũ), hệ thống sẽ bị treo khi có nhiều người hỏi cùng lúc.
*   **Ưu điểm:** 
    *   Viết code Bất đồng bộ (`async / await`) cực kỳ tối ưu.
    *   Hỗ trợ sẵn tính năng Streaming (gửi từng chữ của AI về màn hình như ChatGPT).
    *   Tự động tạo tài liệu API Swagger UI.
*   **Công nghệ bị loại bỏ:** `Flask` (đồng bộ, khó mở rộng chịu tải), `Django` (quá nặng và dư thừa tính năng cho một hệ thống thuần API).

---

## 4. Cơ Sở Dữ Liệu Lưu Lịch Sử (Relational Database)
**Lựa chọn:** `SQLite`
*   **Lý do sử dụng:** Lưu trữ lịch sử chat, vết truy xuất (Audit Trail) của hệ thống.
*   **Ưu điểm:** Nằm chung trong thư mục code, chỉ là một file `.sqlite`, không cần cài bất kỳ phần mềm quản trị database nào. Thích hợp cho giai đoạn MVP dưới 100 users.
*   **Cách khắc phục nhược điểm:** Bật chế độ `WAL (Write-Ahead Logging)` để tránh lỗi database bị khóa khi nhiều người dùng cùng nhắn tin.
*   **Công nghệ tương lai (Khi Scale):** `PostgreSQL` sẽ được sử dụng thay thế khi ứng dụng public ra thị trường cho hàng ngàn người dùng, đòi hỏi tính nhất quán ghi (write concurrency) cao.

---

## 5. SDK Trí Tuệ Nhân Tạo
**Lựa chọn:** `google-genai`
*   **Lý do sử dụng:** Đây là SDK chính thức mới nhất của Google để tương tác với mô hình Gemini (cả LLM Text Generation và Text Embedding).
*   **Ưu điểm:** Gemini 1.5 có Context Window cực lớn (lên tới 1-2 triệu tokens), rất phù hợp để nhét nhiều chunk luật pháp vào prompt làm ngữ cảnh. Mô hình `text-embedding-004` của Gemini hiện đang đứng top đầu thế giới về chất lượng nhúng (embedding) và đặc biệt miễn phí hạn mức cao.
