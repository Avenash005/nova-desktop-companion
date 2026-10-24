"""
Unit tests for NOVA configuration and character profiles.
"""

import os
import re
import pytest
from src.open_llm_vtuber.config_manager import validate_config, read_yaml


def test_conf_yaml_exists():
    assert os.path.exists("conf.yaml"), "conf.yaml must exist in the project root."


def test_conf_yaml_has_no_chinese_characters():
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    with open("conf.yaml", "r", encoding="utf-8") as f:
        content = f.read()
    matches = chinese_pattern.findall(content)
    assert len(matches) == 0, f"Expected 0 Chinese characters in conf.yaml, found {len(matches)}: {matches}"


def test_conf_yaml_structure_and_nova_branding():
    config = validate_config(read_yaml("conf.yaml"))
    char_cfg = config.character_config
    assert char_cfg.character_name == "NOVA", f"Expected character_name to be 'NOVA', got {char_cfg.character_name}"
    assert "nova" in char_cfg.conf_name.lower() or "nova" in char_cfg.character_name.lower()
    assert char_cfg.avatar == "nova.png", "Expected avatar to be 'nova.png'"
    assert "friendly, intelligent" in char_cfg.persona_prompt.lower() or "nova" in char_cfg.persona_prompt.lower()


def test_nova_character_alt_config():
    assert os.path.exists("characters/nova.yaml"), "characters/nova.yaml must exist"
    data = read_yaml("characters/nova.yaml")
    char_cfg = data["character_config"]
    assert char_cfg["character_name"] == "NOVA"
    assert char_cfg["avatar"] == "nova.png"
    assert char_cfg["tts_config"]["edge_tts"]["voice"] == "en-US-AvaMultilingualNeural"
