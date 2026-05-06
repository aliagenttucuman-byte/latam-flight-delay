import json
import os
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock

from challenge.ai_insights import (
    generate_context,
    generate_and_save_context,
    load_context,
    get_cached_context,
    build_prompt,
    _format_context,
    call_llm,
    get_ai_insight
)


class TestPolarsContext:
    """Tests for Polars context generation (build time)."""

    def test_generate_context_returns_dict(self):
        """Context is a dictionary with expected keys."""
        context = generate_context()
        assert isinstance(context, dict)
        assert "total_flights" in context
        assert "delay_rate" in context

    def test_generate_context_has_airlines(self):
        """Context includes delay by airline."""
        context = generate_context()
        assert "delay_by_airline" in context
        assert len(context["delay_by_airline"]["airlines"]) == 16

    def test_generate_context_has_months(self):
        """Context includes all 12 months."""
        context = generate_context()
        assert "delay_by_month" in context
        assert len(context["delay_by_month"]["months"]) == 12

    def test_delay_rate_is_percentage(self):
        """Delay rate is between 0 and 1."""
        context = generate_context()
        assert 0 <= context["delay_rate"] <= 1


class TestContextPersistence:
    """Tests for JSON save/load (build time)."""

    def test_generate_and_save_context_creates_file(self, tmp_path):
        """generate_and_save_context creates a JSON file."""
        csv_path = "data/data.csv"
        output_path = tmp_path / "context.json"

        generate_and_save_context(csv_path, str(output_path))

        assert output_path.exists()
        with open(output_path, "r") as f:
            data = json.load(f)
        assert "total_flights" in data
        assert "delay_rate" in data

    def test_load_context_returns_dict(self, tmp_path):
        """load_context returns dictionary from JSON."""
        context_data = {"total_flights": 1000, "delay_rate": 0.15}
        json_path = tmp_path / "context.json"

        with open(json_path, "w") as f:
            json.dump(context_data, f)

        loaded = load_context(str(json_path))
        assert loaded == context_data


class TestCachedContext:
    """Tests for cached context (request time)."""

    def test_get_cached_context_returns_dict(self):
        """get_cached_context returns the context dictionary."""
        with patch("challenge.ai_insights.load_context") as mock_load:
            mock_load.return_value = {"total_flights": 1000, "delay_rate": 0.15}

            import challenge.ai_insights
            challenge.ai_insights._context_cache = None

            result = get_cached_context()
            assert result == {"total_flights": 1000, "delay_rate": 0.15}

    def test_get_cached_context_caches_result(self):
        """get_cached_context caches the result to avoid repeated reads."""
        with patch("challenge.ai_insights.load_context") as mock_load:
            mock_load.return_value = {"total_flights": 1000, "delay_rate": 0.15}

            import challenge.ai_insights
            challenge.ai_insights._context_cache = None

            get_cached_context()
            get_cached_context()

            assert mock_load.call_count == 1


class TestPromptBuilding:
    """Tests for prompt construction."""

    def test_build_prompt_returns_list(self):
        """Prompt is a list of message dicts."""
        context = {
            "total_flights": 100,
            "total_delays": 15,
            "delay_rate": 0.15,
            "delay_by_airline": {"airlines": [], "rates": [], "counts": []},
            "delay_by_month": {"months": [], "rates": [], "counts": []},
            "delay_by_tipovuelo": {},
            "top_combinations": [],
            "worst_months": []
        }
        prompt = build_prompt("Why are flights delayed?", context)
        assert isinstance(prompt, list)
        assert len(prompt) >= 1

    def test_prompt_has_system_and_user(self):
        """Prompt contains system and user messages."""
        context = {
            "total_flights": 100,
            "total_delays": 15,
            "delay_rate": 0.15,
            "delay_by_airline": {"airlines": [], "rates": [], "counts": []},
            "delay_by_month": {"months": [], "rates": [], "counts": []},
            "delay_by_tipovuelo": {},
            "top_combinations": [],
            "worst_months": []
        }
        prompt = build_prompt("Why are flights delayed?", context)
        roles = [m["role"] for m in prompt]
        assert "system" in roles
        assert "user" in roles


class TestFormatContext:
    """Tests for context formatting."""

    def test_format_context_includes_numbers(self):
        """Formatted context includes flight numbers."""
        context = {
            "total_flights": 682,
            "total_delays": 102,
            "delay_rate": 0.15,
            "delay_by_airline": {"airlines": ["LATAM"], "rates": [0.18], "counts": [100]},
            "delay_by_month": {"months": [12], "rates": [0.31], "counts": [50]},
            "delay_by_tipovuelo": {"I": {"rate": 0.19, "count": 50}},
            "top_combinations": [],
            "worst_months": [{"MES": 12, "rate": 0.31}]
        }
        formatted = _format_context(context)
        assert "682" in formatted
        assert "LATAM" in formatted


class TestLLMCall:
    """Tests for LLM integration."""

    @pytest.mark.asyncio
    @patch("challenge.ai_insights.OPENROUTER_API_KEY", "test-key-123")
    @patch("challenge.ai_insights.httpx.AsyncClient")
    async def test_call_llm_success(self, mock_client):
        """Successful LLM call returns content."""
        pytest.skip("httpx mock complexity - tested via integration")

    @pytest.mark.asyncio
    async def test_call_llm_no_api_key(self):
        """Error when OPENROUTER_API_KEY is not set."""
        with patch("challenge.ai_insights.OPENROUTER_API_KEY", ""):
            prompt = [{"role": "user", "content": "test"}]
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                await call_llm(prompt)


class TestGetInsight:
    """Tests for the main insight function."""

    @pytest.mark.asyncio
    @patch("challenge.ai_insights.get_cached_context")
    async def test_get_ai_insight_returns_dict(self, mock_get_context):
        """Function returns dict with insight and context."""
        mock_get_context.return_value = {
            "total_flights": 682,
            "total_delays": 102,
            "delay_rate": 0.15,
            "delay_by_airline": {"airlines": ["LATAM"], "rates": [0.18], "counts": [100]},
            "delay_by_month": {"months": [12], "rates": [0.31], "counts": [50]},
            "delay_by_tipovuelo": {"I": {"rate": 0.19, "count": 50}},
            "top_combinations": [],
            "worst_months": [{"MES": 12, "rate": 0.31}]
        }

        with patch("challenge.ai_insights.call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "Los vuelos en diciembre tienen más retrasos."

            result = await get_ai_insight("¿Por qué se retrasan los vuelos?")

            assert isinstance(result, dict)
            assert "insight" in result
            assert "context_used" in result

    @pytest.mark.asyncio
    @patch("challenge.ai_insights.get_cached_context")
    async def test_get_ai_insight_error_handling(self, mock_get_context):
        """Function raises RuntimeError on LLM failure."""
        mock_get_context.return_value = {
            "total_flights": 682,
            "total_delays": 102,
            "delay_rate": 0.15,
            "delay_by_airline": {"airlines": ["LATAM"], "rates": [0.18], "counts": [100]},
            "delay_by_month": {"months": [12], "rates": [0.31], "counts": [50]},
            "delay_by_tipovuelo": {"I": {"rate": 0.19, "count": 50}},
            "top_combinations": [],
            "worst_months": [{"MES": 12, "rate": 0.31}]
        }

        with patch("challenge.ai_insights.call_llm", new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("Connection failed")

            with pytest.raises(RuntimeError, match="LLM call failed"):
                await get_ai_insight("¿Por qué se retrasan los vuelos?")