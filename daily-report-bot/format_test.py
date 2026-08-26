import pyautogui
import pyperclip
import time
import subprocess
from datetime import datetime


# ============================================================
# SETTINGS
# ============================================================

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

NEWS_URL = "https://news.google.com"


# ============================================================
# CURRENT DATE AND TIME
# ============================================================

now = datetime.now()

current_datetime = now.strftime("%Y-%m-%d %H:%M")
current_date = now.strftime("%Y-%m-%d")


# Excel filename
# Do NOT include .xlsx because Excel adds it automatically
excel_filename = f"daily_report_{current_date}"

saved_excel_filename = f"{excel_filename}.xlsx"


# Screenshot filename
screenshot_filename = f"daily_report_{current_date}.png"


print("Daily Report Bot")
print("Date & Time:", current_datetime)
print("Excel File:", saved_excel_filename)
print("Screenshot:", screenshot_filename)

print("Starting...")
time.sleep(2)


# ============================================================
# OPEN / BRING CHROME TO FRONT
# ============================================================

subprocess.run([
    "open",
    "-a",
    "Google Chrome"
])

time.sleep(3)


# ============================================================
# CREATE A NEW CHROME TAB
# ============================================================

subprocess.run([
    "osascript",
    "-e",
    '''
    tell application "Google Chrome"
        activate

        tell front window
            make new tab
        end tell
    end tell
    '''
])

time.sleep(2)


# ============================================================
# TYPE GOOGLE NEWS URL
# ============================================================

pyautogui.write(
    NEWS_URL,
    interval=0.03
)

pyautogui.press("enter")

time.sleep(3)

print("Google News opened.")


# ============================================================
# COPY WEBPAGE CONTENT
# ============================================================

print("Copying news data...")

pyautogui.hotkey(
    "command",
    "a"
)

time.sleep(1)

pyautogui.hotkey(
    "command",
    "c"
)

time.sleep(2)

print("News data copied.")


# ============================================================
# READ COPIED DATA
# ============================================================

page_text = pyperclip.paste()

lines = page_text.splitlines()


# ============================================================
# FILTER USEFUL ITEMS
# ============================================================

items = []

skip_words = [
    "Your briefing",
    "Today",
    "Thu",
    "Fri",
    "Sat",
    "Sun",
    "Mon",
    "Tue",
    "Wed",
    "Google News",
    "Home",
    "For you",
    "Following",
    "News Showcase",
    "See more headlines and perspectives"
]


for line in lines:

    line = line.strip()

    # Skip blank lines
    if line == "":
        continue

    # Skip unwanted menu items
    if line in skip_words:
        continue

    # Skip temperature values
    if "°" in line:
        continue

    # Skip very short text
    if len(line) < 25:
        continue

    # Avoid duplicates
    if line in items:
        continue

    items.append(line)

    # Stop after collecting 10 items
    if len(items) == 10:
        break


# ============================================================
# PRINT THE 10 ITEMS
# ============================================================

print("\nFiltered 10 items:")
print("--------------------------------")

for number, item in enumerate(items, start=1):
    print(f"{number}. {item}")

print("--------------------------------")
print("Total items collected:", len(items))


# ============================================================
# CLOSE TEMPORARY GOOGLE NEWS TAB
# ============================================================

print("\nClosing news tab...")

subprocess.run([
    "osascript",
    "-e",
    '''
    tell application "Google Chrome"
        tell front window
            close active tab
        end tell
    end tell
    '''
])

time.sleep(2)

print("News tab closed.")


# ============================================================
# OPEN MICROSOFT EXCEL
# ============================================================

print("\nOpening Microsoft Excel...")

subprocess.run([
    "open",
    "-a",
    "Microsoft Excel"
])

time.sleep(5)


# ============================================================
# CREATE NEW BLANK WORKBOOK
# ============================================================

print("Creating new workbook...")

pyautogui.hotkey(
    "command",
    "n"
)

time.sleep(4)

print("New workbook opened.")


# ============================================================
# PREPARE DATA FOR EXCEL
# ============================================================

excel_rows = []


# Header row
excel_rows.append(
    "Date & Time\tFetched Data\tComment"
)


# Add 10 news items
for item in items:

    row = (
        f"{current_datetime}"
        f"\t{item}"
        f"\tDaily news update"
    )

    excel_rows.append(row)


# Join all rows into one block of text
excel_data = "\n".join(excel_rows)


# ============================================================
# COPY EXCEL DATA TO CLIPBOARD
# ============================================================

pyperclip.copy(excel_data)

time.sleep(1)


# ============================================================
# PASTE INTO EXCEL
# ============================================================

print("Pasting data into Excel...")

pyautogui.hotkey(
    "command",
    "v"
)

time.sleep(4)

print("Data pasted successfully.")


# ============================================================
# AUTO-FIT EXCEL COLUMNS
# ============================================================

print("Auto-fitting Excel columns...")

subprocess.run([
    "osascript",
    "-e",
    '''
    tell application "Microsoft Excel"
        activate

        tell active sheet
            autofit columns of range "A:C"
        end tell

    end tell
    '''
])

time.sleep(3)

print("Excel columns formatted successfully.")


# ============================================================
# SAVE EXCEL FILE
# ============================================================

print("Saving Excel file...")

pyautogui.hotkey(
    "command",
    "shift",
    "s"
)

time.sleep(4)


# Type filename WITHOUT .xlsx
# Excel adds the extension automatically
pyautogui.write(
    excel_filename,
    interval=0.05
)

time.sleep(1)

pyautogui.press("enter")

time.sleep(5)

print(
    "Excel file saved as:",
    saved_excel_filename
)


# ============================================================
# TAKE SCREENSHOT
# ============================================================

print("Taking screenshot...")

# Allow Excel to settle after saving
time.sleep(2)

# Capture the full screen
screenshot = pyautogui.screenshot()

# Save in the directory where the script is being run
screenshot.save(
    screenshot_filename
)

print(
    "Screenshot saved as:",
    screenshot_filename
)


# ============================================================
# FINISHED
# ============================================================

print("\n================================")
print("AUTOMATION COMPLETED")
print("================================")

print("Items collected:", len(items))
print("Excel file:", saved_excel_filename)
print("Screenshot:", screenshot_filename)

print("================================")