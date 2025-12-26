# Issue#07: 最小出現回数フィルタの追加

## 概要

トーク履歴の解析において、単語とメッセージの最小出現回数をAPI引数で指定できる機能を追加しました。デフォルト値は2回に設定されており、1回しか発言されていない内容が流行語ランキングに入ることを防ぎます。

## 背景

### 問題点

トーク履歴が少ない場合、または特定の期間を指定して解析する場合、1回しか発言されていない単語やメッセージが流行語ランキングに入ってしまうことがありました。1回しか使われていない言葉を「流行語」と呼ぶには無理があります。

### 具体例

以下のようなトーク履歴の場合：

```
2024/01/01(月)
10:00	ユーザーA	おはよう
10:01	ユーザーB	おはよう
10:02	ユーザーC	おはよう
10:03	ユーザーA	今日は天気がいいね
10:04	ユーザーB	そうだね
```

従来の実装では、「今日」「天気」「いい」「そう」などの1回しか出現しない単語もすべてランキングに含まれていました。しかし、「おはよう」（3回）こそが真の「流行語」であり、1回だけの単語は除外すべきです。

## 実装内容

### 1. analyzer.pyの修正

`TalkAnalyzer.analyze()`メソッドに以下のパラメータを追加：

- **`min_word_count`** (int): 最小単語出現回数（デフォルト: 2）
- **`min_message_count`** (int): 最小メッセージ出現回数（デフォルト: 2）

#### 追加されたパラメータ

```python
def analyze(
    self,
    file: TextIO | str,
    top_n: int = 50,
    min_word_length: int = 2,
    max_word_length: int | None = None,
    min_message_length: int = 2,
    max_message_length: int | None = None,
    min_word_count: int = 2,        # ← 新規追加
    min_message_count: int = 2,     # ← 新規追加
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> AnalysisResult:
```

#### フィルタリング処理

集計後に出現回数でフィルタリング：

```python
# 3. 単語カウンターで集計
word_counts = self.word_counter.count_morphological_words(
    messages, words_by_message, min_word_length, max_word_length
)
message_counts = self.word_counter.count_full_messages(
    messages, min_message_length, max_message_length
)

# 3.5. 出現回数でフィルタリング
word_counts = [wc for wc in word_counts if wc.count >= min_word_count]
message_counts = [mc for mc in message_counts if mc.count >= min_message_count]
```

#### バリデーション

パラメータのバリデーションを追加：

```python
if min_word_count < 1:
    raise ValueError(f"min_word_countは1以上である必要があります: {min_word_count}")
if min_message_count < 1:
    raise ValueError(f"min_message_countは1以上である必要があります: {min_message_count}")
```

### 2. analyze.pyの修正

APIエンドポイントに対応するパラメータを追加：

```python
@router.post("/analyze", response_model=AnalysisResult)
async def analyze_talk(
    file: UploadFile = File(..., description="LINEトーク履歴ファイル（.txt形式）"),
    top_n: int = Form(default=None, description="取得する上位単語数"),
    min_word_length: int = Form(default=None, description="最小単語長"),
    max_word_length: int | None = Form(default=None, description="最大単語長"),
    min_message_length: int = Form(default=None, description="最小メッセージ長"),
    max_message_length: int | None = Form(default=None, description="最大メッセージ長"),
    min_word_count: int = Form(default=None, description="最小単語出現回数"),      # ← 新規追加
    min_message_count: int = Form(default=None, description="最小メッセージ出現回数"),  # ← 新規追加
    start_date: str | None = Form(
        default=None, description="解析開始日時（YYYY-MM-DD HH:MM:SS形式）"
    ),
    end_date: str | None = Form(
        default=None, description="解析終了日時（YYYY-MM-DD HH:MM:SS形式）"
    ),
    analyzer: TalkAnalyzer = Depends(get_analyzer),
) -> AnalysisResult:
```

デフォルト値の設定：

