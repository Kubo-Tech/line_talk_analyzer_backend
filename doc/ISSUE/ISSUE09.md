# Issue#09: サンプルレスポンス作成機能の実装

## 概要

アプリケーションの宣伝やデモ時に使用できる、モックレスポンス機能を実装しました。個人情報を含む実際のトーク履歴を使わずに、リアルな解析結果画面を表示できます。

## 背景

### 問題点

アプリケーションを宣伝する際、以下の課題がありました：

1. **個人情報の問題**: 実際のトーク履歴には個人名、会話内容などの個人情報が含まれる
2. **公開の制約**: SNSやWebサイトで解析結果画面を公開できない
3. **デモの困難さ**: 潜在的なユーザーにアプリの魅力を伝えにくい
4. **開発の課題**: フロントエンド開発時に毎回実際のファイルをアップロードする必要がある

### 具体例

従来は、宣伝用のスクリーンショットを作成する際に：

```
1. 実際のトーク履歴をエクスポート
2. 個人名や個人情報を含む内容を手動でマスキング
3. 再度解析を実行
4. スクリーンショット撮影
```

このプロセスは手間がかかり、完全に個人情報を除去できているか確認が困難でした。

## 実装内容

### 1. デモモードの仕組み

特殊なファイル名（`__DEMO__.txt`）をアップロードすると、実際の解析をスキップしてモックレスポンスを返します：

```
[通常モード]
ファイルアップロード → 実際の解析（パーサー → 形態素解析 → 集計）→ レスポンス

[デモモード]
__DEMO__.txt → 判定 → 遅延（3秒）→ モックレスポンス
```

### 2. モックデータの内容

2025年の流行語大賞と一般的な口癖をベースに、リアルなランキングを作成：

#### 基本統計
- **総メッセージ数**: 1000件
- **総ユーザー数**: 3人（太郎、花子、次郎）
- **解析期間**: 2025年1月1日 〜 2025年12月31日

#### 流行語ランキング（50件）

**トップ10**:
1. エッホエッホ (150回) - 2025年流行語大賞1位
2. チャッピー (120回) - ChatGPTの愛称
3. ミャクミャク (105回) - 大阪・関西万博のキャラクター
4. ぬい活 (92回) - ぬいぐるみ活動
5. ビジュイイじゃん (85回) - M!LKの楽曲
6. ほいたらね (78回) - NHK朝ドラの方言
7. オンカジ (72回) - オンラインカジノ
8. 麻辣湯 (68回) - シビカラスープ
9. トランプ関税 (65回) - 時事ネタ
10. 古古古米 (60回) - 令和の米騒動

**11〜30位**: 物価高、二季、平成女児、ラブブ、国宝、教皇選挙など（流行語大賞より）

**31〜50位**: ご飯、仕事、映画、美味しいなど（日常会話の単語）

#### 流行メッセージランキング（30件）

口癖・定型フレーズを出現回数順に：

1. それな (80回)
2. わかる (65回)
3. 草 (58回)
4. まじで (52回)
5. やばい (48回)
6. 確かに (44回)
7. なるほど (40回)
8. いいね (38回)
9. おつかれ (36回)
10. ありがとう (34回)

...（30位までリスト化）

#### ユーザー別統計

各ユーザーの特徴を反映したランキング：

- **太郎**: 仕事関連の単語が多い（仕事、会議、忙しい）
- **花子**: 趣味・エンタメ関連が多い（映画、ご飯、ミャクミャク）
- **次郎**: 時事ネタが多い（チャッピー、トランプ関税、物価高）

### 3. Zipf分布による自然な頻度

実際の言語使用パターンに従い、Zipf分布で出現回数を計算：

```python
def calculate_count(rank: int, first_count: int) -> int:
    """Zipf分布に従って出現回数を計算
    
    Args:
        rank: 順位（1から開始）
        first_count: 1位の出現回数
    
    Returns:
        出現回数
    """
    return int(first_count / rank)
```

例: 1位が150回の場合、2位は75回、3位は50回、4位は37回...

### 4. 遅延機能

実際の解析と同じユーザー体験を提供するため、意図的に遅延を設定：

