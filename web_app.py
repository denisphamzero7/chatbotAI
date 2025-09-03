import os
import gspread
import pandas as pd
from openai import OpenAI
from flask import Flask, request, jsonify
import datetime
from threading import Thread
# --- KHỞI TẠO ỨNG DỤNG FLASK ---
app = Flask(__name__)

# --- CẤU HÌNH ---
# Lấy API key từ biến môi trường để bảo mật hơn
# Bạn nên tạo file .env và dùng thư viện python-dotenv
# DEEPSEEK_API_KEY="sk-..."
api_key = os.getenv("DEEPSEEK_API_KEY")

GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
HISTORY_WORKSHEET_NAME = os.getenv("HISTORY_WORKSHEET_NAME")

# --- PHẦN 1: CÁC HÀM LOGIC LÕI (TỪ MÃ GỐC CỦA BẠN) ---

def get_google_sheet_data(sheet_name):
    """Kết nối với Google Sheets và đọc dữ liệu vào một DataFrame."""
    try:
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.sheet1
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        print(f"Đọc dữ liệu từ Google Sheet '{sheet_name}' thành công.")
        return df
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Lỗi: Không tìm thấy bảng tính '{sheet_name}'.")
        return None
    except Exception as e:
        print(f"Đã xảy ra lỗi khi đọc Google Sheet: {e}")
        return None

def get_worksheet(sheet_name, worksheet_index=0):
    """Hàm trợ giúp để lấy đối tượng worksheet."""
    try:
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open(sheet_name)
        # Lấy sheet đầu tiên theo index
        worksheet = spreadsheet.get_worksheet(worksheet_index)
        return worksheet
    except Exception as e:
        print(f"Lỗi khi lấy worksheet: {e}")
        return None

def find_row_by_id(worksheet, item_id):
    """Tìm số hàng dựa trên ID ở cột đầu tiên (cột A)."""
    try:
        # gspread find() không hoạt động tin cậy với số, nên chuyển tất cả về chuỗi
        str_item_id = str(item_id)
        id_column_values = worksheet.col_values(1)
        for i, cell_value in enumerate(id_column_values):
            if str(cell_value) == str_item_id:
                return i + 1  # Số hàng trong Google Sheet bắt đầu từ 1
        return None # Không tìm thấy
    except Exception as e:
        print(f"Lỗi khi tìm hàng bằng ID: {e}")
        return None

def find_relevant_data(question, dataframe, max_rows=5):
    """Tìm các hàng trong DataFrame có liên quan nhất đến câu hỏi."""
    question_words = set(question.lower().split())
    dataframe['search_col'] = dataframe.apply(lambda row: ' '.join(row.astype(str)).lower(), axis=1)

    def relevance_score(row_text):
        return len(question_words.intersection(row_text.split()))

    dataframe['relevance'] = dataframe['search_col'].apply(relevance_score)
    relevant_df = dataframe.sort_values(by='relevance', ascending=False).head(max_rows)
    relevant_df = relevant_df.drop(columns=['search_col', 'relevance'])

    if relevant_df.empty or dataframe.loc[relevant_df.index]['relevance'].sum() == 0:
        return pd.DataFrame()
    return relevant_df

def add_data_to_google_sheet(sheet_name, data_to_add):
    """Thêm một hàng dữ liệu mới vào cuối Google Sheet."""
    try:
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open(sheet_name)
        worksheet = spreadsheet.sheet1
        worksheet.append_row(data_to_add)
        return True, None
    except Exception as e:
        return False, str(e)

