"""改行メッセージのカウント確認スクリプト"""

from app.services.parser import LineMessageParser


def count_multiline_messages() -> None:
    """sample.txtの改行メッセージ数をカウント"""
    with open("talk/sample.txt", encoding="utf-8") as f:
        parser = LineMessageParser()
        messages = parser.parse(f)

    # 改行を含むメッセージをカウント
    multiline_count = sum(1 for m in messages if "\n" in m.content)
    total_count = len(messages)

    print(f"総メッセージ数: {total_count}")
    print(f"改行メッセージ数: {multiline_count}")
    print(f"改行メッセージ割合: {multiline_count / total_count * 100:.2f}%")

    # 改行メッセージの例を表示
    print("\n改行メッセージの例（最初の5件）:")
    multiline_messages = [m for m in messages if "\n" in m.content][:5]
    for i, msg in enumerate(multiline_messages, 1):
        lines = msg.content.split("\n")
        print(f"\n{i}. ユーザー: {msg.user}")
        print(f"   行数: {len(lines)}")
        print(f"   内容: {repr(msg.content[:100])}")


if __name__ == "__main__":
    count_multiline_messages()
