# PyAutoGUI Daily Report Automation

## Assignment 1 - PyAutoGUI Automation

This project automates the preparation of a daily status report using Python and PyAutoGUI.

The bot controls the computer like a user by opening applications, moving the mouse, clicking, typing, copying information, and saving the final report.

## Objective

The goal is to automatically:

1. Open Google Chrome.
2. Navigate to a public website.
3. Copy useful information from the webpage.
4. Open Microsoft Excel or Numbers.
5. Add the information to a spreadsheet.
6. Add the current date and time automatically.
7. Add a short comment.
8. Save the spreadsheet with the current date in the filename.
9. Take a screenshot of the completed spreadsheet.

## Technologies Used

- Python 3
- PyAutoGUI
- Google Chrome
- Microsoft Excel / Apple Numbers
- `datetime`
- `time`

## Project Structure

```text
pyautogui-assignment/
├── daily_report_bot.py
└── README.md
```

After running the automation:

```text
pyautogui-assignment/
├── daily_report_bot.py
├── README.md
├── daily_report_YYYY-MM-DD.xlsx
└── daily_report_YYYY-MM-DD.png
```

## Installation

### 1. Create a virtual environment

```bash
python3 -m venv venv
```

### 2. Activate the virtual environment on Mac

```bash
source venv/bin/activate
```

### 3. Install PyAutoGUI

```bash
pip install pyautogui
```

## Running the Bot

Run the program from the terminal:

```bash
python daily_report_bot.py
```

or:

```bash
python3 daily_report_bot.py
```

## Automation Workflow

```text
Start
  ↓
Generate Current Date & Time
  ↓
Open Google Chrome
  ↓
Open Public Website
  ↓
Copy Required Information
  ↓
Open Excel / Numbers
  ↓
Create Daily Report
  ↓
Enter Date & Time
  ↓
Paste Fetched Data
  ↓
Enter Comment
  ↓
Save Spreadsheet
  ↓
Take Screenshot
  ↓
End
```

## Spreadsheet Format

The final spreadsheet contains three columns:

| Date & Time | Fetched Data | Comment |
|---|---|---|
| Current date and time | Data copied from website | Short status comment |

Example:

| Date & Time | Fetched Data | Comment |
|---|---|---|
| 2026-08-26 09:00:00 | Example news headline | Important update for today's operations. |

## Automatic Filename

The program generates the current date using Python's `datetime` module.

Example spreadsheet filename:

```text
daily_report_2026-08-26.xlsx
```

Example screenshot filename:

```text
daily_report_2026-08-26.png
```

The date is generated automatically at runtime and is not entered manually.

## PyAutoGUI Features Used

The project uses PyAutoGUI for:

- Opening applications
- Mouse movement
- Mouse clicks
- Keyboard typing
- Keyboard shortcuts
- Copying and pasting information
- Taking screenshots

## Safety

PyAutoGUI's fail-safe feature is enabled:

```python
pyautogui.FAILSAFE = True
```

If the automation behaves unexpectedly, move the mouse quickly to the **top-left corner of the screen** to stop the program.

## Important Note

PyAutoGUI works with actual screen positions.

Mouse coordinates and waiting times may need to be adjusted depending on:

- Screen resolution
- Application window size
- Internet speed
- Website layout
- Excel or Numbers version

The bot uses delays to allow applications and webpages enough time to load before continuing.

## Requirements

- Python 3
- PyAutoGUI
- Google Chrome
- Microsoft Excel or Apple Numbers
- macOS, Windows, or another supported desktop environment

## Main Python File

All automation code is maintained in a single file:

```text
daily_report_bot.py
```

This satisfies the assignment requirement of keeping the automation logic in one Python file.