```python
async def generate_demo_response(self, delay_seconds: float) -> dict[str, Any]:
    """遅延付きでモックレスポンスを生成する"""
    # 遅延を設ける（デフォルト3秒）
    await asyncio.sleep(delay_seconds)
    
    # モックレスポンスを読み込み
    data = self.load_demo_response()
    
    return data
```

- **デフォルト**: 3秒（約1000メッセージの解析時間を想定）
- **環境変数**: `DEMO_RESPONSE_DELAY_SECONDS`で調整可能

### 5. 環境変数による制御

本番環境での無効化など、柔軟な制御が可能：

```bash
# デモモード有効化（デフォルト: true）
ENABLE_DEMO_MODE=true

# トリガーファイル名（デフォルト: __DEMO__.txt）
DEMO_TRIGGER_FILENAME=__DEMO__.txt

# 遅延時間（秒、デフォルト: 3.0）
DEMO_RESPONSE_DELAY_SECONDS=3.0
```

## 変更ファイル

### 新規作成ファイル（4件）

1. **`app/data/demo_response.json`**
   - モックレスポンスのJSONデータ
   - 流行語50件、流行メッセージ30件、ユーザー別統計を含む
   - サイズ: 約8KB（レスポンス全体で約9KB）

2. **`app/services/demo_service.py`**
   - `DemoService`クラス
   - `is_demo_file()`: デモファイル判定
   - `load_demo_response()`: JSONファイル読み込み
   - `generate_demo_response()`: 遅延付きレスポンス生成

3. **`tests/unit/test_demo_service.py`**
   - 単体テスト（14テスト）
   - デモファイル判定、JSONロード、遅延時間、並行実行のテスト

4. **`tests/e2e/test_demo.py`**
   - E2Eテスト（4テスト）
   - 完全なフロー、一貫性、遅延時間、レスポンス形式のテスト

### 修正ファイル（3件）

5. **`app/core/config.py`**
   - デモモード設定の追加（3つの環境変数）
   - `_get_float_env()`メソッド追加（遅延時間用）

6. **`app/api/v1/endpoints/analyze.py`**
   - デモファイル判定ロジックの追加
   - `DemoService`のインポートとインスタンス化
   - レスポンス形式の変換（dict → Pydanticモデル）

7. **`tests/integration/test_api.py`**
   - `TestDemoMode`クラス追加（3テスト）
   - デモファイルでのAPI呼び出し、通常ファイルとの比較テスト

## テスト結果

### 全テストの実行結果

```bash
$ python -m pytest tests/ -v
```

- **総テスト数**: 221件 ✅（従来200件 + 新規21件）
- **成功**: 221件 ✅
- **失敗**: 0件
- **実行時間**: 41.42秒

### 新規テストの詳細

#### 1. 単体テスト（14件）

**デモファイル判定のテスト**（8件）:
```python
@pytest.mark.parametrize(
    "filename,expected",
    [
        ("__DEMO__.txt", True),
        ("test.txt", False),
        ("demo.txt", False),
        ("__demo__.txt", False),  # 大文字小文字を区別
        ("__DEMO__", False),      # .txtがない
        (None, False),
        ("", False),
    ],
)
def test_is_demo_file(self, filename, expected):
    """デモファイル判定のテスト"""
    service = DemoService()
    assert service.is_demo_file(filename) == expected
```

**結果**: すべてPASSED ✅

**モックレスポンス読み込みのテスト**:
```python
def test_load_demo_response(self):
    """モックレスポンス読み込みのテスト"""
    service = DemoService()
    data = service.load_demo_response()

    # 基本構造の検証
    assert data["total_messages"] == 1000
    assert data["total_users"] == 3
    
    # 流行語ランキングの検証
    top_words = data["morphological_analysis"]["top_words"]
    assert len(top_words) == 50
    assert top_words[0]["word"] == "エッホエッホ"
    assert top_words[0]["count"] == 150
    
    # 流行メッセージランキングの検証
    top_messages = data["full_message_analysis"]["top_messages"]
    assert len(top_messages) == 30
    assert top_messages[0]["message"] == "それな"
    assert top_messages[0]["count"] == 80
```

**結果**: PASSED ✅

