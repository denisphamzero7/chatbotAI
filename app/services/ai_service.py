# /chatbotAI/app/services/ai_service.py
import pandas as pd
from openai import OpenAI
from config import Config

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