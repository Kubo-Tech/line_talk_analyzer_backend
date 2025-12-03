# Pythonコーディング規約

本プロジェクトでは、以下のツール・ガイドラインに基づいて Python のコードスタイルを統一する。
copilot chatはこの文書を読み込んだら「コーディング規約を完全に理解しました。」と述べてください。

## 基本ルール

基本的にはPython 標準の [PEP8](https://pep8-ja.readthedocs.io/ja/latest/) に準拠する。場合によっては[Google Style](https://github.com/charmie11/google-styleguide/blob/gh-pages/pyguide-ja.md)のルールを採用する。  
以下のルールは後述するフォーマッタで自動整形してくれるため気にしなくてもよい。

- インデント：4文字
- 文字列リテラル：ダブルクォート " " を使用
  - ' ' は片手で入力しづらいため
- 1行の文字数：100文字
  - PEP8は79文字or99文字を推奨しているが、会社で100文字が採用されているため

以下のルールは後述するリンタや静的解析ツールによってリアルタイムで警告が出るので警告が出なくなるように自分で直すこと。

- docstring：[Google Style](https://github.com/charmie11/google-styleguide/blob/gh-pages/pyguide-ja.md#38-comments-and-docstrings-%E3%82%B3%E3%83%A1%E3%83%B3%E3%83%88%E3%81%A8docstring)を使用（後述）
- 命名規則（後述）
- 型アノテーション必須（後述）

以下のルールは誰も注意してくれないため自分で意識して守ること。

- モジュールやクラスではpublicな関数を上に、privateな関数を下に書く
- privateな関数は先頭に_をつける
  - 例：別のファイルからimportされない関数は`function()`ではなく`_function()`のように書く
- 実行ファイルは`if __name__ == '__main__'`を使う
- 1文字変数は原則禁止。
  - 例外：カウンタ・イテレータの`i`等、exceptでの`e`、ファイルオブジェクトの`f`

## 使用ツール

以下のツールは`/.vscode/extensions.json`に記載されているため、VSCodeをプロジェクトルートで開けばおすすめの拡張機能として推奨される。インストールすること。  
`/.vscode/settings.json`で細かいルールを設定しているため、VSCodeをプロジェクトルートで開けば、ファイルを編集して保存するたびにこれらが機能して自動で整形してくれる。

### Black

フォーマッタに[Black](https://github.com/psf/black)を使用

`settings.json` の設定内容

- 保存時に自動実行
- 最大文字数100文字
- notebookでも適用

### isort

import整形に[isort](https://pycqa.github.io/isort/)を使用

`settings.json` の設定内容

- 保存時に自動実行
- notebookでも適用

### flake8

リンタに[flake8](https://flake8.pycqa.org/)を使用

`settings.json` の設定内容

- 保存時に自動実行
- 最大文字数100文字
- :の前にスペースを入れることを許容
- 改行が演算子の前にあることを許容
- `self`には型アノテーション不要
- `__init__`には返り値の型アノテーション不要
- 型アノテーションに`Any`を許容
- `__post_init__`などにdocstring不要
- docstringの1行目の末尾にピリオド不要
- docstringにArgsとReturnsがなくてもよい

最大文字数制限をどうしても回避したい場合は行の末尾に`# noqa: E501`と記載する

### mypy

静的型チェックツールにmypyを使用

- 型がない関数引数・戻り値・変数を禁止
- 未注釈の list, dict などを禁止（list -> list[int] を強制）

## 型アノテーション

- 関数、メソッドの引数と戻り値には必ず型アノテーションをつけること
- 型アノテーションでできるだけtypingを使用しない
  - Dict, List, Tupleではなくdict, list, tupleを使うこと
  - Optional, Unionではなく`str | None`のように|を使うこと
  - Any,その他必要なものは使用を認める
- list, dict, tupleなどのコンテナ型には中身の型を必ず指定すること
  - 例：`list[int]`, `dict[str, float]`, `tuple[str, int]`

## Docstring

- [Google スタイル](https://github.com/charmie11/google-styleguide/blob/gh-pages/pyguide-ja.md#38-comments-and-docstrings-%E3%82%B3%E3%83%A1%E3%83%B3%E3%83%88%E3%81%A8docstring)を採用
- すべてのモジュール、クラス、関数に概要は最低限書くこと。説明を書かなくても内容が自明であれば引数の説明などは記載しなくてもよい。
- 返り値がtupleの場合は各要素を改行して記載すること。
- 拡張機能autoDocstringがインストールされているはずなので、基本的にはそれに従えばよい。
- よく以下の警告が出るので気を付けること。
  - Missing exception(s) in Raises section: -r ValueErrorFlake8(DAR401)
  - Multi-line docstring summary should start at the first lineFlake8(D212)

書き方の例）

- モジュールの場合

    ```python

    """モジュールの概要

    モジュールの詳細説明
    """

    # 1行開けてからimport文を記載
    ```

- クラスの場合

    ```python
    class FugaFuga():
        """クラスの概要

        クラスの詳細説明

    　　Attributes:
            属性名 (型): 属性の説明
        """

        # 1行開けてからクラスの内容を記載
    ```

- 関数の場合

    ```python
    # good
    def hogehoge(arg1: int, arg2: float) -> tuple[str, int]:
        """関数の概要

        関数の詳細説明

        Args:
            arg1 (int): 引数の説明
            arg2 (float): 引数の説明

        Returns:
            str: 返り値の説明
            int: 返り値の説明
        """
        # 1行開けずに関数の内容を記載

    # bad
    def fugafuga(arg1: int, arg2: float) -> tuple[str, int]:
        """
        関数の概要  # 2行目に書いてはいけない

        関数の詳細説明

        Args:
            arg1 (int): 引数の説明
            arg2 (float): 引数の説明

        Returns:
            tuple[str, int]: 返り値の説明  # tupleを1行にまとめてはいけない
        """

        # docstringのあとは1行開けてはいけない
    ```

- その他のセクション

    | セクション | 内容 |
    |------------|------|
    | Yields     | yield文での戻り値の説明 |
    | Raises     | 例外処理の説明 |
    | Examples   | クラスや関数の実行例 |
    | Note       | 特筆事項 |
    | Todo       | Todoリストを記載 |

## 命名規則（PEP8準拠）

以下の命名規則に従わない場合、flake8の警告が出るので直すこと。

| 対象         | 命名規則    | 例                      |
|--------------|-------------|-------------------------|
| 変数名       | snake_case  | `user_id`, `score_list` |
| 関数名       | snake_case  | `calculate_score()`     |
| メソッド名   | snake_case  | `get_value()`           |
| クラス名     | PascalCase  | `UserModel`, `MyClass`  |
| 定数名       | UPPER_CASE  | `MAX_RETRY_COUNT`       |
| モジュール名 | snake_case  | `utils.py`, `my_module.py` |
| パッケージ名 | snake_case  | `my_project/`, `tools/` |
| 引数名       | snake_case  | `user_name`, `file_path` |
| 例外クラス   | PascalCase + "Error" | `ValidationError`, `IOError` |

## 1行文字数との戦い方

フォーマッタによる1行の文字数制限のせいでコードが意図しない形に整形され可読性が下がる場合がある。  
以下の方法で対策して字数制限を守りながら可読性を向上させよう  

### 後ろにコメントを付けたせいで改行されたとき

コメントを上の行にずらそう

例：

```python
common_columns = [
    col for col in SUPPORTED_COLUMNS if col in race_basic_columns
]  # 重複するリストを取得
```

↓

```python
# 重複するリストを取得
common_columns = [col for col in SUPPORTED_COLUMNS if col in race_basic_columns]
```

### 引数の文字数が長くて改行されたとき

引数を変数にしよう

```python
race_info_df[str_remove] = int(
        re.search(r"\d+", race_info_df[str_remove].iloc[0]).group()
    )
```

↓

```python
num = re.search(r"\d+", race_info_df[str_remove].iloc[0]).group()
race_info_df[str_remove] = int(num)
```

まだ足りなければ、複数の引数をまとめて変数にしよう

```python
suitable_path = io.gene_suitable_path(
    race_id, self.target, self.include_rate_flag, self.param
)
```

↓

```python
args = (race_id, self.target, self.include_rate_flag, self.param)
suitable_path = io.gene_suitable_path(*args)
```

### リスト内包表記が改行されたとき

リスト内法表記はforループを使わずに1行でシンプルに書けることが利点だが、改行されてしまうと非常に見にくい  
大人しくforループを使おう

```python
rate_before_list = [
    env.expose(
        rate_dict.get(
            row[target_index], trueskill.Rating(mu=param.MU, sigma=param.SIGMA)
        )
    )
    for row in Rating_df_calc_before.values
]  # レース前レート（初登場は初期値）
```

↓

```python
# デフォルトレーティングを定義（初登場時用）
default_rating = trueskill.Rating(mu=param.MU, sigma=param.SIGMA)
# レース前レート（初登場は初期値）
rate_before_list = []
for row in rating_df_calc_before.values:
    # 辞書から対象のレートを取得、なければデフォルト値を使用
    current_rating = rate_dict.get(row[target_index], default_rating)
    # 実際のレート値に変換
    rate_before = env.expose(current_rating)
    rate_before_list.append(rate_before)
```

全体の行数は増えたが、このほうが見やすい

## classの使い方

メンバ変数を持たないclassはclassである意味がないので、通常の関数にするかメンバ変数を持たせる設計に変更すること。  
コンストラクタで何も処理しないclassも意味がないので設計変更すること。

```python
# Good
class MyClass:
    def __init__(self, message):
        self.message = message

    def my_method(self):
        return self.message

# Bad
class MyClass:
    def my_method(self):
        return "Hello, World!"

```

selfを参照しないメソッドはメソッドにする意味がないので通常の関数にすること。

```python
# Good
def my_function(message):
    return message

# Bad
class MyClass:
    def my_method(self, message):
        return message
```

## ソフトウェア設計思想

SOLID原則に基づいたソフトウェア設計を行うこと。  
参考：[イラストで理解するSOLID原則](https://qiita.com/baby-degu/items/d058a62f145235a0f007)

## 独自ルール

異論は認める

- ミュータブルな変数にはできるだけ型情報を末尾につける
  - 例：`rank_list`, `keibajo_to_id_dict`, `race_info_df`, `score_array`
  - 例外：
    - 変数名が長すぎて型アノテーションしてる場合ではない場合
    - 末尾が`_collumns`や`_vec`でリストやnp.arrayであることが明白である場合
    - 変数スコープが短く型アノテーションしなくても型がその場でわかる場合
- print文は日本語で書く。日本人なので。

## 参考文献

- [[Pythonコーディング規約]PEP8を読み解く](https://qiita.com/simonritchie/items/bb06a7521ae6560738a7)
- [【Pythonコーディング規約】PEP 8 vs Google Style](https://qiita.com/hi-asano/items/f43ced224483ea1f62f4)
- [[Python] docstringのスタイルと書き方](https://qiita.com/flcn-x/items/393c6f1f1e1e5abec906)
- [イラストで理解するSOLID原則](https://qiita.com/baby-degu/items/d058a62f145235a0f007)
