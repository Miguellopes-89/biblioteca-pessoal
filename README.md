# Biblioteca Pessoal

A desktop application to catalog a personal book collection, built with Python and PySide6. Add books manually or look them up automatically by ISBN, browse and search your collection, and track what you've read — all stored locally, no internet connection required once a book is in your library.

This is a self-driven portfolio project built while transitioning into software development.

## Features

- **Full CRUD** — add, list, search, edit, and remove books
- **Automatic ISBN lookup** — fetches title, author(s), publisher, and genre from the Google Books API, falling back to Open Library if the first lookup doesn't find a match. Runs on a background thread so the interface never freezes while waiting on the network.
- **Multiple authors per book**, stored as a proper many-to-many relationship (not a flat text field)
- **Accent- and punctuation-insensitive search** — searching "meditacoes" finds "Meditações"
- **Reading status tracking** (not read / reading / read)
- **Fully offline** after a book is added — the SQLite database is local, no server or account needed
- **No API key required** — both Google Books and Open Library are queried through their free, keyless public endpoints

## Tech stack

- **Python 3.14**
- **PySide6** (Qt for Python) — desktop GUI
- **SQLite** — local storage, accessed through the standard library `sqlite3` module
- **`urllib.request`** (standard library) — ISBN lookups, with no external HTTP dependency

## Getting started

### Prerequisites

- Python 3.10 or newer (developed and tested on 3.14)
- Git

### Installation

```bash
git clone https://github.com/Miguellopes-89/biblioteca-pessoal.git
cd biblioteca-pessoal

python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Running

```bash
python gui.py
```

The SQLite database (`biblioteca.db`) and its tables are created automatically on first run.

## Project structure

```
biblioteca-pessoal/
├── gui.py            # PySide6 desktop interface (QMainWindow)
├── database.py        # SQLite data layer: schema, CRUD, search
├── isbn_lookup.py      # ISBN lookup: Google Books + Open Library, with retry
├── main.py            # original environment smoke test (not used by the GUI)
├── requirements.txt
└── pyrightconfig.json   # points the linter at the project's venv
```

## Data model

Three tables, supporting a proper many-to-many relationship between books and authors:

- **`livros`** (books) — id, title, publisher, collection/series, genre, ISBN (unique), reading status
- **`autores`** (authors) — id, name (unique)
- **`livro_autor`** (book_author) — join table linking books to authors

ISBN is the sole duplicate-detection key (each edition of a book has its own ISBN). Authors are matched case-insensitively when a book is added, so "J.R.R. Tolkien" and "j.r.r. tolkien" resolve to the same author record.

## Notes on the ISBN lookup

- Neither Google Books nor Open Library reliably expose a book's *collection/series* — that field always needs to be filled in manually.
- The Google Books public endpoint (used without an API key) shares a global daily quota across all anonymous users worldwide, so it can occasionally return "quota exceeded." The Open Library fallback exists specifically to cover that case.
- Network requests use `urllib.request` from the standard library, with automatic retries on transient failures.

## Roadmap

- Web version (Flask/FastAPI + Docker) as a possible future phase
- ISBN checksum validation before querying the APIs
- Book cover thumbnails (both APIs return cover image URLs already)

## License

MIT — see [LICENSE](LICENSE).