def log_chat_history(spreadsheet_name, worksheet_name, data_to_log):
    """Ghi lịch sử chat vào một trang tính cụ thể."""
    try:
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open(spreadsheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        worksheet.append_row(data_to_log)
        return True, None
    except Exception as e:
        print(f"Lỗi khi ghi lịch sử chat: {e}")
        return False, str(e)

def answer_question_with_deepseek(question, dataframe):
    """
    Gửi câu hỏi và dữ liệu LIÊN QUAN đến DeepSeek API để nhận câu trả lời.
    """
    if not api_key:
        return "Lỗi: API key của DeepSeek chưa được cấu hình."

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    # BƯỚC 1: Tìm dữ liệu liên quan trước khi gửi cho AI
    relevant_data = find_relevant_data(question, dataframe)

    # Nếu không có gì liên quan, dùng toàn bộ dữ liệu. Ngược lại, chỉ dùng dữ liệu liên quan.
    data_to_send = dataframe if relevant_data.empty else relevant_data
    data_string = data_to_send.to_csv(index=False)

    # BƯỚC 2: Sử dụng prompt cải tiến từ ví dụ của bạn
    prompt = f"""
    Dựa vào dữ liệu dưới đây từ một bảng tính:

    {data_string}

    Hãy trả lời câu hỏi sau: "{question}"

    **Yêu cầu quan trọng:**
    - CHỈ sử dụng thông tin từ dữ liệu được cung cấp trong bảng tính trên.
    - KHÔNG sử dụng bất kỳ kiến thức ngoài nào khác.
    - Nếu dữ liệu không đủ để trả lời, hãy nói rõ: "Dữ liệu không đủ để trả lời câu hỏi này."
    - Giọng văn thân thiện, rõ ràng và chuyên nghiệp.
    - Ưu tiên sắp xếp thông tin theo cấu trúc dễ đọc (ví dụ: gạch đầu dòng nếu cần).
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý AI chuyên nghiệp, phân tích dữ liệu từ Google Sheet và trả lời câu hỏi bằng tiếng Việt."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Đã xảy ra lỗi khi gọi DeepSeek API: {e}")
        return "Đã có lỗi xảy ra khi kết nối tới dịch vụ AI."


def log_in_background(app_context, spreadsheet_name, worksheet_name, data_to_log):
    """Hàm này sẽ chạy trên một thread riêng để không chặn request chính."""
    with app_context:
        try:
            gc = gspread.service_account(filename='credentials.json')
            spreadsheet = gc.open(spreadsheet_name)
            worksheet = spreadsheet.worksheet(worksheet_name)
            worksheet.append_row(data_to_log)
            print("Lịch sử chat đã được ghi lại trong nền.")
        except Exception as e:
            print(f"Lỗi khi ghi lịch sử chat trong nền: {e}")

# --- PHẦN 2: TẢI DỮ LIỆU KHI KHỞI ĐỘNG SERVER ---

# Đọc dữ liệu một lần duy nhất để tối ưu hiệu suất
sheet_data_df = get_google_sheet_data(GOOGLE_SHEET_NAME)

# --- PHẦN 3: CÁC API ENDPOINT ---

@app.route('/ask', methods=['POST'])
def ask():
    """Endpoint nhận câu hỏi, xử lý và trả về câu trả lời."""
    if sheet_data_df is None:
        return jsonify({'error': f'Không thể tải dữ liệu từ Google Sheet "{GOOGLE_SHEET_NAME}".'}), 500

    data = request.get_json()
    if not data or 'question' not in data:
        return jsonify({'error': 'Request phải là JSON và chứa key "question".'}), 400

    question = data['question']
    if not question:
        return jsonify({'error': 'Câu hỏi không được để trống.'}), 400

    print(f"Nhận được câu hỏi: {question}")

    # Lấy câu trả lời từ AI
    answer = answer_question_with_deepseek(question, sheet_data_df.copy()) # Dùng .copy() để tránh thay đổi dataframe gốc

    # Ghi lại lịch sử với ID duy nhất
    chat_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f") # Tạo ID mới
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Thêm ID vào đầu danh sách dữ liệu để ghi lại
    log_data = [chat_id, timestamp, question, answer] 
    # --- TỐI ƯU HÓA: GỌI HÀM GHI LOG TRONG MỘT THREAD RIÊNG ---
    thread = Thread(target=log_in_background, args=(app.app_context(), GOOGLE_SHEET_NAME, HISTORY_WORKSHEET_NAME, log_data))
    thread.start()

    return jsonify({'answer': answer})

@app.route('/add-knowledge', methods=['POST'])
def add_knowledge():
    """Endpoint để thêm kiến thức mới vào Google Sheet."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dữ liệu không hợp lệ.'}), 400

    # Lấy dữ liệu từ request, khớp với các cột trong form Streamlit của bạn
    form_question = data.get('question')
    form_answer = data.get('answer')
    form_sender = data.get('sender', '') # Tùy chọn
    form_time_question = data.get('time_question', '')
    form_answering_unit = data.get('answering_unit', '')
    form_time_answer = data.get('time_answer', '')

    if not form_question or not form_answer:
        return jsonify({'error': 'Câu hỏi và câu trả lời là bắt buộc.'}), 400
    new_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    # Đảm bảo thứ tự các cột khớp với file Google Sheet
    new_data_row = [
        new_id,
        form_sender,
        form_question,
        form_time_question,
        form_answer,
        form_answering_unit,
        form_time_answer
    ]

    success, error_message = add_data_to_google_sheet(GOOGLE_SHEET_NAME, new_data_row)

    if success:
        # Tùy chọn: Tải lại dữ liệu sau khi thêm mới
        global sheet_data_df
        sheet_data_df = get_google_sheet_data(GOOGLE_SHEET_NAME)
        return jsonify({'message': 'Thêm kiến thức mới thành công!'}), 201
    else:
        return jsonify({'error': f'Thêm thất bại: {error_message}'}), 500

@app.route('/update-knowledge', methods=['PUT'])
def update_knowledge():
    """Endpoint để sửa một hàng kiến thức dựa trên ID. Chỉ cập nhật các trường được cung cấp."""
    data = request.get_json()
    item_id = data.get('id')
    new_data = data.get('new_data')

    if not item_id or not new_data:
        return jsonify({'error': 'Cần cung cấp "id" và "new_data".'}), 400

    worksheet = get_worksheet(GOOGLE_SHEET_NAME)
    if worksheet is None:
        return jsonify({'error': 'Không thể kết nối tới Google Sheet.'}), 500

    row_to_update = find_row_by_id(worksheet, item_id)
    if not row_to_update:
        return jsonify({'error': f'Không tìm thấy kiến thức với ID: "{item_id}"'}), 404

    try:
        # Lấy dữ liệu hiện tại của hàng
        current_row_values = worksheet.row_values(row_to_update)
        
        # Tạo một bản sao để cập nhật
        updated_row_values = list(current_row_values)

        # Định nghĩa mapping giữa key trong JSON và vị trí cột (index)
        # Bỏ qua cột ID (index 0) vì nó không thay đổi
        column_mapping = {
            'sender': 1,
            'question': 2,
            'time_question': 3,
            'answer': 4,
            'answering_unit': 5,
            'time_answer': 6
        }

        # Lặp qua các key trong new_data và cập nhật giá trị tương ứng
        for key, index in column_mapping.items():
            if key in new_data:
                # Đảm bảo index không vượt quá độ dài của hàng hiện tại
                if index < len(updated_row_values):
                    updated_row_values[index] = new_data[key]
                else:
                    # Xử lý trường hợp hàng hiện tại có ít cột hơn dự kiến
                    # Bổ sung các giá trị rỗng cho đến khi đạt index mong muốn
                    while len(updated_row_values) <= index:
                        updated_row_values.append('')
                    updated_row_values[index] = new_data[key]
        
        # Cập nhật cả hàng bằng cell range
        worksheet.update(f'A{row_to_update}', [updated_row_values])
        
        global sheet_data_df
        sheet_data_df = get_google_sheet_data(GOOGLE_SHEET_NAME) # Tải lại dữ liệu
        return jsonify({'message': f'Cập nhật kiến thức thành công cho ID: "{item_id}"'}), 200
    except Exception as e:
        return jsonify({'error': f'Cập nhật thất bại: {e}'}), 500



# --- MỚI: API Xóa kiến thức bằng ID ---
@app.route('/delete-knowledge/<item_id>', methods=['DELETE'])
def delete_knowledge(item_id):
    """Endpoint để xóa một hàng kiến thức dựa trên ID."""
    if not item_id:
        return jsonify({'error': 'Cần cung cấp ID để xóa.'}), 400

    worksheet = get_worksheet(GOOGLE_SHEET_NAME)
    if worksheet is None:
        return jsonify({'error': 'Không thể kết nối tới Google Sheet.'}), 500

    row_to_delete = find_row_by_id(worksheet, item_id)
    if not row_to_delete:
        return jsonify({'error': f'Không tìm thấy kiến thức với ID: "{item_id}"'}), 404

    try:
        worksheet.delete_rows(row_to_delete)
        global sheet_data_df
        sheet_data_df = get_google_sheet_data(GOOGLE_SHEET_NAME) # Tải lại dữ liệu
        return jsonify({'message': f'Xóa kiến thức thành công cho ID: "{item_id}"'}), 200
    except Exception as e:
        return jsonify({'error': f'Xóa thất bại: {e}'}), 500
#--- MỚI: Lấy danh sách lịch sử chat ---
@app.route('/history-chat', methods=['GET'])
def get_log_chat():
    """Lấy danh sách toàn bộ lịch sử chat."""
    try:
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
        worksheet = spreadsheet.worksheet(HISTORY_WORKSHEET_NAME)
        history_data = worksheet.get_all_records()
        return jsonify(history_data), 200
    except gspread.exceptions.WorksheetNotFound:
        return jsonify({'error': f'Không tìm thấy trang tính lịch sử "{HISTORY_WORKSHEET_NAME}".'}), 404
    except Exception as e:
        return jsonify({'error': f'Lấy lịch sử chat thất bại: {e}'}), 500
  

@app.route('/history-chat/<chat_id>', methods=['GET'])
def get_chat_detail(chat_id):
    """Lấy chi tiết một cuộc trò chuyện trong lịch sử dựa trên ID."""
    if not chat_id:
        return jsonify({'error': 'Cần cung cấp chat_id.'}), 400

    try:
        gc = gspread.service_account(filename='credentials.json')
        spreadsheet = gc.open(GOOGLE_SHEET_NAME)
        worksheet = spreadsheet.worksheet(HISTORY_WORKSHEET_NAME)
        if worksheet is None:
            return jsonify({'error': f'Không tìm thấy trang tính lịch sử "{HISTORY_WORKSHEET_NAME}".'}), 404
        
        # Tìm hàng dựa trên chat_id
        row_number = find_row_by_id(worksheet, chat_id)
        
        if not row_number:
            return jsonify({'error': f'Không tìm thấy lịch sử chat với ID: "{chat_id}"'}), 404
        
        # Lấy giá trị của hàng và tiêu đề
        headers = worksheet.row_values(1)
        values = worksheet.row_values(row_number)
        
        # Kết hợp tiêu đề và giá trị thành một dictionary để dễ đọc
        chat_detail = dict(zip(headers, values))
        
        return jsonify(chat_detail), 200

    except Exception as e:
        return jsonify({'error': f'Lấy chi tiết lịch sử chat thất bại: {e}'}), 500
# --- PHẦN 4: CHẠY ỨNG DỤNG ---

if __name__ == '__main__':
    # Chạy ứng dụng web, có thể truy cập từ bất kỳ IP nào trên mạng
    # Truy cập vào http://<your-local-ip>:5000
    app.run(host='0.0.0.0', port=5000, debug=True)
