# ============================================================
# 1. IMPORTS
# ============================================================

import json
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI


# ============================================================
# 2. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "schemes_detailed.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "schemes_structured.json"
)


# ============================================================
# 3. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(
    PROJECT_ROOT / ".env"
)

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

if not OPENAI_API_KEY:

    raise ValueError(
        "OPENAI_API_KEY not found in .env file."
    )


# ============================================================
# 4. DEFINE KNOWLEDGE GRAPH SCHEMA
# ============================================================

class SchemeKnowledge(BaseModel):
    """
    Structured knowledge extracted from
    one Tamil Nadu Government scheme.
    """

    scheme_name: str = Field(
        description=(
            "Official name of the government scheme."
        )
    )

    department: str = Field(
        description=(
            "Government department responsible "
            "for the scheme."
        )
    )

    description: str = Field(
        description=(
            "Short factual description of the scheme."
        )
    )

    beneficiaries: List[str] = Field(
        default_factory=list,
        description=(
            "People, communities, institutions, "
            "or groups targeted by the scheme."
        )
    )

    eligibility: List[str] = Field(
        default_factory=list,
        description=(
            "Eligibility requirements explicitly "
            "mentioned in the source."
        )
    )

    benefits: List[str] = Field(
        default_factory=list,
        description=(
            "Financial, infrastructure, service, "
            "or other benefits provided."
        )
    )

    documents_required: List[str] = Field(
        default_factory=list,
        description=(
            "Documents explicitly required "
            "for eligibility or application."
        )
    )

    locations: List[str] = Field(
        default_factory=list,
        description=(
            "Geographical locations where "
            "the scheme applies."
        )
    )

    activities: List[str] = Field(
        default_factory=list,
        description=(
            "Activities, works, projects, or actions "
            "supported by the scheme."
        )
    )


# ============================================================
# 5. INITIALIZE OPENAI MODEL
# ============================================================

llm = ChatOpenAI(
    model="gpt-5-mini",
    temperature=0
)


# ============================================================
# 6. ENABLE STRUCTURED OUTPUT
# ============================================================

structured_llm = llm.with_structured_output(
    SchemeKnowledge
)


# ============================================================
# 7. LOAD SCRAPED SCHEMES
# ============================================================

def load_schemes():
    """
    Load schemes_detailed.json created
    by our Step 11 scraper.
    """

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        schemes = json.load(
            file
        )

    print(
        f"Loaded {len(schemes)} schemes."
    )

    return schemes


# ============================================================
# 8. BUILD EXTRACTION PROMPT
# ============================================================

def build_prompt(scheme):
    """
    Build instructions for the LLM.

    The LLM must only extract information
    supported by the government source.
    """

    scheme_name = scheme.get(
        "scheme_name",
        ""
    )

    department = scheme.get(
        "department",
        ""
    )

    raw_content = scheme.get(
        "raw_content",
        ""
    )

    prompt = f"""
You are extracting structured knowledge from an official
Tamil Nadu Government scheme description.

Your job is to convert the source text into structured data
for a Neo4j knowledge graph.

IMPORTANT RULES:

1. Use ONLY information explicitly supported by the source text.

2. Do NOT invent eligibility requirements, benefits,
   beneficiaries, documents, locations, or activities.

3. If information is not available, return an empty list.

4. Keep entity descriptions short, factual and useful
   for a knowledge graph.

5. Do not duplicate equivalent items.

6. Preserve important numerical information such as:
   - rupee amounts
   - percentages
   - years
   - quantities
   - distances
   - allocation amounts

7. If the source contains Tamil text, extract information
   from it when understandable, but return structured
   fields in English.

8. The scheme name should remain the official scheme name
   supplied below.

9. The department should remain the department supplied
   below unless the source explicitly provides a more
   specific responsible department.

OFFICIAL SCHEME NAME:

{scheme_name}

DEPARTMENT:

{department}

OFFICIAL GOVERNMENT SOURCE TEXT:

---------------- SOURCE START ----------------

{raw_content}

----------------- SOURCE END -----------------

Extract the knowledge from this source.
"""

    return prompt


# ============================================================
# 9. EXTRACT ONE SCHEME
# ============================================================

def extract_scheme(scheme):
    """
    Send one government scheme to the LLM
    and receive validated structured output.
    """

    prompt = build_prompt(
        scheme
    )

    result = structured_llm.invoke(
        prompt
    )

    return result


