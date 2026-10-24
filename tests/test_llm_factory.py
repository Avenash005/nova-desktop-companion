"""
Unit tests for the LLM Factory and provider instantiation.
"""

import pytest
from src.open_llm_vtuber.agent.stateless_llm_factory import LLMFactory
from src.open_llm_vtuber.agent.stateless_llm.ollama_llm import OllamaLLM
from src.open_llm_vtuber.agent.stateless_llm.openai_compatible_llm import AsyncLLM as OpenAICompatibleLLM


def test_create_ollama_llm():
    llm = LLMFactory.create_llm(
        "ollama_llm",
        model="qwen2.5:latest",
        base_url="http://localhost:11434/v1",
        keep_alive=0,
        unload_at_exit=False
    )
    assert isinstance(llm, OllamaLLM)
    assert llm.model == "qwen2.5:latest"


def test_create_openai_compatible_llm():
    llm = LLMFactory.create_llm(
        "openai_compatible_llm",
        model="qwen2.5:latest",
        base_url="http://localhost:11434/v1",
        llm_api_key="none"
    )
    assert isinstance(llm, OpenAICompatibleLLM)
    assert llm.model == "qwen2.5:latest"


def test_unsupported_provider_raises():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        LLMFactory.create_llm("nonexistent_provider_xyz")


def test_transformers_llm_importable():
    from src.open_llm_vtuber.agent.stateless_llm.transformers_llm import TransformersLLM
    assert TransformersLLM is not None

