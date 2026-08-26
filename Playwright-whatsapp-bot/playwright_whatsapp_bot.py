from playwright.sync_api import sync_playwright
import pandas as pd
import os
import random
import re
from datetime import datetime


WHATSAPP_URL = "https://web.whatsapp.com/"
USER_DATA_DIR = "whatsapp_session"
CONTACTS_FILE = "contacts.xlsx"
SCREENSHOT_DIR = "screenshots"


# =========================================================
# LOAD CONTACTS
# =========================================================

def load_contacts():

    if not os.path.exists(CONTACTS_FILE):
        print(f"ERROR: {CONTACTS_FILE} not found.")
        return None

    try:
        df = pd.read_excel(
            CONTACTS_FILE,
            dtype={
                "Name": str,
                "Phone": str,
                "Message": str
            }
        )

        required_columns = [
            "Name",
            "Phone",
            "Message"
        ]

        for column in required_columns:

            if column not in df.columns:

                print(
                    f"ERROR: Missing required column: {column}"
                )

                return None

        df = df.fillna("")

        print(
            f"Loaded {len(df)} contacts successfully."
        )

        return df

    except Exception as e:

        print(
            f"ERROR reading contacts file: {e}"
        )

        return None


# =========================================================
# PREPARE MESSAGE
# =========================================================

def prepare_message(name, template):

    if not template:

        template = (
            "Hello {name}, this is a test message."
        )

    return str(template).replace(
        "{name}",
        str(name)
    )


# =========================================================
# RANDOM DELAY
# =========================================================

def random_delay(page, minimum=2, maximum=5):

    seconds = random.uniform(
        minimum,
        maximum
    )

    print(
        f"Waiting {seconds:.2f} seconds..."
    )

    page.wait_for_timeout(
        int(seconds * 1000)
    )


# =========================================================
# WAIT FOR WHATSAPP
# =========================================================

def wait_for_whatsapp_ready(page):

    print(
        "Waiting for WhatsApp interface..."
    )

    page.wait_for_timeout(
        5000
    )

    selectors = [
        "#pane-side",
        '[role="grid"]',
        '[role="textbox"]',
        '[contenteditable="true"]'
    ]

    for selector in selectors:

        try:

            page.wait_for_selector(
                selector,
                timeout=5000,
                state="visible"
            )

            print(
                "WhatsApp interface detected using:",
                selector
            )

            return True

        except Exception:

            continue

    return False


# =========================================================
# FIND SEARCH BOX
# =========================================================

def get_search_box(page):

    print(
        "Looking for WhatsApp search box..."
    )

    labels = [
        "Search",
        "Search or start new chat",
        "Search input textbox"
    ]

    for label in labels:

        try:

            locator = page.get_by_label(
                label,
                exact=False
            ).first

            if locator.is_visible(
                timeout=2000
            ):

                print(
                    f"Search box found using label: {label}"
                )

                return locator

        except Exception:

            pass

    try:

        searchboxes = page.get_by_role(
            "searchbox"
        )

        for i in range(
            searchboxes.count()
        ):

            locator = searchboxes.nth(i)

            if locator.is_visible():

                print(
                    "Search box found using role=searchbox"
                )

                return locator

    except Exception:

        pass

    try:

        textboxes = page.get_by_role(
            "textbox"
        )

        for i in range(
            textboxes.count()
        ):

            locator = textboxes.nth(i)

            try:

                if not locator.is_visible():

                    continue

                aria_label = locator.get_attribute(
                    "aria-label"
                )

                title = locator.get_attribute(
                    "title"
                )

                combined = (
                    f"{aria_label} {title}"
                ).lower()

                if "search" in combined:

                    print(
                        "Search box found using textbox role."
                    )

                    return locator

            except Exception:

                continue

    except Exception:

        pass

    try:

        editables = page.locator(
            '[contenteditable="true"]'
        )

        for i in range(
            editables.count()
        ):

            locator = editables.nth(i)

            try:

                if not locator.is_visible():

                    continue

                aria_label = locator.get_attribute(
                    "aria-label"
                )

                title = locator.get_attribute(
                    "title"
                )

                combined = (
                    f"{aria_label} {title}"
                ).lower()

                if "search" in combined:

                    print(
                        "Search box found using contenteditable."
                    )

                    return locator

            except Exception:

                continue

    except Exception:

        pass

    fallback_selectors = [
        '[aria-label*="Search"]',
        '[placeholder*="Search"]',
        'div[role="searchbox"]',
        'input[type="search"]'
    ]

    for selector in fallback_selectors:

        try:

            locators = page.locator(
                selector
            )

            for i in range(
                locators.count()
            ):

                locator = locators.nth(i)

                if locator.is_visible():

                    print(
                        f"Search box found using CSS: {selector}"
                    )

                    return locator

        except Exception:

            continue

    return None


