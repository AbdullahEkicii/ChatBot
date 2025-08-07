import ijson
import json
import gzip
import sys
from datetime import datetime

# Hızlı JSON opsiyonel
try:
    import ujson as jsonlib     # pip install ujson
except ImportError:
    jsonlib = json

# 50 000 kayıtta bir rapor verelim
REPORT_STEP = 1_000_000

with open("veritabani.json", "r", encoding="utf-8") as infile, \
     gzip.open("veriseti.jsonl.gz", "wt", encoding="utf-8") as outfile:

    parser = ijson.items(infile, "sorular.item")
    line_no = 0                       # JSONL satır sayacı

    for item in parser:
        soru = item["soru"]
        cevaplar = item["cevap"]

        for cevap in cevaplar:
            satir = jsonlib.dumps({"soru": soru, "cevap": cevap}, ensure_ascii=False)
            outfile.write(satir + "\n")
            line_no += 1

            # Debug çıktısı
            if line_no % REPORT_STEP == 0:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[{ts}] {line_no:,} satır yazıldı...", file=sys.stderr)