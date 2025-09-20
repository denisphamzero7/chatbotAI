# /chatbotAI/app/services/ai_service.py
import pandas as pd
from config import Config
import time
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- CONFIG & MODEL INITIALIZATION ---
api_key = Config.GEMINI_API_KEY
genai.configure(api_key=api_key)

print("Đang tải model embedding 'bkai-foundation-models/vietnamese-bi-encoder'...")
embedding_model = SentenceTransformer('bkai-foundation-models/vietnamese-bi-encoder')
print("Model embedding đã tải xong!")

gemini_model = genai.GenerativeModel('gemini-2.0-flash')
print("Model Gemini đã sẵn sàng!")

# ✅ SỬA ĐỔI HÀM: NHẬN VÀO `document_embeddings` ĐÃ ĐƯỢC TÍNH SẴN
def find_relevant_data_semantic(question, dataframe, document_embeddings, max_rows=12):
    func_start_time = time.perf_counter()
    print("\n--- [SEMANTIC_TIMER] Bắt đầu tìm kiếm ngữ nghĩa ---")

    if dataframe.empty or document_embeddings is None:
        return pd.DataFrame()

    # Bước 1: Vector hóa CÂU HỎI (chỉ câu hỏi, rất nhanh)
    t1 = time.perf_counter()
    question_embedding = embedding_model.encode([question])[0]
    t2 = time.perf_counter()
    print(f"--- [SEMANTIC_TIMER] Vector hóa câu hỏi: {t2 - t1:.4f} giây ---")

    # Bước 2: Tính toán độ tương đồng (không cần vector hóa tài liệu nữa)
    t3 = time.perf_counter()
    similarities = cosine_similarity([question_embedding], document_embeddings)[0]
    t4 = time.perf_counter()
    print(f"--- [SEMANTIC_TIMER] Tính độ tương đồng: {t4 - t3:.4f} giây ---")

    # Bước 3: Lấy ra các hàng có điểm số cao nhất
    dataframe['similarity'] = similarities
    relevant_df = dataframe.sort_values(by='similarity', ascending=False).head(max_rows)
    relevant_df = relevant_df.drop(columns=['similarity'])

    func_end_time = time.perf_counter()
    print(f"--- [SEMANTIC_TIMER] Tổng thời gian tìm kiếm ngữ nghĩa: {func_end_time - func_start_time:.4f} giây ---")

    return relevant_df

# ✅ SỬA ĐỔI HÀM: NHẬN VÀO `document_embeddings` VÀ TRUYỀN ĐI
def answer_question_with_gemini(question, dataframe, document_embeddings):
    total_start_time = time.perf_counter()
    print(f"\n{'='*20} BẮT ĐẦU XỬ LÝ YÊU CẦU MỚI {'='*20}")

    if not api_key:
        return "Lỗi: API key của Gemini chưa được cấu hình.", 0

    # BƯỚC 1: Tìm dữ liệu liên quan bằng cách sử dụng các embedding đã tính sẵn
    relevant_data = find_relevant_data_semantic(question, dataframe, document_embeddings, max_rows=3)

    # BƯỚC 2: Chuẩn bị dữ liệu để gửi
    t1 = time.perf_counter()
    data_to_send = dataframe if relevant_data.empty else relevant_data
    data_string = data_to_send.to_csv(index=False)
    t2 = time.perf_counter()
    print(f"--- [MAIN_TIMER] Bước 2 - Chuyển đổi DataFrame sang CSV: {t2 - t1:.4f} giây ---")
    print(f"--- [INFO] Số dòng dữ liệu gửi cho AI: {len(data_to_send)} ---")
    
    # BƯỚC 3: Tạo prompt
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
2.  **Trích dẫn nguồn:** Ngay sau mỗi câu trả lời, thông tin, hoặc dữ liệu được trích xuất, bạn **PHẢI** đính kèm nguồn theo định dạng sau:
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

    # BƯỚC 4: Gọi API
    try:
        api_start_time = time.perf_counter()
        print("--- [API_TIMER] Bắt đầu gọi Gemini API... ---")
        
        response = gemini_model.generate_content(prompt)
        
        api_end_time = time.perf_counter()
        print(f"--- [API_TIMER] Gemini API phản hồi sau: {api_end_time - api_start_time:.4f} giây ---")
        
        answer = response.text.strip()
        total_end_time = time.perf_counter()
        total_duration = total_end_time - total_start_time
        print(f"--- [MAIN_TIMER] Tổng thời gian xử lý yêu cầu: {total_duration:.4f} giây ---")
        print(f"{'='*20} KẾT THÚC XỬ LÝ YÊU CẦU {'='*20}\n")
        
        return answer, total_duration
    except Exception as e:
        print(f"AI Service: Đã xảy ra lỗi khi gọi Gemini API: {e}")
        total_end_time = time.perf_counter()
        total_duration = total_end_time - total_start_time
        return "Đã có lỗi xảy ra khi kết nối tới dịch vụ AI của Google.", total_duration