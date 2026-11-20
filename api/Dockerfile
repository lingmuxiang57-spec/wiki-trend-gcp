# 1. ベースイメージ：どの Python を土台にするか（例：python の 3.12 の slim 版）
FROM python:3.13-slim

# 2. コンテナ内の作業フォルダ（以降の COPY や RUN はここが基準になる）
WORKDIR /app

# 3. まず依存関係のファイルだけをコピーする（コピー元 → コピー先）
COPY requirements.txt .

# 4. 依存関係をインストールする（--no-cache-dir でイメージを小さくできる）
RUN pip install --no-cache-dir -r requirements.txt

# 5. 残りのアプリのコード（main.py）をコピーする
COPY main.py . 

# 6. 起動コマンド：uvicorn で main.py の app を、0.0.0.0 の $PORT 番で起動する
CMD uvicorn main:app --host 0.0.0.0 --port $PORT