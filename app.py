from flask import Flask, request, jsonify, Response
import requests
import csv
import io


app = Flask(__name__)

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"
USER_AGENT = "BookSearchAPI/1.0"


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


@app.get("/api/books/search")
def search_books():
    limit = request.args.get("limit", default=20, type=int)
    page = request.args.get("page", default=1, type=int)

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


@app.get("/api/books/export")
def export_books():
    limit = request.args.get("limit", default=100, type=int)
    page = request.args.get("page", default=1, type=int)

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


def get_int_param(name):
    value = request.args.get(name)

    if value is None:
        return None, None

    try:
        return int(value), None
    except ValueError:
        return None, f"{name} must be an integer"


if __name__ == "__main__":
    app.run(debug=True)