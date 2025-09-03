# /chatbotAI/app/__init__.py
from flask import Flask
from config import Config

def create_app(config_class=Config):
    """
    Application Factory: Hàm tạo và cấu hình ứng dụng Flask.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Sử dụng app_context để đảm bảo context của ứng dụng có sẵn
    with app.app_context():
        # Import các thành phần khác ở đây để tránh lỗi circular import
        from .services import google_sheets_service as gs
        
        # --- Tải dữ liệu một lần khi khởi động ---
        print("Đang tải dữ liệu từ Google Sheet khi khởi động...")
        initial_data = gs.get_google_sheet_data()
        if initial_data is None:
            print("LỖI NGHIÊM TRỌNG: Không thể tải dữ liệu ban đầu.")
        
        # Gắn dữ liệu đã tải vào đối tượng app để các blueprint có thể truy cập
        app.initial_sheet_data = initial_data
        
        # --- Đăng ký Blueprints ---
        from .api.chat_api import chat_bp
        from .api.knowledge_api import knowledge_bp

        # Sử dụng url_prefix để tổ chức các endpoint tốt hơn
        # Ví dụ: /api/chat/ask, /api/knowledge/add-knowledge
        app.register_blueprint(chat_bp, url_prefix='/api/chat')
        app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')
        print("Đã đăng ký các blueprint thành công!")

    # Route đơn giản để kiểm tra server có đang chạy không
    @app.route('/health')
    def health():
        return "Server is healthy!"

    return app