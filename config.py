import os
from dotenv import load_dotenv

# # Tải các biến từ file .env
load_dotenv()

class Config:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")
    HISTORY_WORKSHEET_NAME = os.getenv("HISTORY_WORKSHEET_NAME")