from flask import Flask, request, jsonify, Response
import requests
import csv
import io
import os
import json

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# Configuration
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"

USER_AGENT = "BookSearchAPI/1.0"

app = Flask(__name__)


# ============================================================
# OpenRouter structured output schema
# ============================================================

BOOK_REQUIREMENTS_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "book_requirements",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "topics": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "reference_titles": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "exclude_titles": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "authors": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "language": {
                    "type": ["string", "null"]
                },
                "year_from": {
                    "type": ["integer", "null"]
                },
                "year_to": {
                    "type": ["integer", "null"]
                },
                "min_pages": {
                    "type": ["integer", "null"]
                },
                "max_pages": {
                    "type": ["integer", "null"]
                }
            },
            "required": [
                "topics",
                "reference_titles",
                "exclude_titles",
                "authors",
                "language",
                "year_from",
                "year_to",
                "min_pages",
                "max_pages"
            ],
            "additionalProperties": False
        }
    }
}


# ============================================================
# OpenRouter
# ============================================================

def ask_openrouter(messages, response_format=None):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0,
    }

    if response_format:
        payload["response_format"] = response_format

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]


def extract_book_requirements(description):
    system_prompt = """
You are a book-search intent parser.

Your ONLY job is to understand a user's natural-language request
and convert it into structured requirements for searching a real
book catalog.

You are NOT a book recommender.

Do NOT recommend books.
Do NOT generate book titles unless the user explicitly mentioned
those titles.
Do NOT invent authors.
Do NOT invent dates.
Do NOT invent page limits.

The structured result will later be used by a Python application
to search and rank real books from the Open Library catalog.

IMPORTANT DISTINCTION:

1. Reference books

If the user mentions a book as an example of the type of book
they want, put that title in "reference_titles".

For example:

"I want something like Harry Potter"

means:

reference_titles = ["Harry Potter"]

Harry Potter is an example of the desired characteristics.
It is NOT automatically the book the user wants.

2. Excluded books

If the user says they already read a book, do not want it,
want something other than it, or explicitly says not to include it,
put that title in "exclude_titles".

For example:

"I've already read Harry Potter"

means:

exclude_titles = ["Harry Potter"]

A title can appear in both reference_titles and exclude_titles.
This is valid and useful.

3. Topics

Convert the user's desired characteristics into concise,
searchable book concepts.

Extract things such as:

- genres
- themes
- settings
- story characteristics
- tone
- audience
- subject matter
- fictional elements

Prefer concepts that are useful for searching a book catalog.

For example:

"I want an imaginary world with magic and adventure like Harry Potter"

could produce:

[
    "fantasy",
    "magic",
    "imaginary worlds",
    "adventure"
]

Do not simply copy every word from the user's sentence.

4. User intent

Understand the meaning of the request rather than performing
literal keyword extraction.

For example:

"I want something like Harry Potter, but darker and more mature"

should produce concepts related to:

- fantasy
- magic
- imaginary worlds
- adventure
- dark fantasy
- adult fantasy

The title Harry Potter should be treated as a reference,
not as the main search query.

5. Language

Only set "language" when the user explicitly specifies a language
or the requested book language is clearly part of their requirement.

Do not assume a language merely because the user writes the request
in that language.

6. Authors

Only include an author when the user explicitly asks for or mentions
an author.

7. Dates

Only set year_from or year_to when the user expresses a meaningful
publication-year requirement.

8. Pages

Only set min_pages or max_pages when the user expresses a meaningful
page-count preference.

9. Preserve intent

Do not make the requirements unnecessarily restrictive.

The goal is to retrieve a broad but relevant candidate set from
Open Library. Python will perform the final ranking and filtering.

Return ONLY the structured data required by the schema.
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": description,
        },
    ]

    result = ask_openrouter(
        messages,
        response_format=BOOK_REQUIREMENTS_SCHEMA,
    )

    return json.loads(result)


# ============================================================
# Open Library
# ============================================================

def get_open_library_data(params):
    response = requests.get(
        OPEN_LIBRARY_SEARCH_URL,
        params=params,
        headers={
            "User-Agent": USER_AGENT
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def search_books_by_topic(topic, limit=20):
    data = get_open_library_data({
        "subject": topic,
        "limit": limit,
        "page": 1,
    })

    return data.get("docs", [])


def normalize_book(book):
    key = book.get("key", "")

    pages = book.get("number_of_pages_median")

    return {
        "work_id": key.split("/")[-1] if key else None,
        "title": book.get("title"),
        "authors": book.get("author_name", []),
        "first_publish_year": book.get("first_publish_year"),
        "pages": pages if pages is not None else "N/A",
        "languages": book.get("language", []),
        "subjects": book.get("subject", [])[:10],
    }


# ============================================================
# General helpers
# ============================================================

def get_int_param(name):
    value = request.args.get(name)

    if value is None:
        return None, None

    try:
        return int(value), None
    except ValueError:
        return None, f"{name} must be an integer"


def apply_filters(books):
    year_from, _ = get_int_param("year_from")
    year_to, _ = get_int_param("year_to")
    min_pages, _ = get_int_param("min_pages")
    max_pages, _ = get_int_param("max_pages")

    filtered_books = []

    for book in books:
        year = book.get("first_publish_year")
        pages = book.get("pages")

        if year_from is not None:
            if year is None or year < year_from:
                continue

        if year_to is not None:
            if year is None or year > year_to:
                continue

        if pages != "N/A":
            if min_pages is not None and pages < min_pages:
                continue

            if max_pages is not None and pages > max_pages:
                continue

        filtered_books.append(book)

    return filtered_books


def sort_books(books):
    sort = request.args.get("sort")

    if not sort:
        return books

    reverse = False

    if sort.endswith("_desc"):
        reverse = True

    sort_field = sort.replace("_desc", "").replace("_asc", "")

    if sort_field == "year":
        books.sort(
            key=lambda book: book.get("first_publish_year") or 0,
            reverse=reverse,
        )

    elif sort_field == "pages":
        books.sort(
            key=lambda book: book.get("pages") or 0,
            reverse=reverse,
        )

    elif sort_field == "title":
        books.sort(
            key=lambda book: (book.get("title") or "").lower(),
            reverse=reverse,
        )

    return books


# ============================================================
# Recommendation helpers
# ============================================================

def normalize_text(value):
    if not value:
        return ""

    return " ".join(
        value.lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace(":", " ")
        .replace(",", " ")
        .replace(".", " ")
        .split()
    )


def title_matches(candidate_title, requested_title):
    candidate = normalize_text(candidate_title)
    requested = normalize_text(requested_title)

    if not candidate or not requested:
        return False

    return (
        candidate == requested
        or requested in candidate
    )


def language_matches(book_languages, requested_language):
    if not requested_language:
        return True

    requested = normalize_text(requested_language)

    language_map = {
        "english": "eng",
        "french": "fre",
        "français": "fre",
        "german": "ger",
        "deutsch": "ger",
        "spanish": "spa",
        "español": "spa",
        "italian": "ita",
        "portuguese": "por",
        "russian": "rus",
        "arabic": "ara",
        "persian": "per",
        "farsi": "per",
        "japanese": "jpn",
        "chinese": "chi",
    }

    requested_code = language_map.get(
        requested,
        requested,
    )

    return any(
        normalize_text(language) == requested_code
        or normalize_text(language) == requested
        for language in book_languages
    )


def book_matches_hard_requirements(book, requirements):
    year = book.get("first_publish_year")
    pages = book.get("pages")

    year_from = requirements.get("year_from")
    year_to = requirements.get("year_to")

    min_pages = requirements.get("min_pages")
    max_pages = requirements.get("max_pages")

    if year_from is not None:
        if year is None or year < year_from:
            return False

    if year_to is not None:
        if year is None or year > year_to:
            return False

    if pages != "N/A":
        if min_pages is not None and pages < min_pages:
            return False

        if max_pages is not None and pages > max_pages:
            return False

    if requirements.get("language"):
        if not language_matches(
            book.get("languages", []),
            requirements["language"],
        ):
            return False

    requested_authors = requirements.get("authors", [])

    if requested_authors:
        book_authors = [
            normalize_text(author)
            for author in book.get("authors", [])
        ]

        for requested_author in requested_authors:
            requested_author = normalize_text(requested_author)

            if not any(
                requested_author in author
                for author in book_authors
            ):
                return False

    return True


def should_exclude_book(book, requirements):
    title = book.get("title") or ""

    exclude_titles = requirements.get(
        "exclude_titles",
        [],
    )

    for excluded_title in exclude_titles:
        if title_matches(title, excluded_title):
            return True

    return False


def is_reference_book(book, requirements):
    title = book.get("title") or ""

    reference_titles = requirements.get(
        "reference_titles",
        [],
    )

    for reference_title in reference_titles:
        if title_matches(title, reference_title):
            return True

    return False


def calculate_topic_match(book, topic):
    title = normalize_text(book.get("title") or "")

    subjects = [
        normalize_text(subject)
        for subject in book.get("subjects", [])
    ]

    topic_normalized = normalize_text(topic)

    if not topic_normalized:
        return 0

    # Strongest match: exact subject.
    if topic_normalized in subjects:
        return 10

    # Strong match: topic appears inside a subject.
    for subject in subjects:
        if topic_normalized in subject:
            return 7

    # Topic appears in title.
    if topic_normalized in title:
        return 6

    # Partial word overlap.
    topic_words = set(topic_normalized.split())

    if not topic_words:
        return 0

    for subject in subjects:
        subject_words = set(subject.split())

        if topic_words & subject_words:
            return 3

    return 0


def score_book(book, requirements, topic_occurrences):
    score = 0
    matched_topics = []

    topics = requirements.get("topics", [])

    for topic in topics:
        topic_score = calculate_topic_match(
            book,
            topic,
        )

        if topic_score > 0:
            score += topic_score
            matched_topics.append(topic)

    # A book appearing in several topic searches is useful evidence
    # that it matches multiple parts of the user's request.
    occurrence_count = topic_occurrences.get(
        book.get("work_id"),
        1,
    )

    score += max(0, occurrence_count - 1) * 4

    return score, matched_topics


def get_recommendation_candidates(requirements):
    topics = requirements.get("topics", [])

    candidates = {}
    topic_occurrences = {}

    # If the LLM somehow returns no topics, use the reference title
    # only as a fallback search signal.
    search_topics = topics[:]

    if not search_topics:
        search_topics = requirements.get(
            "reference_titles",
            [],
        )

    for topic in search_topics:
        if not topic.strip():
            continue

        try:
            raw_books = search_books_by_topic(
                topic,
                limit=20,
            )
        except requests.RequestException:
            continue

        for raw_book in raw_books:
            book = normalize_book(raw_book)

            work_id = book.get("work_id")

            if not work_id:
                continue

            if work_id not in candidates:
                candidates[work_id] = book
                topic_occurrences[work_id] = 0

            topic_occurrences[work_id] += 1

    return list(candidates.values()), topic_occurrences


def rank_recommendation_candidates(
    candidates,
    requirements,
    topic_occurrences,
):
    ranked = []

    for book in candidates:
        if should_exclude_book(
            book,
            requirements,
        ):
            continue

        # Don't return the exact reference book itself.
        #
        # This is separate from exclude_titles because a reference
        # can be used as an example without explicitly being excluded.
        if is_reference_book(
            book,
            requirements,
        ):
            continue

        if not book_matches_hard_requirements(
            book,
            requirements,
        ):
            continue

        score, matched_topics = score_book(
            book,
            requirements,
            topic_occurrences,
        )

        if score <= 0:
            continue

        ranked.append({
            **book,
            "score": score,
            "matched_topics": matched_topics,
        })

    ranked.sort(
        key=lambda book: (
            book["score"],
            len(book["matched_topics"]),
        ),
        reverse=True,
    )

    return ranked


# ============================================================
# Search endpoint
# ============================================================

@app.get("/api/books/search")
def search_books():
    limit = request.args.get(
        "limit",
        default=20,
        type=int,
    )

    page = request.args.get(
        "page",
        default=1,
        type=int,
    )

    if limit < 1 or limit > 100:
        return jsonify({
            "error": "limit must be between 1 and 100"
        }), 400

    if page < 1:
        return jsonify({
            "error": "page must be greater than 0"
        }), 400

    year_from, error = get_int_param("year_from")

    if error:
        return jsonify({"error": error}), 400

    year_to, error = get_int_param("year_to")

    if error:
        return jsonify({"error": error}), 400

    min_pages, error = get_int_param("min_pages")

    if error:
        return jsonify({"error": error}), 400

    max_pages, error = get_int_param("max_pages")

    if error:
        return jsonify({"error": error}), 400

    if year_from is not None and year_to is not None:
        if year_from > year_to:
            return jsonify({
                "error": "year_from cannot be greater than year_to"
            }), 400

    if min_pages is not None and max_pages is not None:
        if min_pages > max_pages:
            return jsonify({
                "error": "min_pages cannot be greater than max_pages"
            }), 400

    if min_pages is not None and min_pages < 0:
        return jsonify({
            "error": "min_pages cannot be negative"
        }), 400

    if max_pages is not None and max_pages < 0:
        return jsonify({
            "error": "max_pages cannot be negative"
        }), 400

    params = {
        "q": request.args.get("q", ""),
        "limit": limit,
        "page": page,
    }

    if request.args.get("category"):
        params["subject"] = request.args["category"]

    if request.args.get("title"):
        params["title"] = request.args["title"]

    if request.args.get("author"):
        params["author"] = request.args["author"]

    if request.args.get("subject"):
        params["subject"] = request.args["subject"]

    if request.args.get("language"):
        params["language"] = request.args["language"]

    data = get_open_library_data(params)

    books = [
        normalize_book(book)
        for book in data.get("docs", [])
    ]

    books = apply_filters(books)
    books = sort_books(books)

    return jsonify({
        "total": len(books),
        "page": page,
        "limit": limit,
        "books": books,
    })


# ============================================================
# Book details
# ============================================================

@app.get("/api/books/<work_id>")
def get_book(work_id):
    url = f"https://openlibrary.org/works/{work_id}.json"

    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT
        },
        timeout=10,
    )

    if response.status_code == 404:
        return jsonify({
            "error": "Book not found"
        }), 404

    response.raise_for_status()

    return jsonify(response.json())


# ============================================================
# CSV export
# ============================================================

@app.get("/api/books/export")
def export_books():
    limit = request.args.get(
        "limit",
        default=100,
        type=int,
    )

    page = request.args.get(
        "page",
        default=1,
        type=int,
    )

    if limit < 1 or limit > 100:
        return jsonify({
            "error": "limit must be between 1 and 100"
        }), 400

    if page < 1:
        return jsonify({
            "error": "page must be greater than 0"
        }), 400

    year_from, error = get_int_param("year_from")

    if error:
        return jsonify({"error": error}), 400

    year_to, error = get_int_param("year_to")

    if error:
        return jsonify({"error": error}), 400

    min_pages, error = get_int_param("min_pages")

    if error:
        return jsonify({"error": error}), 400

    max_pages, error = get_int_param("max_pages")

    if error:
        return jsonify({"error": error}), 400

    if year_from is not None and year_to is not None:
        if year_from > year_to:
            return jsonify({
                "error": "year_from cannot be greater than year_to"
            }), 400

    if min_pages is not None and max_pages is not None:
        if min_pages > max_pages:
            return jsonify({
                "error": "min_pages cannot be greater than max_pages"
            }), 400

    if min_pages is not None and min_pages < 0:
        return jsonify({
            "error": "min_pages cannot be negative"
        }), 400

    if max_pages is not None and max_pages < 0:
        return jsonify({
            "error": "max_pages cannot be negative"
        }), 400

    params = {
        "q": request.args.get("q", ""),
        "limit": limit,
        "page": page,
    }

    if request.args.get("category"):
        params["subject"] = request.args["category"]

    if request.args.get("title"):
        params["title"] = request.args["title"]

    if request.args.get("author"):
        params["author"] = request.args["author"]

    if request.args.get("subject"):
        params["subject"] = request.args["subject"]

    if request.args.get("language"):
        params["language"] = request.args["language"]

    data = get_open_library_data(params)

    books = [
        normalize_book(book)
        for book in data.get("docs", [])
    ]

    books = apply_filters(books)
    books = sort_books(books)

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "work_id",
        "title",
        "authors",
        "first_publish_year",
        "pages",
        "languages",
        "subjects",
    ])

    for book in books:
        writer.writerow([
            book["work_id"],
            book["title"],
            ", ".join(book["authors"]),
            book["first_publish_year"],
            book["pages"],
            ", ".join(book["languages"]),
            ", ".join(book["subjects"]),
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=books.csv"
        },
    )


# ============================================================
# Recommendation endpoint
# ============================================================

@app.post("/api/books/recommend")
def recommend_books():
    data = request.get_json(silent=True)

    if not data or not isinstance(
        data.get("description"),
        str,
    ):
        return jsonify({
            "error": "description is required"
        }), 400

    description = data["description"].strip()

    if not description:
        return jsonify({
            "error": "description cannot be empty"
        }), 400

    try:
        # ----------------------------------------------------
        # Step 1: Understand the user's request
        # ----------------------------------------------------
        requirements = extract_book_requirements(
            description
        )

        # ----------------------------------------------------
        # Step 2: Retrieve real books from Open Library
        # ----------------------------------------------------
        candidates, topic_occurrences = (
            get_recommendation_candidates(
                requirements
            )
        )

        # ----------------------------------------------------
        # Step 3: Rank real candidates
        # ----------------------------------------------------
        recommendations = rank_recommendation_candidates(
            candidates,
            requirements,
            topic_occurrences,
        )

        # Return a reasonable number of recommendations.
        recommendations = recommendations[:10]

        return jsonify({
            "description": description,
            "candidate_count": len(candidates),
            "recommendations": recommendations,
        })

    except requests.RequestException as exc:
        return jsonify({
            "error": "Failed to contact external service",
            "details": str(exc),
        }), 502

    except (
        KeyError,
        json.JSONDecodeError,
        RuntimeError,
    ) as exc:
        return jsonify({
            "error": "Failed to understand book requirements",
            "details": str(exc),
        }), 502


# ============================================================
# Application entry point
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)