# =========================================================
# CLEAR SEARCH
# =========================================================

def clear_search_box(page, search_box):

    try:

        search_box.click()

        page.wait_for_timeout(
            500
        )

        page.keyboard.press(
            "Meta+A"
        )

        page.keyboard.press(
            "Backspace"
        )

        page.wait_for_timeout(
            500
        )

    except Exception:

        try:
            search_box.fill("")
        except Exception:
            pass


# =========================================================
# SEARCH CONTACT
# =========================================================

def search_contact(page, name, phone):

    search_box = get_search_box(
        page
    )

    if search_box is None:

        print(
            "Search box not found."
        )

        return False

    search_values = []

    if phone:

        search_values.append(
            phone
        )

        if not phone.startswith("+"):

            search_values.append(
                "+" + phone
            )

    if name:

        search_values.append(
            name
        )

    search_values = list(
        dict.fromkeys(
            search_values
        )
    )

    for search_value in search_values:

        try:

            print(
                f"\nSearching for: {search_value}"
            )

            clear_search_box(
                page,
                search_box
            )

            random_delay(
                page,
                2,
                3
            )

            search_box.click()

            search_box.fill(
                search_value
            )

            print(
                "Search text entered."
            )

            page.wait_for_timeout(
                3000
            )

            # -------------------------------------------------
            # MATCH BY NAME
            # -------------------------------------------------

            if name:

                try:

                    result = page.locator(
                        f'span[title="{name}"]'
                    ).first

                    if result.is_visible():

                        print(
                            f"Contact found: {name}"
                        )

                        result.click()

                        page.wait_for_timeout(
                            2000
                        )

                        return True

                except Exception:

                    pass

            # -------------------------------------------------
            # EXACT TEXT FALLBACK
            # -------------------------------------------------

            if name:

                try:

                    result = page.get_by_text(
                        name,
                        exact=True
                    ).first

                    if result.is_visible():

                        print(
                            f"Contact found by text: {name}"
                        )

                        result.click()

                        page.wait_for_timeout(
                            2000
                        )

                        return True

                except Exception:

                    pass

            # -------------------------------------------------
            # ROW FALLBACK
            # -------------------------------------------------

            try:

                rows = page.locator(
                    "#pane-side [role='row']"
                )

                for i in range(
                    rows.count()
                ):

                    row = rows.nth(i)

                    try:

                        if not row.is_visible():
                            continue

                        text = (
                            row.inner_text()
                            .strip()
                        )

                        normalized_text = (
                            text
                            .replace(" ", "")
                            .replace("+", "")
                        )

                        normalized_phone = (
                            phone
                            .replace(" ", "")
                            .replace("+", "")
                        )

                        name_match = (
                            name
                            and name.lower()
                            in text.lower()
                        )

                        phone_match = (
                            phone
                            and normalized_phone
                            in normalized_text
                        )

                        if (
                            name_match
                            or phone_match
                        ):

                            print(
                                "Matching result row found."
                            )

                            row.click()

                            page.wait_for_timeout(
                                2000
                            )

                            return True

                    except Exception:

                        continue

            except Exception:

                pass

        except Exception as e:

            print(
                f"Search error: {e}"
            )

    return False


# =========================================================
# FIND MESSAGE BOX
# =========================================================

def get_message_box(page):

    print(
        "Looking for message box..."
    )

    page.wait_for_timeout(
        1000
    )

    labels = [
        "Type a message",
        "Message"
    ]

    for label in labels:

        try:

            locator = page.get_by_label(
                label,
                exact=False
            ).last

            if locator.is_visible(
                timeout=2000
            ):

                print(
                    f"Message box found using label: {label}"
                )

                return locator

        except Exception:

            pass

    selectors = [
        '[data-testid="conversation-compose-box-input"]',
        '[aria-placeholder="Type a message"]',
        '[placeholder="Type a message"]'
    ]

    for selector in selectors:

        try:

            locator = page.locator(
                selector
            ).last

            if locator.is_visible(
                timeout=2000
            ):

                print(
                    f"Message box found using: {selector}"
                )

                return locator

        except Exception:

            pass

    try:

        editables = page.locator(
            '#main [contenteditable="true"]'
        )

        for i in range(
            editables.count() - 1,
            -1,
            -1
        ):

            locator = editables.nth(i)

            if locator.is_visible():

                print(
                    "Message box found inside #main."
                )

                return locator

    except Exception:

        pass

    return None


