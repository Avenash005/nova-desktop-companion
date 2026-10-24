"""
Unit tests for English localization and frontend assets.
"""

import os
import re
import pytest


def test_index_html_branding():
    assert os.path.exists("frontend/index.html")
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    assert "NOVA — Neural Desktop Companion" in html
    assert "Open-LLM-Vtuber" not in html


def test_frontend_bundle_clean_english():
    js_path = "frontend/assets/main-nu7uwxNJ.js"
    assert os.path.exists(js_path)
    with open(js_path, "r", encoding="utf-8") as f:
        js_content = f.read()

    # Verify that key Chinese strings have been replaced
    forbidden_chinese = [
        "Open LLM VTuber 前端",
        "WebSocket未连接",
        "AI无法听到您的声音",
        "暂无消息。开始对话吧！",
        "输入您的消息...",
        "聊天历史列表",
        "角色预设",
        "设置",
    ]
    for phrase in forbidden_chinese:
        assert phrase not in js_content, f"Found untranslated Chinese phrase in bundle: '{phrase}'"

    # Verify English translations are present
    expected_english = [
        "NOVA Companion Frontend",
        "WebSocket Not Connected",
        "Type your message to NOVA...",
        "No messages yet. Start your conversation with NOVA!",
        "Chat History"
    ]
    for phrase in expected_english:
        assert phrase in js_content, f"Expected English phrase missing from bundle: '{phrase}'"
