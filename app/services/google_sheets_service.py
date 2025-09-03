# /chatbotAI/app/services/google_sheets_service.py
import gspread
import pandas as pd
from config import Config # Import từ file config gốc
import uuid
# Lấy tên sheet từ config
GOOGLE_SHEET_NAME = Config.GOOGLE_SHEET_NAME
HISTORY_WORKSHEET_NAME = Config.HISTORY_WORKSHEET_NAME

def _get_gspread_client():
    """Hàm nội bộ để khởi tạo client, tránh lặp code."""
    return gspread.service_account(filename='credentials.json')

def get_google_sheet_data(sheet_name=GOOGLE_SHEET_NAME):
    """Kết nối và đọc dữ liệu chính."""
    try:
        gc = _get_gspread_client()
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

def get_worksheet(sheet_name, worksheet_name=None):
    """Lấy một worksheet cụ thể."""
    try:
        gc = _get_gspread_client()
        spreadsheet = gc.open(sheet_name)
        if worksheet_name:
            return spreadsheet.worksheet(worksheet_name)
        return spreadsheet.sheet1
    except Exception as e:
        print(f"Lỗi khi lấy worksheet: {e}")
        return None

def find_row_by_id(worksheet, item_id):
    try:
        str_item_id = str(item_id)
        id_column_values = worksheet.col_values(1)
        for i, cell_value in enumerate(id_column_values):
            if str(cell_value) == str_item_id:
                return i + 1
        return None
    except Exception as e:
        print(f"Lỗi khi tìm hàng bằng ID: {e}")
        return None

def add_data_to_google_sheet(data_to_add, sheet_name=GOOGLE_SHEET_NAME):
    try:
        worksheet = get_worksheet(sheet_name)
        if worksheet:
            worksheet.append_row(data_to_add)
            return True, None
        return False, "Không tìm thấy worksheet."
    except Exception as e:
        return False, str(e)

def log_chat_history(data_to_log):
    try:
        worksheet = get_worksheet(GOOGLE_SHEET_NAME, HISTORY_WORKSHEET_NAME)
        if worksheet:
            worksheet.append_row(data_to_log)
            return True, None
        return False, "Không tìm thấy worksheet lịch sử."
    except Exception as e:
        print(f"Lỗi khi ghi lịch sử chat: {e}")
        return False, str(e)


# --- CÁC SERVICE QUẢN LÝ LỊCH SỬ CHAT ---

def get_chat_history_data():
    """Lấy toàn bộ dữ liệu từ worksheet lịch sử chat."""
    try:
        worksheet = get_worksheet(GOOGLE_SHEET_NAME, HISTORY_WORKSHEET_NAME)
        if worksheet:
            history_data = worksheet.get_all_records()
            print(f"Đọc lịch sử chat từ '{HISTORY_WORKSHEET_NAME}' thành công.")
            return history_data
        else:
            print(f"Không tìm thấy worksheet lịch sử: '{HISTORY_WORKSHEET_NAME}'")
            return None
    except gspread.exceptions.WorksheetNotFound:
        print(f"Lỗi: Không tìm thấy trang tính lịch sử '{HISTORY_WORKSHEET_NAME}'.")
        return None
    except Exception as e:
        print(f"Lỗi khi lấy lịch sử chat: {e}")
        return None

def get_chat_history_detail_by_id(chat_id):
    """
    Lấy chi tiết một mục lịch sử chat dựa vào ID.
    Trả về một dictionary nếu tìm thấy, ngược lại trả về None.
    """
    try:
        worksheet = get_worksheet(GOOGLE_SHEET_NAME, HISTORY_WORKSHEET_NAME)
        if not worksheet:
            print(f"Không thể lấy worksheet: {HISTORY_WORKSHEET_NAME}")
            return None

        row_number = find_row_by_id(worksheet, chat_id)
        if not row_number:
            print(f"Không tìm thấy lịch sử chat với ID: {chat_id}")
            return None

        headers = worksheet.row_values(1)
        values = worksheet.row_values(row_number)
        chat_detail = dict(zip(headers, values))
        return chat_detail

    except Exception as e:
        print(f"Lỗi khi lấy chi tiết lịch sử chat: {e}")
        return None

