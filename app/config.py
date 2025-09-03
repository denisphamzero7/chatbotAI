import os
from dotenv import load_dotenv

# # Tải các biến từ file .env
load_dotenv()

class Config:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
    HISTORY_WORKSHEET_NAME = os.getenv("HISTORY_WORKSHEET_NAME")
    WORK_SHEET_PHUONG_XA= os.getenv("WORK_SHEET_PHUONG_XA")
    WORK_SHEET_CO_QUAN= os.getenv("WORK_SHEET_PHUONG_XA")
    KNOWLEDGE_WORKSHEET_STR = os.getenv("KNOWLEDGE_WORKSHEET_NAMES", "")

    # Tách chuỗi đó thành một danh sách các tên sheet
    KNOWLEDGE_WORKSHEET_NAMES = [name.strip() for name in KNOWLEDGE_WORKSHEET_STR.split(',') if name.strip()]