# Affinity Answers — Data Engineer (Intern) Take-Home

Solutions to the three questions: a Python web scraper, SQL against the
public Rfam database, and a Unix shell script.

Tested on macOS (should work the same on Linux). Requires Python 3.9+,
`curl`, `awk`, `sort` and a MySQL client for Q2.

---

## Q1 — Python: MD Computers product scraper

Scrapes product listings from https://mdcomputers.in for a search term.

### Setup and run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r q1_web_scraper/requirements.txt

python q1_web_scraper/mdcomputers_scraper.py "external hard drive"
python q1_web_scraper/mdcomputers_scraper.py "ssd" --pages 3 --output ssd.csv
```

### Sample output

```
name,price_inr,mrp_inr,discount_label,product_url
Seagate Expansion 1TB External Hard Drive,9140,10000,-9%,https://mdcomputers.in/product/seagate-expansion-1tb-external-hard-drive-stkm1000400
WD Elements 1TB External Hard Drive,9280,14000,-34%,https://mdcomputers.in/product/wd-elements-1tb-external-hard-drive-wdbhhg0010bbk-eesn
```

### Design choices

- **Why `curl_cffi` instead of `requests`:** the site is behind Cloudflare
  bot protection which fingerprints the TLS handshake. Plain `requests`
  and `urllib` get HTTP 403 (verified). `curl_cffi` sends the request with
  a real Chrome TLS fingerprint, so the page loads like it does in a
  browser. No other workaround (headers, user-agent) was enough.
- **Why CSV output:** the extracted data is flat and tabular (one row per
  product), and CSV is the least-friction format for downstream use — it
  opens in Excel, loads into pandas/a database in one line, and diffs
  cleanly. Writing to stdout by default lets you pipe it (`| head`,
  `| grep`), and `--output` saves it to a file.
- **Prices are cleaned to plain integers** (`₹10,000` → `10000`) so the
  column is immediately usable for sorting/aggregation — no downstream
  regex needed. The discount label is kept as displayed (`-9%`).
- **Pagination** is supported via `--pages N` (default 1). The scraper
  reads the real page count from the "(N Pages)" footer and never fetches
  beyond it.
- **Failure behaviour:** non-200 responses and empty result sets exit
  non-zero with a message on stderr, so the script is safe to use in a
  pipeline.

---

## Q2 — SQL: Rfam database

Queries live in `q2_sql/`, one file per question, each with the verified
result in its header comment. Run them against the public server:

```bash
mysql --user rfamro --host mysql-rfam-public.ebi.ac.uk --port 4497 --database Rfam < q2_sql/1_acacia_count.sql
```

| # | Question | Answer (verified Sep 2026) |
|---|----------|----------------------------|
| 1 | Types of Acacia in `taxonomy` | **326** |
| 2 | Wheat type with the longest DNA sequence | **Triticum durum (durum wheat)** — 836,514,780 bp |
| 3 | Page 9 (15/page) of families with max sequence length > 1,000,000 | 15 rows, `RF01284 snoR8a` … `RF04335 Plastid-rpl20` (see file) |

Notes:

- Q2.2 matches wheat by `tax_string LIKE '%Triticum%'` (wheat = genus
  *Triticum*), joins `rfamseq` to `taxonomy` on `ncbi_id`, and takes the
  longest sequence.
- Q2.3 pages with `LIMIT 15 OFFSET 120` (page 9 → skip 8 × 15 rows), and
  keeps only significant hits (`is_significant = 1`) as the Rfam docs
  recommend. `full_region` is large, so this query takes a few minutes on
  the shared public server.

---

## Q3 — Shell: S&P 500 company info

```bash
./q3_shell/company_info.sh "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/refs/heads/main/data/constituents.csv"
```

Prints `company name <TAB> headquarters location <TAB> founding year`,
sorted by founding year:

```
State Street Corporation	Boston, Massachusetts	1792
Colgate-Palmolive	New York City, New York	1806
...
Qnity Electronics	Wilmington, Delaware	2025
```

### Design choices

- The CSV has commas inside quoted fields (`"Saint Paul, Minnesota"`,
  `"Block, Inc."`), so a plain `awk -F,` split would corrupt rows. The
  script parses each line with a small quote-aware awk function instead —
  portable across BSD awk (macOS) and gawk (Linux), no extra tools needed.
- The `Founded` column can be `2013 (1888)` or `2020 (1915, ... spinoff)`;
  the first 4-digit number is taken as the founding year of the listed
  entity.
- `set -euo pipefail` + `curl -f` make the script fail loudly (non-zero
  exit) on a bad URL or download error instead of printing partial data.

---

## Repository layout

```
q1_web_scraper/   mdcomputers_scraper.py, requirements.txt
q2_sql/           1_acacia_count.sql, 2_longest_wheat_sequence.sql, 3_family_pagination.sql
q3_shell/         company_info.sh
```
