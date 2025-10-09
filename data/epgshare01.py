#!/usr/bin/env python3
import io, json, re, sys, requests
from pathlib import Path
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter

PDF_URL      = "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.pdf"
OUTPUT_FILE  = Path(__file__).with_name("tvg-ids.json")

# ─── filters ────────────────────────────────────────────────────────────────────
RE_TIMESTAMP     = re.compile(r"^\d+$")
RE_RIPPER_HEADER = re.compile(r"^--\s*epg_ripper_", re.I)
RE_BANNER        = re.compile(r"^--.*--$")

def fetch_pdf(url: str) -> bytes:
    print("📥  Downloading PDF …")
    with requests.get(url, timeout=60) as r:
        r.raise_for_status()
        return r.content               # bytes

def channel_lines(pdf_bytes: bytes):
    """Yield cleaned channel lines page-by-page to stay memory-light."""
    laparams = LAParams()
    resource_mgr = PDFResourceManager()
    with io.BytesIO(pdf_bytes) as fh:
        for page in PDFPage.get_pages(fh, caching=False, check_extractable=True):
            with io.StringIO() as out_str:
                device = TextConverter(resource_mgr, out_str, laparams=laparams)
                interpreter = PDFPageInterpreter(resource_mgr, device)
                interpreter.process_page(page)
                device.close()
                for raw in out_str.getvalue().splitlines():
                    line = raw.strip()
                    if (not line or
                        RE_TIMESTAMP.fullmatch(line) or
                        RE_RIPPER_HEADER.match(line) or
                        RE_BANNER.match(line)):
                        continue
                    yield line
    # Explicitly close resource manager pools (avoids hanging threads)
    if hasattr(resource_mgr, "cleanup"):
        resource_mgr.cleanup()

def write_json_stream(lines, outfile: Path):
    with outfile.open("w", encoding="utf-8") as out:
        out.write("{\n")
        current_region = None
        first_region   = True
        first_channel  = True
        next_id        = 1
        seen           = set()

        for chan in lines:
            if chan in seen:
                continue
            seen.add(chan)

            region = chan.rsplit(".", 1)[-1].lower()
            if region != current_region:
                if not first_region:
                    out.write("\n  },\n")
                out.write(f'  "{region}": {{\n')
                current_region = region
                first_region   = False
                first_channel  = True

            if not first_channel:
                out.write(",\n")
            out.write(f'    "{chan}": {next_id}')
            next_id += 1
            first_channel = False

        if not first_region:
            out.write("\n  }\n")
        out.write("}\n")
    print(f"✅  {outfile} written ({next_id-1} channel IDs)")

def main():
    pdf_bytes = fetch_pdf(PDF_URL)
    lines     = channel_lines(pdf_bytes)
    write_json_stream(lines, OUTPUT_FILE)
    print("🎉  Done!")
    sys.exit(0)   # <- ensure interpreter terminates even if threads linger

if __name__ == "__main__":
    main()
