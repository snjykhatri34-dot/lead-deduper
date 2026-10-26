# Lead Deduper

Merge the same lead from your trade-show list, LinkedIn export, website form and cold list into **one clean record**, then score each lead on how reachable it is.

Pure Python, no dependencies, works on plain CSVs.

```
$ python -m lead_deduper data/sample_leads.csv -o clean_leads.csv

16 rows in -> 11 unique leads (5 duplicates merged into 5 records)

Merged:
  Priya Shah             ids 1, 2             same phone; similar name at same company (100%)
  Elena Ruiz             ids 5, 6             same email; similar name at same company (100%)
  Owen Brooks            ids 15, 16           same phone; similar name at same company (100%)
  Marcus Bell            ids 3, 4             similar name at same company (95%)
  Tom Nguyen             ids 7, 8             same email; similar name at same company (87%)

Top leads:
  100  Priya Shah             Sunset Inn LLC             business email, phone, company, decision maker
  100  Elena Ruiz             Ruiz Hospitality Group     business email, phone, company, decision maker
  ...

Wrote 11 leads to clean_leads.csv
```

## What counts as a duplicate

Two rows are the same person if any of these is true:

| Rule | Catches |
|---|---|
| **Same email** after normalising | `ELENA@Ruiz.example` = `elena@ruiz.example`; Gmail dots and `+tags` (`tom.nguyen+leads@gmail.com` = `tomnguyen@gmail.com`) |
| **Same phone** after normalising | `(512) 555-0142` = `+1 512-555-0142` = `512.555.0142` |
| **Similar name at the same company** | `Shah, Priya` at *Sunset Inn LLC* = `Priya Shah` at *Sunset Inn*; `Marcus Bel` = `Marcus Bell` |

The fuzzy name rule is skipped when the two rows have **different phone numbers or different work emails**. That's what keeps *Raj Patel* and *Rajesh Patel* at Patel Motels apart: similar names, but clearly two people.

Matches chain together: if row A matches B by email and B matches C by phone, all three become one lead.

## How records are merged

The most complete row wins. Any field it's missing is filled from the other rows, and every source is kept (`Trade show; LinkedIn`). The output adds four columns:

| Column | Meaning |
|---|---|
| `merged_ids` | Original row IDs that went into this lead |
| `match_reasons` | Why they were merged, so you can audit it |
| `score` | 0 to 100, how reachable and relevant the lead is |
| `score_notes` | What the score is made of |

## Scoring

| Signal | Points |
|---|---|
| Business email (not Gmail, Yahoo, etc.) | 35 (personal email: 15) |
| Phone number | 25 |
| Company name | 15 |
| Decision-maker title (owner, founder, CEO, president, director, partner, GM) | 25 (any other title: 10) |

Edit `score_lead` in `lead_deduper/dedupe.py` to match your own sales process.

## Usage

Requires Python 3.9+.

```bash
git clone https://github.com/snjykhatri34-dot/lead-deduper.git
cd lead-deduper
python -m lead_deduper list1.csv list2.csv -o clean_leads.csv
```

| Option | Meaning |
|---|---|
| `-o FILE` | Write the merged, scored list to a CSV. Without it you only get the summary. |
| `--threshold 0.85` | How similar names must be (0 to 1) for the fuzzy rule. Lower catches more typos but risks false merges. |

Input columns: `id, name, email, phone, company, title, source`. Missing columns are treated as blank. The sample file uses fictional people and `.example` domains.

## Tests

```bash
python -m unittest discover -s tests -t .
```

## License

MIT
