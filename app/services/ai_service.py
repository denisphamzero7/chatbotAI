# /chatbotAI/app/services/ai_service.py
import pandas as pd
from openai import OpenAI
from config import Config
import time
import google.generativeai as genai
api_key = Config.DEEPSEEK_API_KEY

def find_relevant_data(question, dataframe, max_rows=12):
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
    relevant_data = find_relevant_data(question, dataframe, max_rows=3)

    # Nếu không có gì liên quan, dùng toàn bộ dữ liệu. Ngược lại, chỉ dùng dữ liệu liên quan.
    data_to_send = dataframe if relevant_data.empty else relevant_data
    data_string = data_to_send.to_csv(index=False)

    # BƯỚC 2: Sử dụng prompt cải tiến từ ví dụ của bạn
    prompt = f"""
   **[BẮT ĐẦU PROMPT]**

**Bối cảnh:** Bạn là một trợ lý thú vị phân tích thông tin chuyên nghiệp. Nhiệm vụ của bạn là xử lý và trích xuất dữ liệu một cách chính xác tuyệt đối từ văn bản được cung cấp.

---

**Dữ liệu cung cấp:**

    {data_string}

  **Yêu cầu:**

Dựa **DUY NHẤT** vào nội dung trong phần "Dữ liệu cung cấp" ở trên, hãy soạn câu trả lời cho câu hỏi sau:

`"{question}"`

---

**Các quy tắc bắt buộc:**

1.  **Phạm vi thông tin:** Tuyệt đối không được suy diễn, bình luận thêm, hay sử dụng bất kỳ kiến thức nào bên ngoài "Dữ liệu cung cấp". Mọi thông tin trong câu trả lời phải có thể truy vết được về nguồn dữ liệu.
2.  **Trích dẫn nguồn:** Ngay sau mỗi luận điểm, thông tin, hoặc dữ liệu được trích xuất, bạn **PHẢI** đính kèm nguồn theo định dạng sau:
    `(Nguồn: [Số văn bản], [Loại văn bản] - tham khảo tại [Link văn bản])`
3.  **Xử lý trường hợp thiếu dữ liệu:** Nếu toàn bộ dữ liệu được cung cấp không chứa thông tin để trả lời câu hỏi, hãy trả lời chính xác như sau:
    `"Dữ liệu được cung cấp không đủ để trả lời câu hỏi này."`

---

**Định dạng và văn phong:**

* **Văn phong:** Chuyên nghiệp, rõ ràng, nhưng vẫn giữ sự gần gũi, thân thiện.
* **Cấu trúc:** Trình bày câu trả lời một cách logic, sử dụng gạch đầu dòng (-) cho các ý chính để người đọc dễ theo dõi.
* **Câu kết:** Luôn kết thúc câu trả lời bằng câu: `Hy vọng những thông tin trên hữu ích cho bạn!`

---

**Ví dụ về kết quả mong muốn:**

**Câu hỏi:** *Thủ tục gia hạn giấy phép lao động cho người nước ngoài cần những gì?*

**Câu trả lời mẫu:**
Chào bạn nhé,

Dựa trên các thông tin được cung cấp, thủ tục gia hạn giấy phép lao động cho người nước ngoài bao gồm các yêu cầu sau:

- Người sử dụng lao động cần phải nộp một bộ hồ sơ đề nghị gia hạn giấy phép lao động cho cơ quan có thẩm quyền. `(Nguồn: 123/2025/NĐ-CP, Nghị định - tham khảo tại https://example.com/link-1)`
- Hồ sơ phải được nộp trước ít nhất 5 ngày nhưng không quá 45 ngày trước ngày giấy phép lao động hết hạn. `(Nguồn: 456/2025/TT-BLĐTBXH, Thông tư - tham khảo tại https://example.com/link-2)`

Hy vọng những thông tin trên hữu ích cho bạn!

**[KẾT THÚC PROMPT]**
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