# ベースイメージ
FROM python:3.12.4

# 作業ディレクトリを設定
WORKDIR /line_talk_analyzer_backend

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    unzip \
    fonts-noto-cjk \
    libnss3 \
    libatk1.0-0 \
    libpangocairo-1.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcups2 \
    libxss1 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# 依存ライブラリをコピー
COPY requirements.txt /line_talk_analyzer_backend/

# 必要なライブラリをインストール
RUN pip install --no-cache-dir -r /line_talk_analyzer_backend/requirements.txt

# ipykernel をインストール（requirements.txt に含めてもよいが、環境全体に必要なものと区別するため直接 Dockerfile で指定する）
RUN pip install --no-cache-dir ipykernel

# mypy 型チェック用のスタブパッケージを追加
RUN pip install --no-cache-dir types-PyYAML types-requests

# 基本的なディレクトリ構造を作成
RUN mkdir -p /line_talk_analyzer_backend/src

# デフォルトで実行するコマンド
CMD ["/bin/bash"]