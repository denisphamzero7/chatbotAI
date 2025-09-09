# /chatbotAI/app/services/ai_service.py
import pandas as pd
from openai import OpenAI
from config import Config
import time
import google.generativeai as genai
api_key = Config.DEEPSEEK_API_KEY

def find_relevant_data(question, dataframe, max_rows=5):
    # ... (giữ nguyên code của hàm find_relevant_data)
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
# sửa file answer_question_with_gemini
def answer_question_with_gemini(question, dataframe):
    """
    Gửi câu hỏi và dữ liệu LIÊN QUAN đến Genimi API để nhận câu trả lời.
    """
    total_start_time = time.perf_counter()
    if not api_key:
        return "Lỗi: API key của Genimi chưa được cấu hình."

    # client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    # BƯỚC 1: Tìm dữ liệu liên quan trước khi gửi cho AI
    relevant_data = find_relevant_data(question, dataframe)

    # Nếu không có gì liên quan, dùng toàn bộ dữ liệu. Ngược lại, chỉ dùng dữ liệu liên quan.
    data_to_send = dataframe if relevant_data.empty else relevant_data
    data_string = data_to_send.to_csv(index=False)

    # BƯỚC 2: Sử dụng prompt cải tiến từ ví dụ của bạn
    prompt = f"""
    Dựa vào dữ liệu dưới đây đã được cung cấp:

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
        model = genai.GenerativeModel('gemini-2.0-flash') # Tên model đúng
        
        api_start_time = time.perf_counter()
        print("--- [API_TIMER] Bắt đầu gọi Gemini API... ---")
        
        response = model.generate_content(prompt)
        
        api_end_time = time.perf_counter()
        print(f"--- [API_TIMER] Gemini API phản hồi sau: {api_end_time - api_start_time:.4f} giây ---")
        
        # Xử lý response của Gemini
        answer = response.text.strip()
        total_end_time = time.perf_counter()
        return answer, total_end_time - total_start_time
    except Exception as e:
        print(f"AI Service: Đã xảy ra lỗi khi gọi Gemini API: {e}")
        total_end_time = time.perf_counter()
        return "Đã có lỗi xảy ra khi kết nối tới dịch vụ AI của Google.", total_end_time - total_start_time