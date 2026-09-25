# Book API

A simple Flask REST API for searching, filtering, viewing, exporting, and recommending books using the [Open Library API](https://openlibrary.org/developers/api).

The project is intentionally small and simple. It does not use a database, authentication system, microservices, or a complex architecture.

The recommendation feature uses an LLM through OpenRouter to understand natural-language book requests, while Open Library remains the source of the actual books.

---

# Features

* Search books
* Search by title, author, subject, and language
* Filter by publication year
* Filter by page count
* Sort results
* Pagination
* Get detailed information about a book/work
* Export search results to CSV
* Natural-language book recommendations
* LLM-powered intent extraction
* Structured recommendation requirements
* Relevance scoring of real Open Library books
* Input validation
* JSON error responses

---

# Requirements

* Python 3.10+
* Flask
* Requests
* python-dotenv
* An OpenRouter API key for the recommendation endpoint

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

# Environment Variables

The recommendation endpoint uses OpenRouter to understand natural-language requests.

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
```

`OPENROUTER_API_KEY` is required for the recommendation endpoint.

`OPENROUTER_MODEL` specifies which OpenRouter model is used.

The application also has the following default model:

```text
nvidia/nemotron-3-ultra-550b-a55b:free
```

Do not commit your `.env` file or API key to Git.

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

The API provides four endpoints:

| Method | Endpoint               | Description                                         |
| ------ | ---------------------- | --------------------------------------------------- |
| `GET`  | `/api/books/search`    | Search and filter books                             |
| `GET`  | `/api/books/{work_id}` | Get details of a book/work                          |
| `GET`  | `/api/books/export`    | Export search results as CSV                        |
| `POST` | `/api/books/recommend` | Recommend books from a natural-language description |

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
| `category`  | string  | No       | -       | Search by category/topic |
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

## Search by Category

The `category` parameter is mapped to an Open Library subject search.

It can be used for general categories and topics such as:

```text
programming
history
psychology
fantasy
science
philosophy
```

Example:

```http
GET /api/books/search?category=programming
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

# 4. Book Recommendations

## Endpoint

```http
POST /api/books/recommend
```

The recommendation endpoint accepts a natural-language description of the kind of book the user wants.

Instead of requiring the user to specify exact search keywords, the endpoint uses an LLM to understand the request and convert it into structured search requirements.

The application then searches the real Open Library catalog and ranks the resulting books.

The LLM does **not** directly invent or return book recommendations.

---

# Recommendation Architecture

The recommendation process works in several steps:

```text
User description
       |
       v
OpenRouter LLM
       |
       v
Structured requirements
       |
       v
Open Library searches
       |
       v
Real book candidates
       |
       v
Python relevance scoring
       |
       v
Ranked recommendations
```

This separates **understanding the user's intent** from **retrieving real books**.

---

## Natural-Language Request

Example request:

```json
{
  "description": "I want something with an imaginary world and magic like Harry Potter, but I have already read Harry Potter. I want something darker, more adventurous, and suitable for adults."
}
```

PowerShell example:

```powershell
$body = @{
    description = "I want something with an imaginary world and magic like Harry Potter, but I have already read Harry Potter. I want something darker, more adventurous, and suitable for adults."
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:5000/api/books/recommend" `
    -ContentType "application/json" `
    -Body $body
```

---

# Structured Requirements

The LLM converts the natural-language request into structured requirements.

For example:

```json
{
  "topics": [
    "fantasy",
    "magic",
    "imaginary worlds",
    "adventure",
    "dark fantasy",
    "adult fantasy"
  ],
  "reference_titles": [
    "Harry Potter"
  ],
  "exclude_titles": [
    "Harry Potter"
  ],
  "authors": [],
  "language": null,
  "year_from": null,
  "year_to": null,
  "min_pages": null,
  "max_pages": null
}
```

### Requirement Fields

| Field              | Description                                 |
| ------------------ | ------------------------------------------- |
| `topics`           | Concepts and characteristics the user wants |
| `reference_titles` | Books mentioned as examples or references   |
| `exclude_titles`   | Books that should not be recommended        |
| `authors`          | Explicitly requested authors                |
| `language`         | Requested language, if specified            |
| `year_from`        | Minimum publication year                    |
| `year_to`          | Maximum publication year                    |
| `min_pages`        | Minimum page count                          |
| `max_pages`        | Maximum page count                          |

---

# Reference Books

A reference book is a book that the user mentions as an example of what they want.

For example:

```text
I want something like Harry Potter.
```

The system treats `Harry Potter` as a reference:

```json
{
  "reference_titles": [
    "Harry Potter"
  ]
}
```

It does **not** assume that the user wants another copy or edition of Harry Potter.

If the user says:

```text
I've already read Harry Potter.
```

the title is also added to:

```json
{
  "exclude_titles": [
    "Harry Potter"
  ]
}
```

This allows the recommendation system to understand the characteristics represented by the reference book while preventing the reference itself from being returned as a recommendation.

---

# Recommendation Candidate Search

The extracted topics are used to query Open Library.

For example:

```text
fantasy
magic
imaginary worlds
adventure
dark fantasy
adult fantasy
```

The application performs searches for these topics and combines the resulting books into a single candidate set.

Duplicate books are removed using their Open Library Work ID.

---

# Recommendation Scoring

After retrieving candidates, the application ranks them using Python.

The scoring considers:

* Matching topics
* Matching Open Library subjects
* Topic matches in the book title
* Books appearing in multiple topic searches
* Explicit language requirements
* Explicit author requirements
* Publication-year requirements
* Page-count requirements
* Excluded titles
* Reference titles

Each recommendation also contains:

```text
score
```

and:

```text
matched_topics
```

so the result provides some transparency into why a candidate received its score.

---

# Recommendation Response

A successful recommendation request returns:

```json
{
  "description": "I want something with an imaginary world and magic like Harry Potter, but I have already read Harry Potter. I want something darker, more adventurous, and suitable for adults.",
  "requirements": {
    "topics": [
      "fantasy",
      "magic",
      "imaginary worlds",
      "adventure",
      "dark fantasy",
      "adult fantasy"
    ],
    "reference_titles": [
      "Harry Potter"
    ],
    "exclude_titles": [
      "Harry Potter"
    ],
    "authors": [],
    "language": null,
    "year_from": null,
    "year_to": null,
    "min_pages": null,
    "max_pages": null
  },
  "candidate_count": 100,
  "recommendations": [
    {
      "work_id": "OL123456W",
      "title": "Example Book",
      "authors": [
        "Example Author"
      ],
      "first_publish_year": 2001,
      "pages": 500,
      "languages": [
        "eng"
      ],
      "subjects": [
        "Fantasy",
        "Magic",
        "Adventure"
      ],
      "score": 35,
      "matched_topics": [
        "fantasy",
        "magic",
        "adventure"
      ]
    }
  ]
}
```

The exact books and scores depend on the current data available from Open Library.

---

# Recommendation Errors

If the `description` field is missing:

```json
{
  "error": "description is required"
}
```

If the description is empty:

```json
{
  "error": "description cannot be empty"
}
```

If the recommendation service cannot be contacted:

```json
{
  "error": "Failed to contact external service"
}
```

The endpoint returns:

```text
502 Bad Gateway
```

when an external service required for the recommendation process fails.

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

Recommendation:

```powershell
$body = @{
    description = "I want a dark fantasy book with magic and an imaginary world. I have already read Harry Potter."
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri "$BASE/api/books/recommend" `
    -ContentType "application/json" `
    -Body $body
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

# External Services

The project uses two external services.

## Open Library

Open Library provides the actual book catalog data.

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

## OpenRouter

OpenRouter is used only by the recommendation endpoint.

The application sends the user's natural-language description to the configured LLM and receives structured book-search requirements.

The LLM is used for **intent understanding**, not as the source of the books.

The actual books are retrieved from Open Library.

---

# Design Philosophy

The project intentionally avoids unnecessary complexity.

The recommendation system follows a simple separation of responsibilities:

```text
LLM
  ↓
Understand user intent

Open Library
  ↓
Provide real book data

Python
  ↓
Filter, score, and rank candidates
```

This prevents the LLM from directly inventing book recommendations and keeps the actual catalog data grounded in Open Library.

The project can be extended later with more advanced semantic ranking or other recommendation techniques if needed.

---

# License

This project is intended for educational and development purposes.
