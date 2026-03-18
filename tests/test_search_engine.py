from unittest.mock import MagicMock, patch
from src.tools.search_engine import search_web


def test_search_web_returns_structured_results():
    fake_results = [
        {"title": "T1", "href": "https://a.com/1", "body": "snip1"},
        {"title": "T2", "href": "https://a.com/2", "body": "snip2"},
    ]

    fake_gen = (r for r in fake_results)
    mock_ddgs = MagicMock()

    mock_ddgs.__enter__.return_value = mock_ddgs
    mock_ddgs.text.return_value = fake_gen

    with patch("src.tools.search_engine.DDGS", return_value=mock_ddgs):
        out = search_web("query", max_results=2)
        assert isinstance(out, list)
        assert out[0]["source"] == "S1"
        assert out[0]["title"] == "T1"
        assert out[0]["url"] == "https://a.com/1"
        assert out[0]["snippet"] == "snip1"
        assert out[0]["domain"] == "a.com"
        assert out[0]["rank"] == 1


def test_search_web_handle_errors():
    mock_ddgs = MagicMock()

    mock_ddgs.__enter__.return_value = mock_ddgs
    mock_ddgs.text.side_effect = Exception("Connection Timeout!")

    with patch("src.tools.search_engine.DDGS", return_value=mock_ddgs):
        out = search_web("query", max_results=2)
        assert isinstance(out, list)
        assert out == []
