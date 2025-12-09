# ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# MeCabとmecab-ipadic-neologdのインストールに必要なパッケージ
RUN apt-get update && apt-get install -y --no-install-recommends \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    git \
    make \
    curl \
    xz-utils \
    file \
    patch \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# mecab-ipadic-neologdのインストール
RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git /tmp/neologd \
    && /tmp/neologd/bin/install-mecab-ipadic-neologd -n -y \
    && rm -rf /tmp/neologd

# MeCabの設定ファイルへのシンボリックリンクを作成
RUN ln -s /etc/mecabrc /usr/local/etc/mecabrc

# 依存ライブラリをコピー
COPY requirements.txt /app/

# 必要なライブラリをインストール
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# アプリケーションコードをコピー
COPY . /app/

# ポート8000を公開
EXPOSE 8000

# FastAPIアプリケーションを起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]