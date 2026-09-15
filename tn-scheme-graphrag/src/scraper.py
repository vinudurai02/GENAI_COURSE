# ============================================================
# 1. IMPORTS
# ============================================================

import json
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# ============================================================
# 2. WEBSITE CONFIGURATION
# ============================================================

LIST_URL = (
    "https://tnrd.tn.gov.in/"
    "rdweb_newsite/project/reports/Public/StateSchemes.php"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/140.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ============================================================
# 3. OUTPUT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

OUTPUT_FILE = DATA_DIR / "schemes_detailed.json"


# ============================================================
# 4. CREATE HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update(HEADERS)


# ============================================================
# 5. DOWNLOAD PAGE
# ============================================================

def fetch_page(url):
    """
    Download HTML from a URL.
    """

    print(f"Downloading: {url}")

    response = session.get(
        url,
        timeout=30
    )

    response.raise_for_status()

    print(
        f"   HTTP Status: {response.status_code}"
    )

    return response.text


# ============================================================
# 6. CLEAN TEXT
# ============================================================

def clean_text(text):
    """
    Clean whitespace while preserving useful line breaks.
    """

    lines = []

    for line in text.splitlines():

        cleaned_line = " ".join(
            line.split()
        )

        if cleaned_line:
            lines.append(cleaned_line)

    return "\n".join(lines)


# ============================================================
# 7. EXTRACT SCHEME LINKS
# ============================================================

def extract_scheme_links(html):
    """
    Extract scheme names and detail-page links
    from the State Sponsored Schemes page.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    schemes = []

    rows = soup.find_all("tr")

    print()
    print(
        f"Table rows found: {len(rows)}"
    )

    for row in rows:

        cells = row.find_all("td")

        if len(cells) < 2:
            continue

        # ----------------------------------------------------
        # Serial number
        # ----------------------------------------------------

        serial_number = cells[0].get_text(
            " ",
            strip=True
        )

        if not serial_number.isdigit():
            continue

        # ----------------------------------------------------
        # Scheme name
        # ----------------------------------------------------

        scheme_cell = cells[1]

        scheme_name = scheme_cell.get_text(
            " ",
            strip=True
        )

        # ----------------------------------------------------
        # Scheme link
        # ----------------------------------------------------

        link = scheme_cell.find("a")

        if not link:
            print(
                f"⚠️ No link found: {scheme_name}"
            )
            continue

        href = link.get("href")

        if not href:
            print(
                f"⚠️ Empty link: {scheme_name}"
            )
            continue

        # ----------------------------------------------------
        # Convert relative URL → absolute URL
        # ----------------------------------------------------

        detail_url = urljoin(
            LIST_URL,
            href
        )

        # ----------------------------------------------------
        # Create scheme record
        # ----------------------------------------------------

        scheme = {
            "serial_number": serial_number,
            "scheme_name": scheme_name,
            "department": (
                "Rural Development and "
                "Panchayat Raj Department"
            ),
            "scheme_type": "State Scheme",
            "detail_url": detail_url,
            "list_source_url": LIST_URL
        }

        schemes.append(
            scheme
        )

    return schemes


# ============================================================
# 8. EXTRACT REAL SCHEME CONTENT
# ============================================================

def extract_detail_content(html):
    """
    Extract ONLY the actual scheme content.

    Inspection of the TN Government HTML showed
    that the useful scheme information is inside:

        <div class="justify">

    This avoids extracting navigation menus,
    headers and footer text.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # --------------------------------------------------------
    # Find the real content container
    # --------------------------------------------------------

    content_div = soup.find(
        "div",
        class_="justify"
    )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    if content_div is None:

        print(
            "   ⚠️ 'justify' content container not found."
        )

        content_div = soup.find(
            "div",
            class_="webpage_content"
        )

    # --------------------------------------------------------
    # If still nothing found
    # --------------------------------------------------------

    if content_div is None:

        print(
            "   ❌ Scheme content container not found."
        )

        return ""

    # --------------------------------------------------------
    # Remove unnecessary elements
    # --------------------------------------------------------

    for tag in content_div.find_all(
        ["script", "style", "noscript", "svg"]
    ):

        tag.decompose()

    # --------------------------------------------------------
    # Extract readable text
    # --------------------------------------------------------

    raw_text = content_div.get_text(
        "\n",
        strip=True
    )

    cleaned_text = clean_text(
        raw_text
    )

    return cleaned_text


# ============================================================
# 9. VALIDATE EXTRACTED CONTENT
# ============================================================

def validate_content(content, scheme_name):
    """
    Basic validation to make sure we extracted
    useful scheme content rather than navigation text.
    """

    if not content:
        return False

    if len(content) < 100:
        return False

    # Scheme name should normally appear
    # somewhere in the content container.

    if scheme_name.lower() not in content.lower():

        print(
            "   ⚠️ Scheme name not found "
            "inside extracted content."
        )

    return True


# ============================================================
# 10. SCRAPE ALL SCHEMES
# ============================================================

def scrape_all_schemes():
    """
    Scrape the scheme list and all scheme detail pages.
    """

    print()
    print(
        "======================================"
    )
    print(
        "TN GOVERNMENT SCHEME SCRAPER"
    )
    print(
        "======================================"
    )
    print()

    # --------------------------------------------------------
    # Download scheme list
    # --------------------------------------------------------

    list_html = fetch_page(
        LIST_URL
    )

    # --------------------------------------------------------
    # Extract scheme URLs
    # --------------------------------------------------------

    schemes = extract_scheme_links(
        list_html
    )

    print()
    print(
        f"Scheme links found: {len(schemes)}"
    )

    print()

    detailed_schemes = []

    total = len(schemes)

    # --------------------------------------------------------
    # Visit every scheme
    # --------------------------------------------------------

    for index, scheme in enumerate(
        schemes,
        start=1
    ):

        print(
            f"[{index}/{total}] "
            f"{scheme['scheme_name']}"
        )

        print(
            f"   URL: {scheme['detail_url']}"
        )

        try:

            # ------------------------------------------------
            # Download scheme page
            # ------------------------------------------------

            detail_html = fetch_page(
                scheme["detail_url"]
            )

            # ------------------------------------------------
            # Extract real scheme content
            # ------------------------------------------------

            content = extract_detail_content(
                detail_html
            )

            # ------------------------------------------------
            # Validate
            # ------------------------------------------------

            is_valid = validate_content(
                content,
                scheme["scheme_name"]
            )

            # ------------------------------------------------
            # Save data
            # ------------------------------------------------

            scheme["raw_content"] = content

            scheme["content_length"] = len(
                content
            )

            if is_valid:

                scheme["scrape_status"] = "success"

            else:

                scheme["scrape_status"] = (
                    "content_validation_failed"
                )

            # ------------------------------------------------
            # Print result
            # ------------------------------------------------

            print(
                f"   ✓ Extracted "
                f"{len(content)} characters"
            )

            print()

            print(
                "   CONTENT PREVIEW"
            )

            print(
                "   ----------------------------"
            )

            # First 500 characters
            preview = content[:500]

            print(
                preview
            )

            print(
                "   ----------------------------"
            )

            print()

        except requests.RequestException as error:

            print(
                f"   ❌ HTTP Error: {error}"
            )

            scheme["raw_content"] = ""

            scheme["content_length"] = 0

            scheme["scrape_status"] = "failed"

            scheme["scrape_error"] = str(
                error
            )

        except Exception as error:

            print(
                f"   ❌ Processing Error: {error}"
            )

            scheme["raw_content"] = ""

            scheme["content_length"] = 0

            scheme["scrape_status"] = "failed"

            scheme["scrape_error"] = str(
                error
            )

        detailed_schemes.append(
            scheme
        )

        # ----------------------------------------------------
        # Avoid hammering government server
        # ----------------------------------------------------

        if index < total:
            time.sleep(1)

    return detailed_schemes


# ============================================================
# 11. SAVE JSON
# ============================================================

def save_to_json(schemes):
    """
    Save detailed scheme information as JSON.
    """

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            schemes,
            file,
            ensure_ascii=False,
            indent=4
        )

    print()
    print(
        "======================================"
    )
    print(
        "JSON SAVED"
    )
    print(
        "======================================"
    )

    print(
        OUTPUT_FILE
    )


