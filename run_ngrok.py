import os
from pyngrok import ngrok
from threading import Timer

# Import đối tượng 'web_app' từ file web_app.py của bạn
# Đảm bảo file này được đặt cùng cấp với web_app.py
try:
    from app import app
except ImportError:
    print("LỖI: Không thể import 'web_app' từ file web_app.py.")
    print("Hãy đảm bảo bạn đang chạy file này từ cùng thư mục với web_app.py.")
    exit()

# --- PHẦN CẤU HÌNH ---

# 1. Đặt Authtoken cho ngrok của bạn
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN")

# 2. Cổng mà ứng dụng Flask đang chạy
PORT = 5000

# --- PHẦN THỰC THI ---

def launch_web_app():
    # Đặt authtoken
    if NGROK_AUTHTOKEN:
        ngrok.set_auth_token(NGROK_AUTHTOKEN)
    else:
        print("CẢNH BÁO: NGROK_AUTHTOKEN chưa được thiết lập. Tunnel có thể bị giới hạn.")

    # Tắt các tunnel cũ có thể đang chạy
    for tunnel in ngrok.get_tunnels():
        ngrok.disconnect(tunnel.public_url)
        
    public_url = None
    try:
        # Tạo đường hầm ngrok tới đúng cổng của Flask
        public_url = ngrok.connect(PORT, "http")
        print("-------------------------------------------------")
        print(f"✅ API Flask của bạn đã sẵn sàng!")
        print(f"👉 Truy cập tại đây: {public_url}")
        print("-------------------------------------------------")
        
        # Chạy ứng dụng Flask
        # use_reloader=False là cần thiết để tránh lỗi khi chạy trong môi trường này
        app.run(port=PORT, use_reloader=False)

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
    finally:
        # Đảm bảo ngrok luôn được tắt khi chương trình kết thúc
        if public_url:
            print("\nĐang đóng đường hầm ngrok...")
            ngrok.disconnect(public_url.public_url)
            ngrok.kill()
        print("Chương trình đã kết thúc.")


if __name__ == '__main__':
    launch_web_app()