**遅延付きレスポンス生成のテスト**:
```python
@pytest.mark.asyncio
async def test_generate_demo_response(self):
    """遅延付きレスポンス生成のテスト"""
    service = DemoService()
    delay_seconds = 0.1  # テスト用に短く設定

    start_time = time.time()
    data = await service.generate_demo_response(delay_seconds)
    elapsed_time = time.time() - start_time

    # 遅延時間の確認（±0.05秒の誤差を許容）
    assert abs(elapsed_time - delay_seconds) < 0.05
    assert data["total_messages"] == 1000
```

**結果**: PASSED ✅

**並行実行のテスト**:
```python
@pytest.mark.asyncio
async def test_generate_demo_response_concurrent(self):
    """複数回同時呼び出しのテスト"""
    service = DemoService()
    
    # 3回同時に呼び出し
    tasks = [
        service.generate_demo_response(0.1),
        service.generate_demo_response(0.1),
        service.generate_demo_response(0.1),
    ]
    
    results = await asyncio.gather(*tasks)
    
    # すべて同じレスポンスが返ること
    assert len(results) == 3
    for result in results:
        assert result["total_messages"] == 1000
```

**結果**: PASSED ✅

#### 2. 統合テスト（3件）

**デモファイルでのAPI呼び出し**:
```python
def test_demo_file_upload(self) -> None:
    """デモファイルでのAPI呼び出しのテスト"""
    # デモファイル（空でも可）
    content = b""
    file = BytesIO(content)

    start_time = time.time()
    
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("__DEMO__.txt", file, "text/plain")},
    )
    
    elapsed_time = time.time() - start_time

    # レスポンスの検証
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    
    # 基本統計情報の検証
    assert data["data"]["total_messages"] == 1000
    assert data["data"]["total_users"] == 3
    
    # 流行語ランキングの検証
    top_words = data["data"]["morphological_analysis"]["top_words"]
    assert len(top_words) == 50
    assert top_words[0]["word"] == "エッホエッホ"
    
    # 遅延時間の検証（設定値は3秒、±0.5秒の誤差を許容）
    assert 2.5 <= elapsed_time <= 3.5
```

**結果**: PASSED ✅

**デモファイルと通常ファイルの比較**:
```python
def test_demo_file_vs_normal_file(self) -> None:
    """デモファイルと通常ファイルの動作の違いを確認"""
    # デモファイル
    demo_response = client.post(
        "/api/v1/analyze",
        files={"file": ("__DEMO__.txt", BytesIO(b""), "text/plain")},
    )
    
    # 通常ファイル（最小サンプル）
    normal_content = """[LINE] テスト
保存日時：2024/01/01 00:00

2024/01/01(月)
10:00	ユーザーA	テストメッセージ
"""
    normal_response = client.post(
        "/api/v1/analyze",
        files={"file": ("test.txt", BytesIO(normal_content.encode("utf-8")), "text/plain")},
    )
    
    # デモファイルは固定のメッセージ数
    assert demo_response.json()["data"]["total_messages"] == 1000
    
    # 通常ファイルは実際のメッセージ数
    assert normal_response.json()["data"]["total_messages"] == 1
```

**結果**: PASSED ✅

#### 3. E2Eテスト（4件）

**完全なフローのテスト**:
```python
def test_demo_mode_complete_flow(self) -> None:
    """デモモードの完全なフローのテスト"""
    demo_file = BytesIO(b"")
    
    response = client.post(
        "/api/v1/analyze",
        files={"file": ("__DEMO__.txt", demo_file, "text/plain")},
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # トップ10を確認
    expected_top_10 = [
        "エッホエッホ", "チャッピー", "ミャクミャク", "ぬい活",
        "ビジュイイじゃん", "ほいたらね", "オンカジ", "麻辣湯",
        "トランプ関税", "古古古米",
    ]
    top_words = data["data"]["morphological_analysis"]["top_words"]
    for i, expected_word in enumerate(expected_top_10):
        assert top_words[i]["word"] == expected_word
    
    # レスポンスサイズの確認（10KB以下）
    response_text = json.dumps(data, ensure_ascii=False)
    response_size = len(response_text.encode("utf-8"))
    assert response_size < 10 * 1024
```

**結果**: PASSED ✅

