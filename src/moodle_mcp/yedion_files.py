# opens Yedion's PDF files (exam papers, exam-bank files, scanned notebooks) as page images plus any
# text layer. Everything stays in memory: PDFs and rendered pages are never written to disk or cached.
import html
import io
import re

import pypdfium2 as pdfium

MAX_PAGES = 10      # per call; more pages = another call with first_page
LONG_EDGE = 1400    # px; Claude scales larger images down anyway
JPEG_QUALITY = 70


def hidden_fields(page: str) -> dict[str, str]:
    """The page form's hidden fields (TZ, Token, ...), which a file button posts along with its
    arguments. They identify the student: never return or log them."""
    return {name: value for name, value in re.findall(r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', page)
            if name not in ("PRGNAME", "ARGUMENTS")}


def button_arguments(cell: str, progname: str, kind: str | None = None) -> str | None:
    """data-arguments of the first `progname` button in a result cell (with `kind` as the third
    argument part when given, e.g. "-N10" for the exam bank's download button)."""
    for attrs in re.findall(rf'<button[^>]*data-progname="{progname}"[^>]*>', cell):
        args = re.search(r'data-arguments="([^"]*)"', attrs)
        if args:
            value = html.unescape(args.group(1))
            if kind is None or value.split(",")[2:3] == [kind]:
                return value
    return None


def render_pages(pdf: bytes, first_page: int = 1, last_page: int | None = None) -> tuple[dict, list[bytes]]:
    """Render pages first_page..last_page (1-based, at most MAX_PAGES) to JPEG bytes and collect
    any text layer. Returns ({"pages_total", "pages": [first, last], "text": {page: text},
    "next_first_page"?}, [jpeg, ...])."""
    try:
        document = pdfium.PdfDocument(pdf)  # from the bytes in memory, no temporary file
    except pdfium.PdfiumError:
        raise ValueError("Yedion's file could not be read as a PDF.") from None
    try:
        total = len(document)
        if first_page < 1 or first_page > total:
            raise ValueError(f"first_page must be between 1 and {total} (the file has {total} pages).")
        last = min(last_page if last_page is not None else first_page + MAX_PAGES - 1, total)
        if last < first_page:
            raise ValueError(f"last_page must be at least first_page ({first_page}).")
        if last - first_page + 1 > MAX_PAGES:
            raise ValueError(f"At most {MAX_PAGES} pages per call; ask for {first_page}-{first_page + MAX_PAGES - 1}, "
                             f"then continue from {first_page + MAX_PAGES}.")
        images, text = [], {}
        for index in range(first_page - 1, last):
            page = document[index]
            try:
                width, height = page.get_size()
                bitmap = page.render(scale=LONG_EDGE / max(width, height))
                buffer = io.BytesIO()
                bitmap.to_pil().convert("RGB").save(buffer, "JPEG", quality=JPEG_QUALITY, optimize=True)
                images.append(buffer.getvalue())
                textpage = page.get_textpage()
                words = textpage.get_text_range().strip()
                textpage.close()
                if words:
                    text[str(index + 1)] = words
            finally:
                page.close()
    except pdfium.PdfiumError:
        raise ValueError("Yedion's file could not be read as a PDF.") from None
    finally:
        document.close()
    info = {"pages_total": total, "pages": [first_page, last], "text": text}
    if last < total:
        info["next_first_page"] = last + 1
    return info, images

