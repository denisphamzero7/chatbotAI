# /chatbotAI/app/api/chat_api.py
from flask import Blueprint, request, jsonify, current_app
from app.services import ai_service, google_sheets_service as gs
import datetime

# Tạo một Blueprint
chat_bp = Blueprint('chat_api', __name__)

@chat_bp.route('/ask', methods=['POST'])
def ask():
    # Lấy dữ liệu đã được tải sẵn từ application context
    sheet_data_df = current_app.initial_sheet_data
 
    if sheet_data_df is None:
        return jsonify({'error': 'Dữ liệu chưa được tải hoặc tải lỗi.'}), 500

    data = request.get_json()
    question = data.get('question')
    if not question:
        return jsonify({'error': 'Câu hỏi không được để trống.'}), 400

    print(f"Nhận được câu hỏi: {question}")
    answer = ai_service.answer_question_with_deepseek(question, sheet_data_df.copy())

    log_data = [
        datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"),
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        question,
        answer
    ]
    gs.log_chat_history(log_data)
    return jsonify({'answer': answer})

@chat_bp.route('/history-chat', methods=['GET'])
def get_log_chat():
    """Endpoint để lấy toàn bộ lịch sử trò chuyện."""
    history_data = gs.get_chat_history_data()

    if history_data is not None:
        # Nếu lấy dữ liệu thành công (kể cả là danh sách rỗng), trả về dữ liệu đó
        return jsonify(history_data), 200
    else:
        # Nếu có lỗi xảy ra trong service, trả về lỗi 500
        return jsonify({'error': 'Lấy lịch sử chat thất bại từ máy chủ.'}), 500
    
@chat_bp.route('/history-chat-detail', methods=['GET'])
def get_log_chat_detail():
    """
    Endpoint để lấy chi tiết một mục lịch sử trò chuyện dựa vào ID.
    ID được truyền qua query parameter, ví dụ: /history-chat-detail?id=20240903175246123456
    """
    # Lấy chat_id từ query parameters của URL
    chat_id = request.args.get('id')

    # Kiểm tra xem client có cung cấp id hay không
    if not chat_id:
        return jsonify({'error': 'Vui lòng cung cấp "id" của lịch sử chat.'}), 400

    # Gọi service để lấy chi tiết
    chat_detail = gs.get_chat_history_detail_by_id(chat_id)

    # Xử lý kết quả trả về từ service
    if chat_detail:
        # Nếu tìm thấy, trả về dữ liệu với status code 200 OK
        return jsonify(chat_detail), 200
    else:
        # Nếu không tìm thấy, trả về lỗi 404 Not Found
        return jsonify({'error': f'Không tìm thấy lịch sử chat với ID: {chat_id}'}), 404