# ============================================================
# 12. DISPLAY SUMMARY
# ============================================================

def display_summary(schemes):
    """
    Display final scraping results.
    """

    successful = [
        scheme
        for scheme in schemes
        if scheme["scrape_status"] == "success"
    ]

    failed = [
        scheme
        for scheme in schemes
        if scheme["scrape_status"] != "success"
    ]

    print()
    print(
        "======================================"
    )
    print(
        "SCRAPING SUMMARY"
    )
    print(
        "======================================"
    )

    print()

    for scheme in schemes:

        if scheme["scrape_status"] == "success":
            symbol = "✓"
        else:
            symbol = "❌"

        print(
            f"{symbol} "
            f"{scheme['scheme_name']}"
        )

        print(
            f"   Characters: "
            f"{scheme['content_length']}"
        )

        print(
            f"   Status: "
            f"{scheme['scrape_status']}"
        )

        print()

    print(
        "--------------------------------------"
    )

    print(
        f"Total schemes: "
        f"{len(schemes)}"
    )

    print(
        f"Successful: "
        f"{len(successful)}"
    )

    print(
        f"Failed / invalid: "
        f"{len(failed)}"
    )

    print(
        "--------------------------------------"
    )


# ============================================================
# 13. MAIN PROGRAM
# ============================================================

def main():

    # Scrape website
    schemes = scrape_all_schemes()

    # Save raw knowledge
    save_to_json(
        schemes
    )

    # Display statistics
    display_summary(
        schemes
    )


# ============================================================
# 14. RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()