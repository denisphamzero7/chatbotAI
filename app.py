import os
import gspread
import pandas as pd
from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime

# --- KHỞI TẠO ỨNG DỤNG FLASK ---
app = Flask(__name__)
CORS(app, origins="*")


if __name__ == '__main__':
    # Chạy ứng dụng web, có thể truy cập từ bất kỳ IP nào trên mạng
    # Truy cập vào http://<your-local-ip>:5000
    app.run(host='0.0.0.0', port=8080, debug=True)