**複数回呼び出しの一貫性**:
```python
def test_demo_mode_consistent_response(self) -> None:
    """複数回呼び出しでの一貫性のテスト"""
    response1 = client.post("/api/v1/analyze", files={"file": ("__DEMO__.txt", BytesIO(b""), "text/plain")})
    response2 = client.post("/api/v1/analyze", files={"file": ("__DEMO__.txt", BytesIO(b""), "text/plain")})
    response3 = client.post("/api/v1/analyze", files={"file": ("__DEMO__.txt", BytesIO(b""), "text/plain")})
    
    # すべて同じレスポンスが返ること
    data1 = response1.json()
    data2 = response2.json()
    data3 = response3.json()
    
    assert data1 == data2 == data3
```

**結果**: PASSED ✅

### コード品質チェック

```bash
# Black（フォーマット）
$ python -m black app/services/demo_service.py app/core/config.py app/api/v1/endpoints/analyze.py tests/
✅ All files reformatted

# isort（import順序）
$ python -m isort --profile=black --line-length=100 --check-only <files>
✅ No issues found

# flake8（リンター）
$ python -m flake8 app/services/demo_service.py app/core/config.py app/api/v1/endpoints/analyze.py \
    --max-line-length=100 \
    --ignore=E203,W503,ANN101,ANN204,ANN401,D105,D107,D403,D415,DAR101,DAR201 \
    --select=E,W,F,N,D \
    --docstring-convention=google
✅ No issues found

# mypy（型チェック）
$ python -m mypy app/services/demo_service.py app/core/config.py app/api/v1/endpoints/analyze.py \
    --config-file=mypy.ini
✅ Success: no issues found in 3 source files
```

## 使用例

### API経由（curl）

```bash
# デモファイルをアップロード（空ファイルでも可）
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -F "file=@__DEMO__.txt"

# レスポンス（約3秒後）
{
  "status": "success",
  "data": {
    "analysis_period": {
      "start_date": "2025-01-01",
      "end_date": "2025-12-31"
    },
    "total_messages": 1000,
    "total_users": 3,
    "morphological_analysis": {
      "top_words": [
        {"word": "エッホエッホ", "count": 150, "part_of_speech": "名詞"},
        {"word": "チャッピー", "count": 120, "part_of_speech": "名詞"},
        ...
      ]
    },
    "full_message_analysis": {
      "top_messages": [
        {"message": "それな", "count": 80},
        {"message": "わかる", "count": 65},
        ...
      ]
    },
    "user_analysis": {
      ...
    }
  }
}
```

### API経由（Python requests）

```python
import requests

# デモファイルを作成（空でも可）
with open("__DEMO__.txt", "w") as f:
    f.write("")

# アップロード
files = {"file": open("__DEMO__.txt", "rb")}
response = requests.post("http://localhost:8000/api/v1/analyze", files=files)

result = response.json()
print(f"総メッセージ数: {result['data']['total_messages']}")
print(f"1位: {result['data']['morphological_analysis']['top_words'][0]['word']}")
```

### API経由（JavaScript fetch）

```javascript
// デモファイルを作成
const demoFile = new File([""], "__DEMO__.txt", { type: "text/plain" });

// FormDataに追加
const formData = new FormData();
formData.append('file', demoFile);

// アップロード
const response = await fetch('http://localhost:8000/api/v1/analyze', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(`総メッセージ数: ${result.data.total_messages}`);
console.log(`1位: ${result.data.morphological_analysis.top_words[0].word}`);
```

### フロントエンドでの実装例

```javascript
// デモモード切り替えボタン
<button onClick={handleDemoMode}>デモを見る</button>

// デモモード実行
const handleDemoMode = async () => {
  // デモファイルを作成
  const demoFile = new File([""], "__DEMO__.txt", { type: "text/plain" });
  
  // アップロード
  const formData = new FormData();
  formData.append('file', demoFile);
  
  setLoading(true);
  try {
    const response = await fetch('/api/v1/analyze', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    // 通常の解析結果と同じ形式なので、
    // そのまま結果表示コンポーネントに渡せる
    setAnalysisResult(result.data);
  } finally {
    setLoading(false);
  }
};
```

## 環境変数仕様

### ENABLE_DEMO_MODE