# =========================================================
# TYPE MESSAGE
# =========================================================

def type_message(page, message):

    message_box = get_message_box(
        page
    )

    if message_box is None:

        return None

    try:

        print(
            f"Typing message: {message}"
        )

        message_box.click()

        page.wait_for_timeout(
            500
        )

        page.keyboard.press(
            "Meta+A"
        )

        page.keyboard.press(
            "Backspace"
        )

        message_box.press_sequentially(
            message,
            delay=40
        )

        print(
            "Message typed successfully."
        )

        return message_box

    except Exception as e:

        print(
            f"Typing failed: {e}"
        )

        return None


# =========================================================
# SEND MESSAGE
# =========================================================

def send_message(page, message_box):

    try:

        random_delay(
            page,
            2,
            5
        )

        message_box.press(
            "Enter"
        )

        print(
            "Message submitted."
        )

        page.wait_for_timeout(
            2000
        )

        return True

    except Exception as e:

        print(
            f"Send failed: {e}"
        )

        return False


# =========================================================
# VERIFY SENT MESSAGE
# =========================================================

def verify_message_sent(page, message):

    print(
        "Verifying sent message..."
    )

    page.wait_for_timeout(
        1500
    )

    try:

        matches = page.locator(
            "#main"
        ).get_by_text(
            message,
            exact=True
        )

        for i in range(
            matches.count() - 1,
            -1,
            -1
        ):

            try:

                if matches.nth(i).is_visible():

                    print(
                        "Sent message text detected."
                    )

                    return True

            except Exception:

                continue

    except Exception:

        pass

    print(
        "Message submitted but could not verify."
    )

    return False


# =========================================================
# CLEAN MESSAGE TEXT
# =========================================================

def clean_message_text(text):

    if not text:

        return ""

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:

            continue

        # Remove isolated timestamps
        if re.fullmatch(
            r"\d{1,2}:\d{2}\s*(AM|PM|am|pm)?",
            line
        ):

            continue

        lines.append(
            line
        )

    return "\n".join(
        lines
    ).strip()


# =========================================================
# GET MESSAGE TEXT
# =========================================================

def extract_message_text(row):

    # -----------------------------------------------------
    # METHOD 1: selectable-text
    # -----------------------------------------------------

    try:

        nodes = row.locator(
            "span.selectable-text"
        )

        texts = []

        for i in range(
            nodes.count()
        ):

            try:

                text = (
                    nodes.nth(i)
                    .inner_text()
                    .strip()
                )

                if (
                    text
                    and text not in texts
                ):

                    texts.append(
                        text
                    )

            except Exception:

                continue

        if texts:

            return clean_message_text(
                "\n".join(texts)
            )

    except Exception:

        pass

    # -----------------------------------------------------
    # METHOD 2: data-pre-plain-text
    # -----------------------------------------------------

    try:

        metadata_nodes = row.locator(
            "[data-pre-plain-text]"
        )

        if metadata_nodes.count() > 0:

            text = (
                metadata_nodes
                .first
                .inner_text()
            )

            cleaned = clean_message_text(
                text
            )

            if cleaned:

                return cleaned

    except Exception:

        pass

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    try:

        return clean_message_text(
            row.inner_text()
        )

    except Exception:

        return ""


# =========================================================
# FIND ACTUAL MESSAGE ELEMENT
# =========================================================

def get_message_visual_element(row):

    """
    Try to locate the actual message bubble inside a row.
    """

    selectors = [
        "[data-pre-plain-text]",
        "span.selectable-text"
    ]

    for selector in selectors:

        try:

            locator = row.locator(
                selector
            ).first

            if locator.count() > 0:

                return locator

        except Exception:

            continue

    return row


# =========================================================
# CLASSIFY MESSAGE USING SCREEN POSITION
# =========================================================

