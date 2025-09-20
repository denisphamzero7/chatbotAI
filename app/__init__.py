# /chatbotAI/app/__init__.py
from flask import Flask
from config import Config
from flask_cors import CORS
import time

def create_app(config_class=Config):
    """
    Application Factory: Hàm tạo và cấu hình ứng dụng Flask.
    """
    app = Flask(__name__)
    CORS(app, origins="*")
    app.config.from_object(config_class)

    with app.app_context():
        # Import các service cần thiết
        from .services import google_sheets_service as gs
        from .services.ai_service import embedding_model # ✅ NHẬP MODEL EMBEDDING

        # --- Tải dữ liệu và tính toán embedding một lần ---
        print("Đang tải dữ liệu từ Google Sheet khi khởi động...")
        initial_data = gs.get_google_sheet_data()
        
        # ✅ BẮT ĐẦU TÍNH TOÁN TRƯỚC VECTOR
        app.initial_sheet_data = initial_data
        app.document_embeddings = None # Khởi tạo giá trị

        if initial_data is not None and not initial_data.empty:
            print(f"Dữ liệu đã tải thành công với {len(initial_data)} dòng. Bắt đầu tính toán vector...")
            
            # Chuẩn bị văn bản để vector hóa
            initial_data['search_col'] = initial_data.apply(lambda row: ' '.join(row.astype(str)).lower(), axis=1)
            documents = initial_data['search_col'].tolist()
            
            # Vector hóa
            start_time = time.perf_counter()
            document_embeddings = embedding_model.encode(documents)
            end_time = time.perf_counter()
            
            # Lưu các vector đã tính vào app context
            app.document_embeddings = document_embeddings
            print(f"✅ Đã tính toán và lưu {len(document_embeddings)} vector vào bộ nhớ sau {end_time - start_time:.2f} giây.")

        else:
            print("LỖI NGHIÊM TRỌNG: Không thể tải dữ liệu ban đầu hoặc dữ liệu rỗng.")
        
        # --- Đăng ký Blueprints ---
        from .api.chat_api import chat_bp
        from .api.knowledge_api import knowledge_bp

        app.register_blueprint(chat_bp, url_prefix='/api/chat')
        app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')
        print("Đã đăng ký các blueprint thành công!")

    @app.route('/health')
    def health():
        return "Server is healthy!"

    return app