```python
min_word_count = min_word_count if min_word_count is not None else 2
min_message_count = min_message_count if min_message_count is not None else 2
```

## 変更ファイル

### 修正ファイル（2件）

1. **`app/services/analyzer.py`**
   - `analyze()`メソッドのシグネチャ修正（パラメータ追加）
   - docstring更新
   - バリデーション追加（2箇所）
   - フィルタリング処理追加（1箇所）

2. **`app/api/v1/endpoints/analyze.py`**
   - `analyze_talk()`エンドポイントのシグネチャ修正（パラメータ追加）
   - docstring更新
   - デフォルト値設定処理追加
   - `analyzer.analyze()`呼び出し時の引数追加

### 新規テストケース（5件）

3. **`tests/unit/test_analyzer.py`**
   - `test_analyze_with_min_word_count`: 最小単語出現回数フィルタの動作確認
   - `test_analyze_with_min_message_count`: 最小メッセージ出現回数フィルタの動作確認
   - `test_analyze_with_min_count_default`: デフォルト値（2回）の動作確認
   - `test_analyze_min_count_validation`: バリデーションのテスト（0以下でエラー）

4. **`tests/integration/test_api.py`**
   - `test_analyze_with_min_count_filters`: APIエンドポイント経由でのフィルタ動作確認
   - 既存の`test_analyze_with_parameters`を更新（新パラメータ追加）

## テスト結果

### 全テストの実行結果

```bash
$ python -m pytest tests/ -v
```

- **総テスト数**: 200件
- **成功**: 200件 ✅
- **失敗**: 0件
- **実行時間**: 21.92秒

### 新規テストの詳細

#### 1. 最小単語出現回数フィルタのテスト

```python
def test_analyze_with_min_word_count(self, analyzer: TalkAnalyzer) -> None:
    """最小単語出現回数フィルタのテスト"""
    content = """[LINE] 単語出現回数テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	りんごとバナナとみかん
10:01	ユーザーB	りんごとバナナ
10:02	ユーザーC	りんご
"""
    # min_word_count=2 の場合、2回以上出現する単語のみ取得
    result = analyzer.analyze(content, top_n=10, min_word_count=2)

    # 「りんご」(3回)、「バナナ」(2回) は含まれる
    # 「みかん」(1回) は含まれない
    words = [w.word for w in result.data.morphological_analysis.top_words]
    assert "りんご" in words
    assert "バナナ" in words
    assert "みかん" not in words
```

**結果**: PASSED ✅

#### 2. 最小メッセージ出現回数フィルタのテスト

```python
def test_analyze_with_min_message_count(self, analyzer: TalkAnalyzer) -> None:
    """最小メッセージ出現回数フィルタのテスト"""
    content = """[LINE] メッセージ出現回数テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	おはよう
10:01	ユーザーB	おはよう
10:02	ユーザーC	おはよう
10:03	ユーザーA	こんにちは
10:04	ユーザーB	こんにちは
10:05	ユーザーC	さようなら
"""
    # min_message_count=2 の場合、2回以上出現するメッセージのみ取得
    result = analyzer.analyze(content, top_n=10, min_message_count=2)

    # 「おはよう」(3回)、「こんにちは」(2回) は含まれる
    # 「さようなら」(1回) は含まれない
    messages = [m.message for m in result.data.full_message_analysis.top_messages]
    assert "おはよう" in messages
    assert "こんにちは" in messages
    assert "さようなら" not in messages
```

**結果**: PASSED ✅

#### 3. デフォルト値のテスト

