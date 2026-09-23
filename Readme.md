# Book API

A simple Flask REST API for searching, filtering, viewing, and exporting books using the [Open Library API](https://openlibrary.org/developers/api).

The project is intentionally small and simple. It does not use a database, authentication system, microservices, or a complex architecture.

---

## Features

* Search books
* Search by title, author, subject, and language
* Filter by publication year
* Filter by page count
* Sort results
* Pagination
* Get detailed information about a book/work
* Export search results to CSV
* Input validation
* JSON error responses

---

# Requirements

* Python 3.10+
* Flask
* Requests

---

# Installation

Clone the project:

```bash
git clone <repository-url>
cd book-api
```

Create a virtual environment.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Running the API

Start the Flask development server:

```bash
python app.py
```

The API will be available at:

```text
http://127.0.0.1:5000
```

---

# API Overview

The API provides three endpoints:

| Method | Endpoint               | Description                  |
| ------ | ---------------------- | ---------------------------- |
| `GET`  | `/api/books/search`    | Search and filter books      |
| `GET`  | `/api/books/{work_id}` | Get details of a book/work   |
| `GET`  | `/api/books/export`    | Export search results as CSV |

---

# 1. Search Books

## Endpoint

```http
GET /api/books/search
```

This endpoint searches books using the Open Library Search API.

It supports text search, filters, sorting, and pagination.

---

## Query Parameters

| Parameter   | Type    | Required | Default | Description              |
| ----------- | ------- | -------- | ------- | ------------------------ |
| `q`         | string  | No       | `""`    | General search query     |
| `title`     | string  | No       | -       | Search by title          |
| `author`    | string  | No       | -       | Search by author         |
| `subject`   | string  | No       | -       | Search by subject        |
| `language`  | string  | No       | -       | Filter by language       |
| `year_from` | integer | No       | -       | Minimum publication year |
| `year_to`   | integer | No       | -       | Maximum publication year |
| `min_pages` | integer | No       | -       | Minimum page count       |
| `max_pages` | integer | No       | -       | Maximum page count       |
| `sort`      | string  | No       | -       | Sort results             |
| `page`      | integer | No       | `1`     | Page number              |
| `limit`     | integer | No       | `20`    | Number of results        |

---

## Text Search

### General Search

```http
GET /api/books/search?q=python
```

Example:

```text
http://127.0.0.1:5000/api/books/search?q=python
```

The `q` parameter can be used for a general search.

For example:

```text
q=python
q=harry potter
q=machine learning
```

---

## Search by Title

```http
GET /api/books/search?title=Python
```

Example:

```text
http://127.0.0.1:5000/api/books/search?title=Python
```

---

## Search by Author

```http
GET /api/books/search?author=Eric Matthes
```

Example:

```text
http://127.0.0.1:5000/api/books/search?author=Eric%20Matthes
```

---

## Search by Subject

```http
GET /api/books/search?subject=programming
```

Example:

```text
http://127.0.0.1:5000/api/books/search?subject=programming
```

---

## Filter by Language

Use an Open Library language code.

For example:

```text
eng
```

Request:

```http
GET /api/books/search?q=python&language=eng
```

---

# Publication Year Filters

Two parameters are available:

```text
year_from
year_to
```

### Books published from 2000

```http
GET /api/books/search?q=python&year_from=2000
```

### Books published before 2020

```http
GET /api/books/search?q=python&year_to=2020
```

### Books published between 2000 and 2020

```http
GET /api/books/search?q=python&year_from=2000&year_to=2020
```

`year_from` cannot be greater than `year_to`.

For example:

```text
year_from=2025&year_to=2000
```

returns:

```json
{
  "error": "year_from cannot be greater than year_to"
}
```

with HTTP status:

```text
400 Bad Request
```

---

# Page Count Filters

The API supports:

```text
min_pages
max_pages
```

### At least 300 pages

```http
GET /api/books/search?q=python&min_pages=300
```

### At most 500 pages

```http
GET /api/books/search?q=python&max_pages=500
```

### Between 300 and 500 pages

```http
GET /api/books/search?q=python&min_pages=300&max_pages=500
```

---

## Unknown Page Counts

Open Library does not always provide page-count information.

When the page count is unavailable, the API returns:

```json
"pages": "N/A"
```

For example:

```json
{
  "title": "Python Crash Course",
  "pages": "N/A"
}
```

A book with an unknown page count is **not removed** when `min_pages` or `max_pages` is used.

For example:

```http
GET /api/books/search?q=python&min_pages=500
```

If a book has:

```json
"pages": "N/A"
```

it will still appear in the results.

This is because `N/A` means that the page count is unknown, not that the book failed the filter.

If the page count is known, the page filter is applied normally.

---

# Sorting

The `sort` parameter supports six values:

```text
year_asc
year_desc

pages_asc
pages_desc

title_asc
title_desc
```

### Oldest books first

```http
GET /api/books/search?q=python&sort=year_asc
```

### Newest books first

```http
GET /api/books/search?q=python&sort=year_desc
```

### Fewest pages first

```http
GET /api/books/search?q=python&sort=pages_asc
```

### Most pages first

```http
GET /api/books/search?q=python&sort=pages_desc
```

### Alphabetical order

```http
GET /api/books/search?q=python&sort=title_asc
```

### Reverse alphabetical order

```http
GET /api/books/search?q=python&sort=title_desc
```

---

# Pagination

Pagination uses:

```text
page
limit
```

`page` starts from `1`.

`limit` must be between `1` and `100`.

### First page with 20 results

```http
GET /api/books/search?q=python&page=1&limit=20
```

### Second page with 20 results

```http
GET /api/books/search?q=python&page=2&limit=20
```

### Maximum page size

```http
GET /api/books/search?q=python&limit=100
```

---

# Combining Parameters

All search parameters can be combined.

For example:

```http
GET /api/books/search?q=python&language=eng&year_from=2010&year_to=2025&min_pages=200&max_pages=800&sort=year_desc&page=1&limit=20
```

This request means:

* Search for `python`
* English books
* Published between 2010 and 2025
* Minimum 200 pages
* Maximum 800 pages
* Newest books first
* First page
* 20 results

---

# Search Response

A successful request returns JSON.

Example:

```json
{
  "total": 2,
  "page": 1,
  "limit": 20,
  "books": [
    {
      "work_id": "OL123456W",
      "title": "Python Crash Course",
      "authors": [
        "Eric Matthes"
      ],
      "first_publish_year": 2015,
      "pages": "N/A",
      "languages": [
        "eng"
      ],
      "subjects": [
        "Python",
        "Programming"
      ]
    },
    {
      "work_id": "OL654321W",
      "title": "Fluent Python",
      "authors": [
        "Luciano Ramalho"
      ],
      "first_publish_year": 2015,
      "pages": 792,
      "languages": [
        "eng"
      ],
      "subjects": [
        "Python",
        "Programming"
      ]
    }
  ]
}
```

### Response Fields

| Field   | Description                                    |
| ------- | ---------------------------------------------- |
| `total` | Number of books returned after local filtering |
| `page`  | Current page                                   |
| `limit` | Requested result limit                         |
| `books` | List of books                                  |

Each book contains:

| Field                | Description              |
| -------------------- | ------------------------ |
| `work_id`            | Open Library Work ID     |
| `title`              | Book title               |
| `authors`            | List of authors          |
| `first_publish_year` | First publication year   |
| `pages`              | Page count or `N/A`      |
| `languages`          | Available language codes |
| `subjects`           | Book subjects            |

---

# 2. Get Book Details

## Endpoint

```http
GET /api/books/{work_id}
```

This endpoint returns detailed information about an Open Library Work.

The `work_id` can be obtained from the search endpoint.

For example:

```json
{
  "work_id": "OL123456W"
}
```

You can then request:

```http
GET /api/books/OL123456W
```

Example:

```text
http://127.0.0.1:5000/api/books/OL123456W
```

The API requests the Work directly from Open Library and returns its data.

---

# 3. Export Books to CSV

## Endpoint

```http
GET /api/books/export
```

This endpoint exports search results as a CSV file.

It supports the same search, filtering, sorting, and pagination parameters as the search endpoint.

---

## Example

```http
GET /api/books/export?q=python
```

A file named:

```text
books.csv
```

will be returned.

---

## Advanced CSV Export

For example:

```http
GET /api/books/export?q=python&language=eng&year_from=2010&year_to=2025&min_pages=200&sort=year_desc&limit=100
```

This exports:

* English books
* Related to Python
* Published from 2010 to 2025
* At least 200 pages
* Sorted by newest publication year
* Up to 100 results

---

## CSV Columns

The generated CSV contains:

```text
work_id
title
authors
first_publish_year
pages
languages
subjects
```

Example:

```csv
work_id,title,authors,first_publish_year,pages,languages,subjects
OL123456W,Python Crash Course,Eric Matthes,2015,N/A,eng,Python;Programming
OL654321W,Fluent Python,Luciano Ramalho,2015,792,eng,Python;Programming
```

---

# Validation and Errors

The API validates request parameters before sending requests to Open Library.

All validation errors return:

```text
400 Bad Request
```

---

## Invalid Integer

Parameters that expect integers must contain valid integer values.

Affected parameters:

```text
year_from
year_to
min_pages
max_pages
page
limit
```

For example:

```http
GET /api/books/search?q=python&min_pages=abc
```

returns:

```json
{
  "error": "min_pages must be an integer"
}
```

---

## Invalid Page Range

`min_pages` cannot be greater than `max_pages`.

Invalid:

```text
min_pages=500
max_pages=100
```

Response:

```json
{
  "error": "min_pages cannot be greater than max_pages"
}
```

---

## Invalid Year Range

`year_from` cannot be greater than `year_to`.

Invalid:

```text
year_from=2025
year_to=2000
```

Response:

```json
{
  "error": "year_from cannot be greater than year_to"
}
```

---

## Negative Page Count

`min_pages` and `max_pages` cannot be negative.

Invalid:

```http
GET /api/books/search?min_pages=-100
```

Response:

```json
{
  "error": "min_pages cannot be negative"
}
```

---

## Invalid Page

`page` must be greater than `0`.

Invalid:

```http
GET /api/books/search?q=python&page=0
```

Response:

```json
{
  "error": "page must be greater than 0"
}
```

---

## Invalid Limit

`limit` must be between `1` and `100`.

Invalid:

```http
GET /api/books/search?q=python&limit=200
```

Response:

```json
{
  "error": "limit must be between 1 and 100"
}
```

---

## Book Not Found

If the requested Work does not exist:

```http
GET /api/books/invalid-work-id
```

Response:

```json
{
  "error": "Book not found"
}
```

Status:

```text
404 Not Found
```

---

# Using the API from PowerShell

You can test the API directly from PowerShell.

Set the base URL:

```powershell
$BASE = "http://127.0.0.1:5000"
```

Search:

```powershell
Invoke-RestMethod "$BASE/api/books/search?q=python"
```

Advanced search:

```powershell
Invoke-RestMethod "$BASE/api/books/search?q=python&year_from=2010&year_to=2025&min_pages=200&sort=year_desc"
```

Get book details:

```powershell
Invoke-RestMethod "$BASE/api/books/OL123456W"
```

Download CSV:

```powershell
Invoke-WebRequest "$BASE/api/books/export?q=python&limit=100" -OutFile books.csv
```

---

# OpenAPI / Swagger

The API specification is available in:

```text
docs/openapi.yaml
```

The file follows the OpenAPI 3.0.3 specification.

You can open the YAML file using any OpenAPI/Swagger viewer.

For example, you can import:

```text
docs/openapi.yaml
```

into Swagger Editor to view the interactive API documentation.

The OpenAPI documentation describes:

* All endpoints
* Query parameters
* Path parameters
* Request examples
* Response schemas
* Error responses
* CSV responses

---

# Project Structure

```text
book-api/
│
├── app.py
├── requirements.txt
├── README.md
│
├── docs/
│   └── openapi.yaml
│
└── tests/
    └── test_books.py
```

The project intentionally keeps the API implementation in a single `app.py` file because the project is small and does not require a complex architecture.

---

# Open Library API

This project uses Open Library as its external book data source.

Search endpoint:

```text
https://openlibrary.org/search.json
```

Work details:

```text
https://openlibrary.org/works/{work_id}.json
```

The API depends on the data provided by Open Library, so some book fields may be unavailable.

For example, page count may be returned as:

```json
"pages": "N/A"
```

when Open Library does not provide the information.

---

# License

This project is intended for educational and development purposes.
