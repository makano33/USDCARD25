# 使用Python 3.9作為基礎映像
FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 複製需要的檔案
COPY requirements.txt .
COPY paga.py .
COPY paga ./paga/

# 安裝依賴項
RUN pip install --no-cache-dir -r requirements.txt

# 設定環境變數（如果需要）
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 暴露連接埠
EXPOSE 8000

# 啟動應用程式
CMD ["uvicorn", "paga:app", "--host", "0.0.0.0", "--port", "8000"]