# ============================================================
# 10. PROCESS ALL SCHEMES
# ============================================================

def process_schemes(schemes):
    """
    Process every scheme through the LLM.
    """

    structured_schemes = []

    total = len(schemes)

    print()
    print(
        "======================================"
    )
    print(
        "OPENAI ENTITY EXTRACTION"
    )
    print(
        "======================================"
    )
    print()

    for index, scheme in enumerate(
        schemes,
        start=1
    ):

        scheme_name = scheme.get(
            "scheme_name",
            "Unknown Scheme"
        )

        scrape_status = scheme.get(
            "scrape_status"
        )

        raw_content = scheme.get(
            "raw_content",
            ""
        )

        print(
            f"[{index}/{total}] "
            f"{scheme_name}"
        )

        # ----------------------------------------------------
        # Skip failed scraper records
        # ----------------------------------------------------

        if scrape_status != "success":

            print(
                "   ⚠️ Skipped: "
                "scraping was not successful."
            )

            continue

        # ----------------------------------------------------
        # Skip empty content
        # ----------------------------------------------------

        if not raw_content.strip():

            print(
                "   ⚠️ Skipped: "
                "raw_content is empty."
            )

            continue

        try:

            # ------------------------------------------------
            # Ask OpenAI to extract entities
            # ------------------------------------------------

            result = extract_scheme(
                scheme
            )

            # ------------------------------------------------
            # Convert Pydantic model → Python dictionary
            # ------------------------------------------------

            structured_data = (
                result.model_dump()
            )

            # ------------------------------------------------
            # Preserve source information
            # ------------------------------------------------

            structured_data[
                "source_url"
            ] = scheme.get(
                "detail_url",
                ""
            )

            structured_data[
                "scheme_type"
            ] = scheme.get(
                "scheme_type",
                ""
            )

            structured_schemes.append(
                structured_data
            )

            # ------------------------------------------------
            # Display extracted graph knowledge
            # ------------------------------------------------

            print(
                f"   ✓ Beneficiaries: "
                f"{len(result.beneficiaries)}"
            )

            print(
                f"   ✓ Eligibility: "
                f"{len(result.eligibility)}"
            )

            print(
                f"   ✓ Benefits: "
                f"{len(result.benefits)}"
            )

            print(
                f"   ✓ Documents: "
                f"{len(result.documents_required)}"
            )

            print(
                f"   ✓ Locations: "
                f"{len(result.locations)}"
            )

            print(
                f"   ✓ Activities: "
                f"{len(result.activities)}"
            )

            print()

        except Exception as error:

            print(
                f"   ❌ Extraction failed: "
                f"{error}"
            )

            print()

    return structured_schemes


# ============================================================
# 11. SAVE STRUCTURED DATA
# ============================================================

def save_structured_data(
    structured_schemes
):
    """
    Save extracted graph-ready knowledge.
    """

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            structured_schemes,
            file,
            ensure_ascii=False,
            indent=4
        )

    print()
    print(
        "======================================"
    )
    print(
        "STRUCTURED DATA SAVED"
    )
    print(
        "======================================"
    )

    print(
        OUTPUT_FILE
    )


# ============================================================
# 12. DISPLAY FINAL SUMMARY
# ============================================================

def display_summary(
    original_schemes,
    structured_schemes
):
    """
    Display extraction statistics.
    """

    print()
    print(
        "======================================"
    )
    print(
        "EXTRACTION SUMMARY"
    )
    print(
        "======================================"
    )

    print(
        f"Input schemes: "
        f"{len(original_schemes)}"
    )

    print(
        f"Successfully structured: "
        f"{len(structured_schemes)}"
    )

    print(
        f"Failed / skipped: "
        f"{len(original_schemes) - len(structured_schemes)}"
    )


# ============================================================
# 13. MAIN PROGRAM
# ============================================================

def main():

    # --------------------------------------------------------
    # Load scraped government data
    # --------------------------------------------------------

    schemes = load_schemes()

    # --------------------------------------------------------
    # Extract graph entities using OpenAI
    # --------------------------------------------------------

    structured_schemes = process_schemes(
        schemes
    )

    # --------------------------------------------------------
    # Save graph-ready JSON
    # --------------------------------------------------------

    save_structured_data(
        structured_schemes
    )

    # --------------------------------------------------------
    # Display statistics
    # --------------------------------------------------------

    display_summary(
        schemes,
        structured_schemes
    )


# ============================================================
# 14. RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()