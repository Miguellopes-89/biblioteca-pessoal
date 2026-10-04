# Biblioteca Pessoal

[![CI](https://github.com/Miguellopes-89/biblioteca-pessoal/actions/workflows/ci.yml/badge.svg)](https://github.com/Miguellopes-89/biblioteca-pessoal/actions/workflows/ci.yml)

A desktop application to catalog a personal book collection, built with Python and PySide6. Add books manually or look them up automatically by ISBN, browse and search your collection, and track what you've read — all stored locally, no internet connection required once a book is in your library.

This is a self-driven portfolio project built while transitioning into software development.

## Features

- **Full CRUD** — add, list, search, edit, and remove books
- **Automatic ISBN lookup** — fetches title, author(s), publisher, and genre from the Google Books API, falling back to Open Library if the first lookup doesn't find a match. Runs on a background thread so the interface never freezes while waiting on the network.
- **Multiple authors per book**, stored as a proper many-to-many relationship (not a flat text field)
- **ISBN validation** — checks the ISBN-10/ISBN-13 check digit before spending a network call, so typos are caught early
- **Cover preview** — shows the book cover after an ISBN lookup, when the APIs provide one
- **Optional web interface** (Flask) — the same library in a browser, with list, search, add, edit, remove and ISBN lookup, running on the same database as the desktop app
- **Accent- and punctuation-insensitive search** — searching "meditacoes" finds "Meditações"
- **Reading status tracking** (not read / reading / read)
- **Fully offline** after a book is added — the SQLite database is local, no server or account needed
- **No API key required** — both Google Books and Open Library are queried through their free, keyless public endpoints

## Tech stack

- **Python 3.14**
- **PySide6** (Qt for Python) — desktop GUI
- **SQLite** — local storage, accessed through the standard library `sqlite3` module
- **`urllib.request`** (standard library) — ISBN lookups, with no external HTTP dependency
- **Flask** — optional web interface
- **Docker** and **gunicorn** — containerized web interface with a persistent volume
- **pytest**, **basedpyright** and **GitHub Actions** — automated tests, static type checking and continuous integration

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

### Web interface (optional)

```bash
pip install -r requirements-web.txt
python web/app.py
```

Then open <http://127.0.0.1:5000>. This runs Flask's development server in debug mode, so it is meant for local use only — do not expose it to a network.

### Web interface with Docker (optional)

Requires Docker. The image runs the web interface under `gunicorn`, a production WSGI server, as a non-root user, and keeps the SQLite database in a Docker volume so your books survive container restarts.

```bash
docker build -t biblioteca-web .
docker run --rm -p 8000:8000 -v biblioteca-data:/data biblioteca-web
```

Then open <http://localhost:8000>. The container uses its own database (the `biblioteca-data` volume, selected through the `BIBLIOTECA_DB` environment variable), separate from the `biblioteca.db` used by the desktop app. Note that the remove button has no CSRF protection, which is acceptable on localhost but should be added before exposing the app to a network.

### Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests cover ISBN validation, text normalization and the data layer. Data-layer tests run against a temporary database, never against your real library. GitHub Actions runs the tests and the type checker on every push.

## Project structure

```
biblioteca-pessoal/
├── gui.py                # PySide6 desktop interface (QMainWindow)
├── database.py           # SQLite data layer: schema, CRUD, search
├── isbn_lookup.py        # ISBN validation + lookup: Google Books + Open Library, with retry
├── web/                  # optional Flask interface (reuses database.py and isbn_lookup.py)
│   ├── app.py
│   └── templates/
├── tests/                # pytest suite
├── Dockerfile            # container image for the web interface (gunicorn)
├── .dockerignore         # keeps the database and secrets out of the image
├── .github/workflows/    # CI: tests + type checking
├── main.py               # original environment smoke test (not used by the GUI)
├── requirements.txt      # desktop app
├── requirements-web.txt  # web interface
├── requirements-dev.txt  # tests and type checking
└── pyrightconfig.json    # type checker configuration
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

- Tests for the web routes, and for the ISBN lookup against recorded API responses

## License

MIT — see [LICENSE](LICENSE).
