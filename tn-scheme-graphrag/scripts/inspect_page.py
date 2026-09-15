# ============================================================
# 1. IMPORTS
# ============================================================

import requests
from bs4 import BeautifulSoup


# ============================================================
# 2. TEST URL
# ============================================================

URL = (
    "https://tnrd.tn.gov.in/"
    "rdweb_newsite/project/reports/Public/"
    "public_page_table_content_details_view.php"
    "?tabular_content_id=MjY5&page_id=Ng=="
)


# ============================================================
# 3. DOWNLOAD PAGE
# ============================================================

response = requests.get(
    URL,
    headers={
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "Chrome/140.0 Safari/537.36"
        )
    },
    timeout=30
)

response.raise_for_status()


# ============================================================
# 4. PARSE HTML
# ============================================================

soup = BeautifulSoup(
    response.text,
    "html.parser"
)


# ============================================================
# 5. BASIC INFORMATION
# ============================================================

print()
print("======================================")
print("PAGE INFORMATION")
print("======================================")

print(f"Status: {response.status_code}")
print(f"HTML length: {len(response.text)}")

print()


# ============================================================
# 6. PAGE TITLE
# ============================================================

print("======================================")
print("TITLE")
print("======================================")

if soup.title:

    print(
        soup.title.get_text(
            " ",
            strip=True
        )
    )

else:

    print("No title found")

print()


# ============================================================
# 7. HEADINGS
# ============================================================

print("======================================")
print("HEADINGS")
print("======================================")

for heading in soup.find_all(
    ["h1", "h2", "h3", "h4", "h5", "h6"]
):

    text = heading.get_text(
        " ",
        strip=True
    )

    if text:
        print(
            heading.name,
            "->",
            text
        )

print()


# ============================================================
# 8. TABLES
# ============================================================

tables = soup.find_all("table")

print("======================================")
print("TABLES")
print("======================================")

print(
    f"Number of tables: "
    f"{len(tables)}"
)

for index, table in enumerate(
    tables,
    start=1
):

    text = table.get_text(
        " ",
        strip=True
    )

    print()
    print(
        f"TABLE {index}"
    )

    print(
        text[:1000]
    )


# ============================================================
# 9. DIVS WITH ID
# ============================================================

print()
print("======================================")
print("DIV IDS")
print("======================================")

for div in soup.find_all(
    "div",
    id=True
):

    text = div.get_text(
        " ",
        strip=True
    )

    print(
        f"ID: {div.get('id')}"
    )

    print(
        f"TEXT: {text[:300]}"
    )

    print("-" * 50)


# ============================================================
# 10. DIVS WITH CLASS
# ============================================================

print()
print("======================================")
print("DIV CLASSES")
print("======================================")

for div in soup.find_all(
    "div",
    class_=True
):

    classes = " ".join(
        div.get("class", [])
    )

    text = div.get_text(
        " ",
        strip=True
    )

    if text:

        print(
            f"CLASS: {classes}"
        )

        print(
            f"TEXT: {text[:300]}"
        )

        print("-" * 50)


# ============================================================
# 11. SEARCH FOR EXPECTED CONTENT
# ============================================================

print()
print("======================================")
print("KEYWORD SEARCH")
print("======================================")

page_text = soup.get_text(
    " ",
    strip=True
)

keywords = [
    "Kalaignarin",
    "Kanavu",
    "3.50",
    "Housing",
    "house",
    "Patta",
    "beneficiary",
]


for keyword in keywords:

    found = (
        keyword.lower()
        in page_text.lower()
    )

    print(
        f"{keyword}: "
        f"{'FOUND' if found else 'NOT FOUND'}"
    )


# ============================================================
# 12. SAVE RAW HTML
# ============================================================

with open(
    "data/debug_scheme_page.html",
    "w",
    encoding="utf-8"
) as file:

    file.write(
        response.text
    )


print()
print("======================================")
print("RAW HTML SAVED")
print("======================================")

print(
    "data/debug_scheme_page.html"
)