# Excel seed importer

The importer is **dry-run by default** and does not connect to PostgreSQL unless `--commit` is passed.

## Dependency

```bash
pip install python-calamine
```

`python-calamine` reads `.xlsm` directly and supports Python 3.14.

## 1. Dry run

From the backend project root:

```bash
python import_excel.py /path/to/FILME-V1.1.xlsm --report-dir import_report
```

Generated reports:

- `summary.json` — counts and overall status
- `warnings.csv` — cleaning/data-quality findings
- `movies_preview.csv` — normalized public movie data before DB insert
- `personal_pending.csv` — legacy own-rating/watched data, deliberately not assigned to any user
- `genres.txt`, `countries.txt`, `people.txt` — unique normalized values for review

## 2. Explicit cleaning overrides

Copy `import_overrides.example.json` and add only replacements you explicitly approve:

```json
{
  "genre_map": {
    "Thiller": "Thriller"
  },
  "country_map": {},
  "person_map": {},
  "title_map": {}
}
```

Then rerun:

```bash
python import_excel.py FILME-V1.1.xlsm \
  --overrides import_overrides.json \
  --report-dir import_report
```

No typo is silently corrected by the importer.

## 3. Optional poster enrichment

Poster URLs from the workbook's `Fotos FP` sheet are intentionally opt-in:

```bash
python import_excel.py FILME-V1.1.xlsm --include-images
```

Ambiguous title→poster matches are reported and not guessed.

## 4. Commit

Run this only from the backend project where `app.models` and `app.db.session` exist:

```bash
python import_excel.py FILME-V1.1.xlsm \
  --overrides import_overrides.json \
  --commit
```

Commit is blocked when error-level findings remain. Ordinary warnings also block commit unless explicitly accepted:

```bash
python import_excel.py FILME-V1.1.xlsm \
  --overrides import_overrides.json \
  --commit \
  --allow-warnings
```

DB duplicate candidates abort the import by default. To intentionally skip already-existing candidates:

```bash
... --commit --skip-duplicates
```

## Personal legacy ratings

`Eigene Bewertung` and `Gesehen?` are not written to `UserMovie`, because they first need to be assigned to the correct user. The importer converts recognizable star/half-star strings to `0–100` only in `personal_pending.csv` so they can later appear as 0–5 half-step **Bricks** in the React UI.
