"""
Unit tests for deterministic HTML to TXT regulatory converter.
"""

import os
import tempfile

from app.rag.converter import (
    compute_sha256,
    convert_html_file_to_txt,
    extract_clean_text_from_html,
)

AI_ACT_HTML_PATH = "ressources/regulatory-corpus/raw/eu-ai-act/2024-1689/en/EU_AI_Act_Regulation_2024_1689_EN.html"
GDPR_HTML_PATH = "ressources/regulatory-corpus/raw/gdpr/2016-679/en/GDPR_Regulation_2016_679_EN.html"


def test_clean_text_extraction_removes_html_tags_and_preserves_articles():
    sample_html = """
    <html>
      <head>
        <style>body { color: red; }</style>
        <script>console.log("cookie banner");</script>
      </head>
      <body>
        <nav class="cookie-banner">Accept cookies</nav>
        <div class="doc-ti">Article 1</div>
        <p>Subject matter and scope of this Regulation.</p>
        <footer>Footer navigation</footer>
      </body>
    </html>
    """
    clean_txt = extract_clean_text_from_html(sample_html)
    assert "style" not in clean_txt
    assert "cookie" not in clean_txt
    assert "Article 1" in clean_txt
    assert "Subject matter and scope" in clean_txt
    assert "Footer navigation" not in clean_txt


def test_ai_act_html_conversion_quality_and_structure():
    assert os.path.exists(AI_ACT_HTML_PATH), f"Raw HTML file missing: {AI_ACT_HTML_PATH}"
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        res = convert_html_file_to_txt(AI_ACT_HTML_PATH, tmp_path)
        assert res["derived_txt_bytes"] > 400000
        assert res["source_html_sha256"] == "8F0B656302F9864CC87E040C371F209A9D65AE1A6CECC25CA5EB737E872D721A"

        with open(tmp_path, encoding="utf-8") as f:
            content = f.read()

        assert "Article 1" in content
        assert "Article 113" in content
        assert "Annex XIII" in content
        assert "<script" not in content
        assert "<html" not in content
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_gdpr_html_conversion_quality_and_structure():
    assert os.path.exists(GDPR_HTML_PATH), f"Raw HTML file missing: {GDPR_HTML_PATH}"
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        res = convert_html_file_to_txt(GDPR_HTML_PATH, tmp_path)
        assert res["derived_txt_bytes"] > 250000
        assert res["source_html_sha256"] == "962539AF03738BF552319FF4CE42D69E5F95A576307C4DFED7BF87E81B646B9D"

        with open(tmp_path, encoding="utf-8") as f:
            content = f.read()

        assert "Article 1" in content
        assert "Article 99" in content
        assert "<script" not in content
        assert "<html" not in content
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_converter_idempotence():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp1, \
         tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp2:
        tmp1_path = tmp1.name
        tmp2_path = tmp2.name

    try:
        res1 = convert_html_file_to_txt(GDPR_HTML_PATH, tmp1_path)
        res2 = convert_html_file_to_txt(GDPR_HTML_PATH, tmp2_path)

        hash1 = compute_sha256(tmp1_path)
        hash2 = compute_sha256(tmp2_path)

        assert hash1 == hash2 == res1["derived_txt_sha256"] == res2["derived_txt_sha256"]
    finally:
        for p in [tmp1_path, tmp2_path]:
            if os.path.exists(p):
                os.remove(p)
