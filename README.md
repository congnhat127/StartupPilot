# AI Legal & Tax Agent for Solo-Entrepreneurs

Một AI Agent tự chủ giúp hỗ trợ các thủ tục pháp lý và tính toán thuế cho người mới bắt đầu kinh doanh cá nhân (Hộ kinh doanh cá thể) tại Việt Nam.

## 🚀 Tính năng chính

- **Tra cứu thủ tục pháp lý & thuế (RAG):** Cung cấp thông tin chính xác về quy định thành lập hộ kinh doanh, các loại thuế suất theo ngành nghề và thời hạn kê khai.
- **Tính toán thuế tự động (Tax Calculator):** Tính chính xác thuế GTGT, TNCN và lệ phí môn bài dựa trên doanh thu và ngành nghề mà không lo ảo tưởng số liệu từ LLM.
- **Dự thảo tờ khai đăng ký kinh doanh:** Trợ giúp điền thông tin và tạo file tờ khai đăng ký hộ kinh doanh cá thể.

## 📁 Cấu trúc thư mục dự kiến

```text
ai-agent-prj/
├── config.py             # Cấu hình biến môi trường, API keys
├── requirements.txt      # Thư viện cần cài đặt
├── .env                  # Lưu trữ API Key (Bảo mật)
├── run_cli.py            # Khởi chạy giao diện dòng lệnh (CLI)
├── agent/                # Bộ não Agent (Core Logic)
├── tools/                # Bộ công cụ Agent gọi
└── data/                 # Cơ sở dữ liệu tri thức & mẫu đơn
```

## 🛠️ Hướng dẫn cài đặt (Dự kiến)

1. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
2. Cấu hình biến môi trường trong file `.env`.
3. Chạy chương trình ở chế độ dòng lệnh:
   ```bash
   python run_cli.py
   ```
