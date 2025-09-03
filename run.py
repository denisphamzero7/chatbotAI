# /chatbotAI/run.py
from app import create_app

# Tạo ứng dụng bằng factory
app = create_app()

if __name__ == '__main__':
    # Chạy ở debug=False khi triển khai thực tế
    app.run(host='0.0.0.0', port=5000, debug=True)