def classify_message_direction(
    page,
    row
):

    """
    Incoming messages appear on left side.
    Outgoing messages appear on right side.

    Returns:
        incoming
        outgoing
        unknown
    """

    try:

        main = page.locator(
            "#main"
        )

        main_box = main.bounding_box()

        if main_box is None:

            return "unknown"

        visual_element = (
            get_message_visual_element(
                row
            )
        )

        element_box = (
            visual_element.bounding_box()
        )

        if element_box is None:

            return "unknown"

        # Center of conversation panel
        main_center = (
            main_box["x"]
            + (
                main_box["width"]
                / 2
            )
        )

        # Center of current message text/bubble
        message_center = (
            element_box["x"]
            + (
                element_box["width"]
                / 2
            )
        )

        # -------------------------------------------------
        # Compare positions
        # -------------------------------------------------

        if message_center < main_center:

            return "incoming"

        if message_center > main_center:

            return "outgoing"

        return "unknown"

    except Exception:

        return "unknown"


# =========================================================
# SMART EXTRACTOR
# =========================================================

def extract_last_three_incoming_messages(
    page
):

    print(
        "\n" + "-" * 60
    )

    print(
        "SMART DATA EXTRACTION"
    )

    print(
        "-" * 60
    )

    page.wait_for_timeout(
        1500
    )

    incoming_messages = []

    try:

        main = page.locator(
            "#main"
        )

        rows = main.locator(
            '[role="row"]'
        )

        row_count = rows.count()

        print(
            f"Message rows detected: {row_count}"
        )

        if row_count == 0:

            return []

        # =================================================
        # ANALYSE EACH ROW
        # =================================================

        for i in range(
            row_count
        ):

            row = rows.nth(i)

            try:

                if not row.is_visible():

                    continue

                text = extract_message_text(
                    row
                )

                if not text:

                    continue

                # -----------------------------------------
                # Skip date separators
                # -----------------------------------------

                if re.fullmatch(
                    r"(Today|Yesterday)",
                    text,
                    flags=re.IGNORECASE
                ):

                    continue

                direction = (
                    classify_message_direction(
                        page,
                        row
                    )
                )

                print(
                    f"{direction.upper():8} | "
                    f"{text[:100]}"
                )

                if direction == "incoming":

                    incoming_messages.append(
                        text
                    )

            except Exception as e:

                print(
                    f"Row {i} error: {e}"
                )

                continue

        # =================================================
        # REMOVE DUPLICATES
        # =================================================

        unique_messages = []

        for message in incoming_messages:

            if (
                message
                and message
                not in unique_messages
            ):

                unique_messages.append(
                    message
                )

        last_three = (
            unique_messages[-3:]
        )

        print(
            "\nIncoming messages detected:",
            len(unique_messages)
        )

        print(
            "Returning last:",
            len(last_three)
        )

        return last_three

    except Exception as e:

        print(
            f"Extraction failed: {e}"
        )

        return []


# =========================================================
# SCREENSHOT
# =========================================================

def take_sent_screenshot(
    page,
    name
):

    try:

        os.makedirs(
            SCREENSHOT_DIR,
            exist_ok=True
        )

        safe_name = "".join(
            c if c.isalnum()
            else "_"
            for c in name
        )

        timestamp = (
            datetime.now()
            .strftime(
                "%Y%m%d_%H%M%S"
            )
        )

        filepath = os.path.join(
            SCREENSHOT_DIR,
            f"{safe_name}_{timestamp}.png"
        )

        page.screenshot(
            path=filepath,
            full_page=False
        )

        print(
            f"Screenshot saved: {filepath}"
        )

        return filepath

    except Exception as e:

        print(
            f"Screenshot failed: {e}"
        )

        return ""


# =========================================================
# PROCESS CONTACT
# =========================================================