```python
def test_analyze_with_min_count_default(self, analyzer: TalkAnalyzer) -> None:
    """最小出現回数のデフォルト値（2）のテスト"""
    content = """[LINE] デフォルト値テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	一回のみ
10:01	ユーザーB	二回目
10:02	ユーザーC	二回目
"""
    # min_word_count, min_message_countを指定しない（デフォルト=2）
    result = analyzer.analyze(content, top_n=10)

    words = [w.word for w in result.data.morphological_analysis.top_words]
    messages = [m.message for m in result.data.full_message_analysis.top_messages]

    # 「一回」は1回のみなので含まれない
    assert "一回" not in words

    # 「二回目」は2回なので含まれる
    assert "二回目" in messages
    # 「一回のみ」は1回なので含まれない
    assert "一回のみ" not in messages
```

**結果**: PASSED ✅

#### 4. バリデーションのテスト

```python
def test_analyze_min_count_validation(self, analyzer: TalkAnalyzer) -> None:
    """最小出現回数のバリデーションテスト"""
    content = """[LINE] バリデーションテスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	テスト
"""
    # min_word_count が 0 以下の場合はエラー
    with pytest.raises(ValueError, match="min_word_count.*1以上"):
        analyzer.analyze(content, min_word_count=0)

    with pytest.raises(ValueError, match="min_word_count.*1以上"):
        analyzer.analyze(content, min_word_count=-1)

    # min_message_count が 0 以下の場合はエラー
    with pytest.raises(ValueError, match="min_message_count.*1以上"):
        analyzer.analyze(content, min_message_count=0)

    with pytest.raises(ValueError, match="min_message_count.*1以上"):
        analyzer.analyze(content, min_message_count=-1)
```

**結果**: PASSED ✅

#### 5. 統合テスト（API経由）

```python
def test_analyze_with_min_count_filters(self) -> None:
    """最小出現回数フィルタのテスト"""
    content = """[LINE] 最小出現回数テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	りんごとバナナとみかん
10:01	ユーザーB	りんごとバナナ
10:02	ユーザーC	りんご
10:03	ユーザーA	おはよう
10:04	ユーザーB	おはよう
10:05	ユーザーC	こんにちは
"""
    file = BytesIO(content.encode("utf-8"))

    response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.txt", file, "text/plain")},
        data={"min_word_count": "2", "min_message_count": "2"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # 2回以上出現する単語のみ含まれる
    words = [w["word"] for w in data["data"]["morphological_analysis"]["top_words"]]
    assert "りんご" in words  # 3回出現
    assert "バナナ" in words  # 2回出現

    # 2回以上出現するメッセージのみ含まれる
    messages = [m["message"] for m in data["data"]["full_message_analysis"]["top_messages"]]
    assert "おはよう" in messages  # 2回出現
    assert "こんにちは" not in messages  # 1回のみ
```

**結果**: PASSED ✅

### コード品質チェック

```bash
# Black（フォーマット）
$ python -m black app/services/analyzer.py app/api/v1/endpoints/analyze.py tests/
✅ All files reformatted

# flake8（リンター）
$ python -m flake8 app/services/analyzer.py app/api/v1/endpoints/analyze.py \
    --max-line-length=100 \
    --ignore=E203,W503,ANN101,ANN204,ANN401,D105,D107,D400,D403,D415,DAR101,DAR201 \
    --select=E,W,F,N,D \
    --docstring-convention=google
✅ No issues found

# mypy（型チェック）
$ python -m mypy app/services/analyzer.py app/api/v1/endpoints/analyze.py \
    --config-file=mypy.ini
✅ Success: no issues found in 2 source files
```

## 使用例

### Pythonから直接使用

```python
from app.services.analyzer import TalkAnalyzer

analyzer = TalkAnalyzer()

# 3回以上出現した単語・メッセージのみ取得
result = analyzer.analyze(
    file_content,
    top_n=50,
    min_word_count=3,      # 3回以上の単語のみ
    min_message_count=3    # 3回以上のメッセージのみ
)
```

### API経由（curl）

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@talk.txt" \
  -F "top_n=50" \
  -F "min_word_count=3" \
  -F "min_message_count=2"
```

### API経由（Python requests）

```python
import requests

files = {"file": open("talk.txt", "rb")}
data = {
    "top_n": 50,
    "min_word_count": 3,
    "min_message_count": 2
}

