"""データモデルのテスト

リクエスト/レスポンスモデルの単体テストを実施する
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models import (
    AnalysisPeriod,
    AnalysisResult,
    AnalyzeRequest,
    ErrorDetail,
    ErrorResponse,
    MessageAnalysisResult,
    MessageAppearance,
    MorphologicalAnalysis,
    TopMessage,
    TopWord,
    WordAnalysisResult,
    WordAppearance,
)


class TestAnalyzeRequest:
    """AnalyzeRequestモデルのテスト"""

    def test_default_values(self) -> None:
        """デフォルト値のテスト"""
        request = AnalyzeRequest()
        assert request.top_n == 50
        assert request.min_word_length == 1
        assert request.exclude_parts is None

    def test_custom_values(self) -> None:
        """カスタム値のテスト"""
        request = AnalyzeRequest(top_n=100, min_word_length=2, exclude_parts="助詞,助動詞")
        assert request.top_n == 100
        assert request.min_word_length == 2
        assert request.exclude_parts == "助詞,助動詞"

    def test_top_n_validation_min(self) -> None:
        """top_nの最小値バリデーション"""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(top_n=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_top_n_validation_max(self) -> None:
        """top_nの最大値バリデーション"""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(top_n=1001)
        assert "less than or equal to 1000" in str(exc_info.value)

    def test_min_word_length_validation_min(self) -> None:
        """min_word_lengthの最小値バリデーション"""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(min_word_length=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_min_word_length_validation_max(self) -> None:
        """min_word_lengthの最大値バリデーション"""
        with pytest.raises(ValidationError) as exc_info:
            AnalyzeRequest(min_word_length=11)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_exclude_parts_normalization(self) -> None:
        """除外品詞の正規化テスト"""
        request = AnalyzeRequest(exclude_parts=" 助詞 , 助動詞 , 記号 ")
        assert request.exclude_parts == "助詞,助動詞,記号"

    def test_exclude_parts_empty_string(self) -> None:
        """空文字列の除外品詞テスト"""
        request = AnalyzeRequest(exclude_parts="   ")
        assert request.exclude_parts is None

    def test_get_exclude_parts_list(self) -> None:
        """除外品詞リスト取得のテスト"""
        request = AnalyzeRequest(exclude_parts="助詞,助動詞,記号")
        assert request.get_exclude_parts_list() == ["助詞", "助動詞", "記号"]

    def test_get_exclude_parts_list_none(self) -> None:
        """除外品詞がNoneの場合のリスト取得テスト"""
        request = AnalyzeRequest()
        assert request.get_exclude_parts_list() == []

    def test_json_serialization(self) -> None:
        """JSONシリアライズのテスト"""
        request = AnalyzeRequest(top_n=100, min_word_length=2)
        json_data = request.model_dump()
        assert json_data["top_n"] == 100
        assert json_data["min_word_length"] == 2

    def test_json_deserialization(self) -> None:
        """JSONデシリアライズのテスト"""
        json_str = '{"top_n": 100, "min_word_length": 2, "exclude_parts": "助詞"}'
        request = AnalyzeRequest.model_validate_json(json_str)
        assert request.top_n == 100
        assert request.min_word_length == 2
        assert request.exclude_parts == "助詞"


class TestWordAppearance:
    """WordAppearanceモデルのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス生成のテスト"""
        appearance = WordAppearance(
            date=datetime(2024, 8, 1, 22, 12, 0),
            user="hoge山fuga太郎",
            message="おうち帰りたい",
        )
        assert appearance.date == datetime(2024, 8, 1, 22, 12, 0)
        assert appearance.user == "hoge山fuga太郎"
        assert appearance.message == "おうち帰りたい"

    def test_json_serialization(self) -> None:
        """JSONシリアライズのテスト"""
        appearance = WordAppearance(
            date=datetime(2024, 8, 1, 22, 12, 0),
            user="hoge山fuga太郎",
            message="おうち帰りたい",
        )
        json_data = appearance.model_dump()
        assert json_data["user"] == "hoge山fuga太郎"
        assert json_data["message"] == "おうち帰りたい"


class TestTopWord:
    """TopWordモデルのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス生成のテスト"""
        word = TopWord(word="おうち", count=42, part_of_speech="名詞", appearances=[])
        assert word.word == "おうち"
        assert word.count == 42
        assert word.part_of_speech == "名詞"
        assert word.appearances == []

    def test_with_appearances(self) -> None:
        """出現情報を含むテスト"""
        appearance = WordAppearance(
            date=datetime(2024, 8, 1, 22, 12, 0),
            user="hoge山fuga太郎",
            message="おうち帰りたい",
        )
        word = TopWord(word="おうち", count=1, part_of_speech="名詞", appearances=[appearance])
        assert len(word.appearances) == 1
        assert word.appearances[0].message == "おうち帰りたい"

    def test_count_validation(self) -> None:
        """カウントのバリデーション"""
        with pytest.raises(ValidationError):
            TopWord(word="test", count=0, part_of_speech="名詞")


class TestMorphologicalAnalysis:
    """MorphologicalAnalysisモデルのテスト"""

    def test_create_empty(self) -> None:
        """空のインスタンス生成テスト"""
        analysis = MorphologicalAnalysis()
        assert analysis.top_words == []

    def test_create_with_words(self) -> None:
        """単語を含むインスタンス生成テスト"""
        word = TopWord(word="おうち", count=42, part_of_speech="名詞", appearances=[])
        analysis = MorphologicalAnalysis(top_words=[word])
        assert len(analysis.top_words) == 1
        assert analysis.top_words[0].word == "おうち"


class TestMessageAppearance:
    """MessageAppearanceモデルのテスト"""

    def test_create_exact_match(self) -> None:
        """完全一致の出現情報テスト"""
        appearance = MessageAppearance(
            date=datetime(2024, 8, 1, 22, 12, 0),
            user="hoge山fuga太郎",
            message="おうち帰りたい",
            match_type="exact",
        )
        assert appearance.match_type == "exact"

    def test_invalid_match_type(self) -> None:
        """不正な一致タイプのバリデーション"""
        with pytest.raises(ValidationError):
            MessageAppearance(
                date=datetime(2024, 8, 1, 22, 12, 0),
                user="hoge山fuga太郎",
                message="test",
                match_type="invalid",  # type: ignore
            )


class TestTopMessage:
    """TopMessageモデルのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス生成のテスト"""
        message = TopMessage(
            message="おうち帰りたい",
            count=23,
            appearances=[],
        )
        assert message.message == "おうち帰りたい"
        assert message.count == 23

    def test_count_validation(self) -> None:
        """カウントのバリデーション"""
        with pytest.raises(ValidationError):
            TopMessage(
                message="test",
                count=0,
            )


class TestMessageAnalysisResult:
    """MessageAnalysisResultモデルのテスト"""

    def test_create_empty(self) -> None:
        """空のインスタンス生成テスト"""
        result = MessageAnalysisResult()
        assert result.top_messages == []

    def test_create_with_messages(self) -> None:
        """メッセージを含むインスタンス生成テスト"""
        message = TopMessage(
            message="おうち帰りたい",
            count=23,
            appearances=[],
        )
        result = MessageAnalysisResult(top_messages=[message])
        assert len(result.top_messages) == 1
        assert result.top_messages[0].message == "おうち帰りたい"


class TestAnalysisPeriod:
    """AnalysisPeriodモデルのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス生成のテスト"""
        period = AnalysisPeriod(start_date="2024-01-01", end_date="2024-12-31")
        assert period.start_date == "2024-01-01"
        assert period.end_date == "2024-12-31"


class TestWordAnalysisResult:
    """WordAnalysisResultモデルのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス生成のテスト"""
        period = AnalysisPeriod(start_date="2024-01-01", end_date="2024-12-31")
        morphological = MorphologicalAnalysis()
        message_analysis = MessageAnalysisResult()

        result = WordAnalysisResult(
            analysis_period=period,
            total_messages=1500,
            total_users=3,
            morphological_analysis=morphological,
            full_message_analysis=message_analysis,
        )
        assert result.total_messages == 1500
        assert result.total_users == 3
        assert result.analysis_period.start_date == "2024-01-01"

    def test_validation(self) -> None:
        """バリデーションテスト"""
        period = AnalysisPeriod(start_date="2024-01-01", end_date="2024-12-31")
        morphological = MorphologicalAnalysis()
        message_analysis = MessageAnalysisResult()

        with pytest.raises(ValidationError):
            WordAnalysisResult(
                analysis_period=period,
                total_messages=-1,
                total_users=3,
                morphological_analysis=morphological,
                full_message_analysis=message_analysis,
            )


class TestAnalysisResult:
    """AnalysisResultモデルのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス生成のテスト"""
        period = AnalysisPeriod(start_date="2024-01-01", end_date="2024-12-31")
        morphological = MorphologicalAnalysis()
        message_analysis = MessageAnalysisResult()
        data = WordAnalysisResult(
            analysis_period=period,
            total_messages=1500,
            total_users=3,
            morphological_analysis=morphological,
            full_message_analysis=message_analysis,
        )

        result = AnalysisResult(data=data)
        assert result.status == "success"
        assert result.data.total_messages == 1500

    def test_json_serialization(self) -> None:
        """JSONシリアライズのテスト"""
        period = AnalysisPeriod(start_date="2024-01-01", end_date="2024-12-31")
        morphological = MorphologicalAnalysis()
        message_analysis = MessageAnalysisResult()
        data = WordAnalysisResult(
            analysis_period=period,
            total_messages=1500,
            total_users=3,
            morphological_analysis=morphological,
            full_message_analysis=message_analysis,
        )
        result = AnalysisResult(data=data)

        json_data = result.model_dump()
        assert json_data["status"] == "success"
        assert json_data["data"]["total_messages"] == 1500


class TestErrorResponse:
    """ErrorResponseモデルのテスト"""

    def test_create_instance(self) -> None:
        """インスタンス生成のテスト"""
        error_detail = ErrorDetail(
            code="INVALID_FILE_FORMAT",
            message="アップロードされたファイルの形式が無効です",
        )
        error = ErrorResponse(error=error_detail)
        assert error.status == "error"
        assert error.error.code == "INVALID_FILE_FORMAT"
        assert error.error.message == "アップロードされたファイルの形式が無効です"

    def test_json_serialization(self) -> None:
        """JSONシリアライズのテスト"""
        error_detail = ErrorDetail(code="INVALID_FILE_FORMAT", message="ファイル形式が無効です")
        error = ErrorResponse(error=error_detail)

        json_data = error.model_dump()
        assert json_data["status"] == "error"
        assert json_data["error"]["code"] == "INVALID_FILE_FORMAT"