def process_contact(
    page,
    name,
    phone,
    message
):

    result = {

        "name": name,

        "phone": phone,

        "message": message,

        "status": "failed",

        "screenshot": "",

        "last_3_messages_from_contact": [],

        "error": ""
    }

    try:

        print(
            "\n" + "=" * 60
        )

        print(
            f"PROCESSING: {name}"
        )

        print(
            "=" * 60
        )

        # -------------------------------------------------
        # SEARCH
        # -------------------------------------------------

        if not search_contact(
            page,
            name,
            phone
        ):

            result["error"] = (
                "Contact not found"
            )

            return result

        random_delay(
            page,
            2,
            5
        )

        # -------------------------------------------------
        # TYPE
        # -------------------------------------------------

        message_box = type_message(
            page,
            message
        )

        if message_box is None:

            result["error"] = (
                "Message box not found"
            )

            return result

        # -------------------------------------------------
        # SEND
        # -------------------------------------------------

        if not send_message(
            page,
            message_box
        ):

            result["error"] = (
                "Message send failed"
            )

            return result

        # -------------------------------------------------
        # VERIFY
        # -------------------------------------------------

        if verify_message_sent(
            page,
            message
        ):

            result["status"] = "sent"

        else:

            result["status"] = (
                "sent_unverified"
            )

        # -------------------------------------------------
        # SCREENSHOT
        # -------------------------------------------------

        result["screenshot"] = (
            take_sent_screenshot(
                page,
                name
            )
        )

        # -------------------------------------------------
        # EXTRACT LAST 3 INCOMING
        # -------------------------------------------------

        result[
            "last_3_messages_from_contact"
        ] = (
            extract_last_three_incoming_messages(
                page
            )
        )

        return result

    except Exception as e:

        result["error"] = str(e)

        print(
            f"Unexpected error for {name}: {e}"
        )

        return result


# =========================================================
# MAIN
# =========================================================

def main():

    contacts = load_contacts()

    if contacts is None:

        return

    if len(contacts) == 0:

        print(
            "No contacts found."
        )

        return

    print(
        "\nPrepared messages:"
    )

    for _, row in contacts.iterrows():

        name = str(
            row["Name"]
        ).strip()

        phone = str(
            row["Phone"]
        ).strip()

        message = prepare_message(
            name,
            str(
                row["Message"]
            ).strip()
        )

        print(
            "\n" + "-" * 50
        )

        print(
            "Name:",
            name
        )

        print(
            "Phone:",
            phone
        )

        print(
            "Message:",
            message
        )

    # =====================================================
    # START PLAYWRIGHT
    # =====================================================

    with sync_playwright() as p:

        print(
            "\nLaunching WhatsApp Web..."
        )

        context = (
            p.chromium
            .launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=False
            )
        )

        if context.pages:

            page = context.pages[0]

        else:

            page = context.new_page()

        page.set_default_timeout(
            10000
        )

        page.goto(
            WHATSAPP_URL,
            wait_until="domcontentloaded"
        )

        print(
            "WhatsApp Web opened."
        )

        if wait_for_whatsapp_ready(
            page
        ):

            print(
                "WhatsApp login successful."
            )

        else:

            input(
                "If WhatsApp is ready, "
                "press ENTER..."
            )

        # =================================================
        # PROCESS CONTACTS
        # =================================================

        results = []

        total = len(
            contacts
        )

        for position, (_, row) in enumerate(
            contacts.iterrows(),
            start=1
        ):

            print(
                "\n" + "#" * 60
            )

            print(
                f"CONTACT {position} OF {total}"
            )

            print(
                "#" * 60
            )

            name = str(
                row["Name"]
            ).strip()

            phone = str(
                row["Phone"]
            ).strip()

            message = prepare_message(
                name,
                str(
                    row["Message"]
                ).strip()
            )

            result = process_contact(
                page,
                name,
                phone,
                message
            )

            results.append(
                result
            )

            if position < total:

                print(
                    "\nPreparing next contact..."
                )

                random_delay(
                    page,
                    2,
                    5
                )

        # =================================================
        # DISPLAY RESULTS
        # =================================================

        print(
            "\n" + "=" * 60
        )

        print(
            "RUN COMPLETE"
        )

        print(
            "=" * 60
        )

        for result in results:

            print(
                "\nContact:",
                result["name"]
            )

            print(
                "Phone:",
                result["phone"]
            )

            print(
                "Status:",
                result["status"]
            )

            print(
                "Screenshot:",
                result["screenshot"]
            )

            print(
                "Last 3 incoming messages:"
            )

            messages = result[
                "last_3_messages_from_contact"
            ]

            if messages:

                for number, message in enumerate(
                    messages,
                    start=1
                ):

                    print(
                        f"{number}. {message}"
                    )

            else:

                print(
                    "- None extracted"
                )

            if result["error"]:

                print(
                    "Error:",
                    result["error"]
                )

        print(
            f"\nProcessed: {len(results)} contacts"
        )

        input(
            "\nPress ENTER to close..."
        )

        context.close()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()