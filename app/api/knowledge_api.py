# /chatbotAI/app/api/knowledge_api.py
from flask import Blueprint, request, jsonify, current_app
from app.services import google_sheets_service as gs
import datetime

knowledge_bp = Blueprint('knowledge_api', __name__)

def _reload_data():
    """Hàm nội bộ để tải lại dữ liệu và cập nhật vào app context."""
    current_app.initial_sheet_data = gs.get_google_sheet_data()


@knowledge_bp.route('/', methods=['GET'])
def get_all_knowledge():
    """Endpoint để lấy danh sách toàn bộ kiến thức."""
    sheet_data_df = current_app.initial_sheet_data
    if sheet_data_df is None:
        return jsonify({'error': 'Dữ liệu kiến thức chưa được tải.'}), 500
    
    knowledge_list = sheet_data_df.to_dict(orient='records')
    return jsonify(knowledge_list), 200

@knowledge_bp.route('/<item_id>', methods=['GET'])
def get_knowledge_detail(item_id):
    """Endpoint để lấy chi tiết một kiến thức bằng ID."""
    sheet_data_df = current_app.initial_sheet_data
    knowledge_item = gs.get_knowledge_detail_by_id(item_id, sheet_data_df)
    
    if knowledge_item is not None:
        return jsonify(knowledge_item), 200
    else:
        return jsonify({'error': f'Không tìm thấy kiến thức với ID: {item_id}'}), 404


@knowledge_bp.route('/add-knowledge', methods=['POST'])
def add_new_knowledge():
    """Endpoint để thêm một kiến thức mới."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dữ liệu không hợp lệ.'}), 400
    
    # Kiểm tra các trường bắt buộc
    question = data.get('question')
    answer = data.get('answer')
    if not question or not answer:
        return jsonify({'error': 'Câu hỏi và câu trả lời là các trường bắt buộc.'}), 400
        
    # Gọi service để thêm dữ liệu
    success, error_message, new_id = gs.add_knowledge(data)
    
    if success:
        _reload_data() # Tải lại dữ liệu trong bộ nhớ cache
        return jsonify({
            'message': 'Thêm kiến thức mới thành công!',
            'new_id': new_id
        }), 201 # 201 Created là status code phù hợp cho việc tạo mới
    else:
        return jsonify({'error': f'Thêm thất bại: {error_message}'}), 500


@knowledge_bp.route('/<item_id>', methods=['PUT'])
def update_knowledge(item_id):
    """Endpoint để cập nhật kiến thức bằng ID."""
    new_data = request.get_json()
    if not new_data:
        return jsonify({'error': 'Dữ liệu cập nhật không được để trống.'}), 400
    
    success, error_message = gs.update_knowledge_by_id(item_id, new_data)
    
    if success:
        current_app.initial_sheet_data = gs.get_google_sheet_data()
        return jsonify({'message': f'Cập nhật kiến thức ID {item_id} thành công.'}), 200
    else:
        if "Không tìm thấy" in error_message:
            return jsonify({'error': error_message}), 404
        return jsonify({'error': f'Cập nhật thất bại: {error_message}'}), 500

@knowledge_bp.route('/<item_id>', methods=['DELETE'])
def delete_knowledge(item_id):
    """Endpoint để xóa kiến thức bằng ID."""
    success, error_message = gs.delete_knowledge_by_id(item_id)
    
    if success:
        current_app.initial_sheet_data = gs.get_google_sheet_data()
        return jsonify({'message': f'Xóa kiến thức ID {item_id} thành công.'}), 200
    else:
        if "Không tìm thấy" in error_message:
            return jsonify({'error': error_message}), 404
        return jsonify({'error': f'Xóa thất bại: {error_message}'}), 500