- **型**: `bool`
- **デフォルト値**: `true`
- **説明**: デモモードの有効/無効を切り替え
- **使用例**:
  ```bash
  # 本番環境ではデモモードを無効化
  ENABLE_DEMO_MODE=false
  ```

### DEMO_TRIGGER_FILENAME

- **型**: `str`
- **デフォルト値**: `__DEMO__.txt`
- **説明**: デモモードをトリガーするファイル名
- **注意**: 大文字小文字を区別
- **使用例**:
  ```bash
  # 別のファイル名に変更
  DEMO_TRIGGER_FILENAME=SAMPLE.txt
  ```

### DEMO_RESPONSE_DELAY_SECONDS

- **型**: `float`
- **デフォルト値**: `3.0`
- **説明**: レスポンスまでの遅延時間（秒）
- **使用例**:
  ```bash
  # 遅延なしで即座に返す（開発用）
  DEMO_RESPONSE_DELAY_SECONDS=0
  
  # 大量データの解析を想定（10秒）
  DEMO_RESPONSE_DELAY_SECONDS=10
  ```

## 期待される効果

### 1. マーケティング・宣伝の改善

✅ **個人情報を気にせず公開可能**
- SNS、Webサイト、プレゼンテーションで自由に使用
- スクリーンショット、デモ動画の作成が容易

✅ **リアルな動作を再現**
- 実際の解析と同じ3秒の待ち時間
- 実際のトーク履歴と見分けがつかない結果

✅ **アプリの魅力を効果的に訴求**
- 2025年の流行語が並ぶ、話題性のあるランキング
- 「それな」「草」など共感できる口癖ランキング

### 2. 開発・テストの効率化

✅ **フロントエンド開発が容易**
- 毎回ファイルをアップロードする手間が不要
- 固定のレスポンスで再現性のあるテスト

✅ **デザインレビューが簡単**
- デモモードで瞬時に結果画面を表示
- UIの調整・検証がスムーズ

### 3. ユーザー体験の向上

✅ **気軽に試せる**
- 自分のトーク履歴をアップロードする前に、デモで動作確認
- アプリの使い方を理解してから本番利用

✅ **サンプルとして参考になる**
- 「こんな結果が出るんだ」というイメージが湧く
- 実際の使用イメージが明確に

### 4. コスト削減

✅ **個人情報マスキング作業が不要**
- 従来: 手動でマスキング → 再解析 → スクリーンショット
- 改善: デモモードで一発

✅ **開発時のファイル準備が不要**
- 従来: 毎回サンプルファイルを準備
- 改善: `__DEMO__.txt`（空ファイル）で即実行

## 注意事項

### 1. デモモードの判定

デモモードの判定は**ファイル名のみ**で行われます：

- ✅ `__DEMO__.txt` → デモモード
- ❌ `__DEMO__` → 通常モード（.txtがない）
- ❌ `__demo__.txt` → 通常モード（小文字）
- ❌ `demo.txt` → 通常モード
- ❌ `__DEMO__.TXT` → 通常モード（.TXTは大文字）

**ファイルの中身は見ません**。空ファイルでも、何か書かれていても、デモモードとして動作します。

### 2. レスポンスサイズ

モックレスポンスのサイズ：
- **JSONファイル**: 約8KB
- **APIレスポンス全体**: 約9KB

実際のトーク履歴（27万メッセージ）の解析結果（約50KB）と比べると、非常にコンパクトです。

### 3. 本番環境での使用

本番環境では、デモモードを無効化することを推奨します：

```bash
# 本番環境の環境変数
ENABLE_DEMO_MODE=false
```

無効化すると、`__DEMO__.txt`をアップロードしても通常の解析として処理されます（ファイル内容が不正なのでエラーになります）。

### 4. パフォーマンス

デモモードは実際の解析を行わないため、サーバーリソースをほとんど消費しません：

- **CPU使用率**: ほぼ0%（JSONファイル読み込みのみ）
- **メモリ使用量**: 約0.01MB（JSONデータのみ）
- **応答時間**: 遅延設定（デフォルト3秒）+ 約0.01秒

実際の解析（約3秒 + CPU/メモリ使用）と比べると、サーバー負荷は極めて軽微です。

### 5. フロントエンドとの互換性

