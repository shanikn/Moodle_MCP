from datetime import datetime

from moodle_mcp.formatting import browser_url, file_list, fmt_date, html_to_text


def test_fmt_date():
    assert fmt_date(0) is None
    assert fmt_date(int(datetime(2026, 5, 4, 23, 59).timestamp())) == "2026-05-04 23:59"


def test_html_to_text_keeps_paragraphs_and_unescapes():
    assert html_to_text("<p>Hello&nbsp;all,</p><p>HW&nbsp;1 is <b>graded</b></p>") == "Hello\xa0all,\nHW\xa01 is graded"
    assert html_to_text("48.00&nbsp;/&nbsp;100.00") == "48.00\xa0/\xa0100.00"
    assert html_to_text(None) == ""


def test_browser_url_drops_webservice_prefix():
    assert browser_url("https://m/2026/webservice/pluginfile.php/1/a.pdf") == "https://m/2026/pluginfile.php/1/a.pdf"


def test_file_list_skips_editpdf_page_images():
    areas = [{"files": [
        {"filename": "combined.pdf", "fileurl": "https://m/webservice/pluginfile.php/c.pdf"},
        {"filename": "image_page0.png", "fileurl": "https://m/webservice/pluginfile.php/i.png"},
    ]}]
    assert file_list(areas) == [{"filename": "combined.pdf", "url": "https://m/pluginfile.php/c.pdf"}]
