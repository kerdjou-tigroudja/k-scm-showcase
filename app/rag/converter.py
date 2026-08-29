"""
Deterministic HTML to UTF-8 TXT Converter for Regulatory Texts (EUR-Lex).
Version: 1.0.0
"""

import datetime
import hashlib
import os
import unicodedata

from bs4 import BeautifulSoup

CONVERTER_VERSION = "1.0.0 (BeautifulSoup4 html.parser + NFKC normalization)"


def compute_sha256(filepath: str) -> str:
    """Computes the uppercase SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().upper()


def extract_clean_text_from_html(html_content: str) -> str:
    """
    Parses HTML content, strips web boilerplate (scripts, styles, nav, footers, cookies),
    preserves titles, chapters, articles, paragraphs, lists, and normalizes whitespace.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove non-content tags
    for tag in soup(["script", "style", "header", "footer", "nav", "iframe", "noscript", "meta", "link"]):
        tag.decompose()

    # Remove elements with class or id containing cookie, banner, nav-menu, etc.
    for tag in soup.find_all(True):
        attrs_str = str(tag.get("class", "")) + " " + str(tag.get("id", ""))
        if any(b in attrs_str.lower() for b in ["cookie", "banner", "nav-menu", "top-bar"]):
            tag.decompose()

    # Extract text with newline separator for block elements
    raw_text = soup.get_text(separator="\n")

    # Normalize NFKC (converts non-breaking spaces \xa0 to standard spaces \x20, etc.)
    normalized_text = unicodedata.normalize("NFKC", raw_text)

    # Clean up whitespace line by line
    lines = [line.strip() for line in normalized_text.splitlines() if line.strip()]
    cleaned_text = "\n".join(lines) + "\n"

    return cleaned_text


def convert_html_file_to_txt(html_path: str, txt_path: str) -> dict:
    """
    Converts an official EUR-Lex HTML file into a clean, normalized UTF-8 TXT file.
    Returns conversion metadata including SHA-256 hashes and bytes count.
    """
    if not os.path.exists(html_path):
        raise FileNotFoundError(f"Source HTML file not found: {html_path}")

    html_bytes = os.path.getsize(html_path)
    html_sha256 = compute_sha256(html_path)

    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()

    cleaned_txt = extract_clean_text_from_html(html_content)

    os.makedirs(os.path.dirname(os.path.abspath(txt_path)), exist_ok=True)
    with open(txt_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(cleaned_txt)

    txt_bytes = os.path.getsize(txt_path)
    txt_sha256 = compute_sha256(txt_path)
    utc_timestamp = datetime.datetime.now(datetime.UTC).isoformat()

    return {
        "source_html_path": html_path,
        "source_html_bytes": html_bytes,
        "source_html_sha256": html_sha256,
        "derived_txt_path": txt_path,
        "derived_txt_bytes": txt_bytes,
        "derived_txt_sha256": txt_sha256,
        "derived_at_utc": utc_timestamp,
        "converter_version": CONVERTER_VERSION,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3:
        src, dst = sys.argv[1], sys.argv[2]
        res = convert_html_file_to_txt(src, dst)
        print(f"Converted {src} -> {dst}")
        print(f"HTML SHA256: {res['source_html_sha256']}")
        print(f"TXT SHA256:  {res['derived_txt_sha256']}")
    else:
        print("Usage: python -m app.rag.converter <source_html> <target_txt>")
