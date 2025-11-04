# 使用官方 Python 3.11 映像檔
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝依賴
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# 複製整個專案檔案到容器內部
COPY . .

# 預設執行保持容器不結束
CMD ["tail", "-f", "/dev/null"]