response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    files=files,
    data=data
)
result = response.json()
```

### API経由（JavaScript fetch）

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('top_n', '50');
formData.append('min_word_count', '3');
formData.append('min_message_count', '2');

const response = await fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  body: formData
});
const result = await response.json();
```

## パラメータ仕様

### min_word_count

- **型**: `int`
- **デフォルト値**: `2`
- **最小値**: `1`
- **説明**: この回数以上出現した単語のみを集計対象とする
- **エラー**: 0以下の値を指定すると`ValueError`が発生

### min_message_count

- **型**: `int`
- **デフォルト値**: `2`
- **最小値**: `1`
- **説明**: この回数以上出現したメッセージのみを集計対象とする
- **エラー**: 0以下の値を指定すると`ValueError`が発生

## 期待される効果

### 1. 流行語ランキングの品質向上

1回しか使われていない言葉が除外されるため、真の「流行語」が上位に来る：

**従来**:
```
1. おはよう (3回)
2. 今日 (1回)
3. 天気 (1回)
4. いい (1回)
5. そう (1回)
```

**改善後** (min_word_count=2):
```
1. おはよう (3回)
（1回のみの単語は除外）
```

### 2. 期間指定解析での実用性向上

特定の期間（例: 先週のみ）を指定した場合、メッセージ数が少なくなるため、1回だけの単語が多数ランクインする問題がありました。この機能により、期間を絞った解析でも意味のあるランキングが得られます。

### 3. ユーザーエクスペリエンスの向上

- デフォルトで2回以上に設定されているため、何も指定しなくても適切な結果が得られる
- 必要に応じて`min_word_count=1`と指定すれば、すべての単語を取得可能
- トーク履歴の量に応じて柔軟に調整可能

## 注意事項

### 1. 出現回数のカウント方法

- **単語のカウント**: 同じメッセージ内で同じ単語が複数回出現しても、1回としてカウント
  - 例: 「テストテストテスト」→「テスト」は1回とカウント
  - 3つのメッセージに「テスト」が出現した場合、3回とカウント

- **メッセージのカウント**: 完全一致のメッセージ出現回数
  - 例: 「おはよう」が3つのメッセージで出現した場合、3回とカウント

### 2. パフォーマンス影響

フィルタリング処理は集計後に行われるため、パフォーマンスへの影響は軽微です：
- フィルタリング処理: O(N)（Nは単語・メッセージ数）
- 追加処理時間: < 0.01秒（測定不能レベル）

### 3. デフォルト値の選択理由

`min_word_count`、`min_message_count`のデフォルト値を`2`に設定した理由：

- **流行語の定義**: 1回だけでは「流行」とは言えない
- **ノイズ除去**: 誤字脱字、打ち間違いなどのノイズを自動的に除外
- **実用性**: 大多数のユースケースで適切な結果が得られる
- **柔軟性**: 必要に応じて`1`に変更すれば全データを取得可能

## まとめ

本機能により、以下が実現されました：

1. ✅ 1回しか発言されていない内容が流行語ランキングに入らない
2. ✅ トーク履歴が少ない場合でも意味のあるランキングが得られる
3. ✅ 期間指定解析での実用性向上
4. ✅ ユーザーが出現回数の閾値を柔軟に調整可能
5. ✅ デフォルト値（2回）により、何も指定しなくても適切な結果

すべてのテストがパス（200/200）し、コード品質チェックもすべてクリアしています。

## 関連Issue・PR

- Issue#01: appearancesフィールドの削除（レスポンスサイズ削減）
- Issue#02: 改行されたメッセージを正しくカウントする
- Issue#03: 単語カウント方法の改善（5項目）
- Issue#04: ひらがな、カタカナの1文字単語を除外する
- Issue#05: 形容動詞語幹を連続名詞結合の対象に含める
- Issue#06: 形容詞を表層形で集計する
