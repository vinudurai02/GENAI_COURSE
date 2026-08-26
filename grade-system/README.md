# grade-system
Implement grade calculation based on marks

# Grade System

A simple Python program that accepts a student's mark and converts it into a corresponding letter grade.

The program runs entirely in the terminal and uses only standard Python. No external packages or frameworks are required.

## Grading Scale

| Mark Range | Grade |
|------------|-------|
| 90–100 | A |
| 80–89 | B |
| 70–79 | C |
| 60–69 | D |
| Below 60 | E |

The grade boundaries are inclusive. For example, a mark of `90` receives an **A**, while a mark of `80` receives a **B**.

## Features

- Accepts a mark from the user through the terminal.
- Supports marks from `0` to `100`.
- Converts the entered mark into grades A, B, C, D, or E.
- Handles decimal marks.
- Detects marks below `0` or above `100`.
- Handles non-numeric input without crashing.
- Displays both the entered mark and resulting grade.
- Uses only Python's standard functionality.

## Requirements

- Python 3
- No third-party packages or frameworks are required.

## Project Structure

```text
grade-system/
├── grade_system.py
```

## Error Handling

If the user enters a number outside the valid range:

```text
Enter your mark (0-100): 105
Invalid mark. Please enter a number between 0 and 100.
```

If the user enters something that is not a number:

```text
Enter your mark (0-100): hello
Invalid input. Please enter a number.
```

This prevents the program from crashing unexpectedly when invalid input is provided.


- User input
- Conditional statements (`if`, `elif`, `else`)
- Numeric conversion
- Exception handling using `try` and `except`
- Formatted output using f-strings