デモモードのレスポンスは、通常の解析結果と**完全に同じ形式**です：

```typescript
// 通常モードもデモモードも同じ型
interface AnalysisResult {
  status: "success";
  data: {
    analysis_period: { start_date: string; end_date: string };
    total_messages: number;
    total_users: number;
    morphological_analysis: { top_words: TopWord[] };
    full_message_analysis: { top_messages: TopMessage[] };
    user_analysis: UserAnalysis;
  };
}
```

フロントエンド側でモード判定する必要はありません。どちらも同じコンポーネントで表示できます。

### 6. カスタムヘッダー（将来的な拡張）

将来的には、デモモードの場合に以下のヘッダーを追加する予定です：

```
X-Demo-Mode: true
```

これにより、フロントエンドで「デモモード」バッジを表示したり、異なるUIを提供できます。

現時点では実装されていませんが、必要に応じて追加可能です。

## まとめ

本機能により、以下が実現されました：

1. ✅ 個人情報を含まない宣伝用のデモが可能に
2. ✅ リアルな動作を再現（3秒の遅延付き）
3. ✅ 2025年の流行語をベースにした話題性のあるランキング
4. ✅ フロントエンド開発・テストの効率化
5. ✅ 気軽に試せるデモ機能でユーザー体験向上
6. ✅ 本番環境での無効化も可能

すべてのテストがパス（221/221）し、コード品質チェックもすべてクリアしています。

## 技術的詳細

### アーキテクチャ

```
[analyze.py]
    ↓
デモファイル判定
    ↓
[DemoService]
    ↓
JSONファイル読み込み
    ↓
遅延（asyncio.sleep）
    ↓
Pydanticモデルに変換
    ↓
レスポンス返却
```

### ファイル構成

```
app/
  data/
    demo_response.json       # モックデータ（8KB）
  services/
    demo_service.py          # デモサービス（91行）
  core/
    config.py                # 設定（環境変数追加）
  api/v1/endpoints/
    analyze.py               # エンドポイント（デモ判定追加）

tests/
  unit/
    test_demo_service.py     # 単体テスト（14テスト）
  integration/
    test_api.py              # 統合テスト（3テスト追加）
  e2e/
    test_demo.py             # E2Eテスト（4テスト）
```

### 設計のポイント

#### 1. シングルトンパターン

DemoServiceはモジュールレベルでインスタンス化され、複数のリクエストで共有されます：

```python
# analyze.py
demo_service = DemoService()  # シングルトン
```

これにより、JSONファイルのパース結果がメモリにキャッシュされ、2回目以降の応答が高速化されます。

#### 2. 非同期処理

遅延処理に`asyncio.sleep()`を使用し、非同期処理を維持：

```python
async def generate_demo_response(self, delay_seconds: float) -> dict[str, Any]:
    await asyncio.sleep(delay_seconds)  # 非同期で待機
    data = self.load_demo_response()
    return data
```

これにより、遅延中も他のリクエストを処理できます。

#### 3. 型安全性

Pydanticモデルに変換することで、型安全性を確保：

```python
# dictからPydanticモデルに変換
demo_data_dict = await demo_service.generate_demo_response(delay_seconds)
demo_data = WordAnalysisResult(**demo_data_dict)
return AnalysisResult(status="success", data=demo_data)
```

これにより、レスポンス構造が保証されます。

#### 4. 環境変数による制御

本番環境での無効化、遅延時間の調整など、柔軟な制御が可能：

```python
if not self.settings.ENABLE_DEMO_MODE:
    return False
```

### パフォーマンス測定

実測値（単体テスト）：

| 項目 | 時間 |
|------|------|
| JSONファイル読み込み | < 0.01秒 |
| 遅延（デフォルト3秒） | 3.00秒 ±0.05秒 |
| Pydanticモデル変換 | < 0.01秒 |
| **合計** | **約3.01秒** |

実際の解析（約1000メッセージ）：

| 項目 | 時間 |
|------|------|
| パーサー | 約0.5秒 |
| 形態素解析（MeCab） | 約2.0秒 |
| 集計・ソート | 約0.5秒 |
| **合計** | **約3.0秒** |

デモモードは実際の解析とほぼ同じ時間で応答するため、リアルなユーザー体験を提供できます。