def delete_chat_history_by_id(chat_id):
    """
    Xóa một mục lịch sử chat dựa trên ID.
    Trả về (True, None) nếu thành công, (False, error_message) nếu thất bại.
    """
    try:
        worksheet = get_worksheet(GOOGLE_SHEET_NAME, HISTORY_WORKSHEET_NAME)
        if not worksheet:
            return False, f"Không tìm thấy worksheet lịch sử: {HISTORY_WORKSHEET_NAME}"

        row_to_delete = find_row_by_id(worksheet, chat_id)
        if not row_to_delete:
            return False, f"Không tìm thấy lịch sử chat với ID: {chat_id}"

        worksheet.delete_rows(row_to_delete)
        return True, None
    except Exception as e:
        print(f"Lỗi khi xóa lịch sử chat: {e}")
        return False, str(e)


# --- CÁC SERVICE QUẢN LÝ KIẾN THỨC ---

def get_knowledge_detail_by_id(item_id, dataframe):
    """
    Lấy chi tiết một kiến thức từ DataFrame đã tải.
    Trả về một dictionary nếu tìm thấy, ngược lại trả về None.
    """
    if dataframe is None:
        return None
    try:
        id_column_name = dataframe.columns[0]
        result_df = dataframe[dataframe[id_column_name].astype(str) == str(item_id)]

        if result_df.empty:
            return None
        
        return result_df.iloc[0].to_dict()
    except Exception as e:
        print(f"Lỗi khi tìm kiến thức bằng ID trong DataFrame: {e}")
        return None

def update_knowledge_by_id(item_id, new_data):
    """
    Cập nhật một hàng kiến thức trong Google Sheet.
    new_data là một dictionary chứa các trường cần cập nhật, key là tên cột.
    """
    try:
        worksheet = get_worksheet(GOOGLE_SHEET_NAME)
        print("update",worksheet)
        if not worksheet:
            return False, "Không tìm thấy worksheet kiến thức."

        row_to_update = find_row_by_id(worksheet, item_id)
        if not row_to_update:
            return False, f"Không tìm thấy kiến thức với ID: {item_id}"
        
        headers = worksheet.row_values(1)
        current_values = worksheet.row_values(row_to_update)
        
        updated_values = list(current_values)
        header_to_index = {header: i for i, header in enumerate(headers)}

        for key, value in new_data.items():
            if key in header_to_index:
                index = header_to_index[key]
                if index < len(updated_values):
                    updated_values[index] = value
        
        worksheet.update(f'A{row_to_update}', [updated_values])
        return True, None

    except Exception as e:
        print(f"Lỗi khi cập nhật kiến thức: {e}")
        return False, str(e)

def delete_knowledge_by_id(item_id):
    """
    Xóa một hàng kiến thức dựa trên ID.
    """
    try:
        worksheet = get_worksheet(GOOGLE_SHEET_NAME)
        if not worksheet:
            return False, "Không tìm thấy worksheet kiến thức."
        
        row_to_delete = find_row_by_id(worksheet, item_id)
        if not row_to_delete:
            return False, f"Không tìm thấy kiến thức với ID: {item_id}"
        
        worksheet.delete_rows(row_to_delete)
        return True, None
    except Exception as e:
        print(f"Lỗi khi xóa kiến thức: {e}")
        return False, str(e)
def add_knowledge(knowledge_data):
    """Thêm kiến thức mới, sử dụng UUID cho ID."""
    try:
        new_id = str(uuid.uuid4()) # <-- SỬ DỤNG UUID
        new_data_row = [
            new_id,
            knowledge_data.get('sender', ''),
            knowledge_data.get('question'),
            knowledge_data.get('time_question', ''),
            knowledge_data.get('answer'),
            knowledge_data.get('answering_unit', ''),
            knowledge_data.get('time_answer', '')
        ]
        worksheet = get_worksheet(GOOGLE_SHEET_NAME)
        if not worksheet:
            return False, "Không tìm thấy worksheet kiến thức.", None
        worksheet.append_row(new_data_row)
        return True, None, new_id
    except Exception as e:
        return False, str(e), None  