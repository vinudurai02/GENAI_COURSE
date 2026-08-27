# Student Grade Calculator

A simple Python program that calculates a student's letter grade based on their mark.

This version uses **Streamlit** to provide a simple web interface where the user can enter a mark and immediately calculate the corresponding grade.

## Features

- Enter a mark between **0 and 100**
- Calculate the corresponding letter grade
- Displays both the entered mark and calculated grade
- Simple Streamlit user interface
- Includes the grading scale for reference
- Prevents values below 0 or above 100

## Grading Scale

| Mark Range | Grade |
|---|---|
| 90 – 100 | A |
| 80 – 89 | B |
| 70 – 79 | C |
| 60 – 69 | D |
| Below 60 | E |

The grade boundaries are inclusive.

For example:

- 90 → Grade A
- 80 → Grade B
- 70 → Grade C
- 60 → Grade D
- 59 → Grade E

## Project Structure

```text
grade-system/
│
├── grade_system.py
└── README.md
```

## Requirements

- Python 3
- Streamlit

## Installation

### 1. Create a virtual environment

```bash
python3 -m venv venv
```

### 2. Activate the virtual environment

On macOS/Linux:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 3. Install Streamlit

```bash
pip install streamlit
```

## Running the Application

Run the following command from the project directory:

```bash
streamlit run grade_system.py
```

Streamlit will start a local development server and open the application in your browser.

The default address is usually:

```text
http://localhost:8501
```

## How It Works

The user enters a mark between 0 and 100 and clicks **Calculate Grade**.

The program uses Python conditional statements to determine the grade:

```python
if mark >= 90:
    grade = "A"
elif mark >= 80:
    grade = "B"
elif mark >= 70:
    grade = "C"
elif mark >= 60:
    grade = "D"
else:
    grade = "E"
```

The conditions are checked from top to bottom until a matching condition is found.

For example, if the user enters:

```text
85
```

the program checks:

```text
85 >= 90 → False
85 >= 80 → True
```

Therefore:

```text
Grade = B
```

## Example

### Input

```text
Mark: 85
```

### Output

```text
You entered 85. Your grade is B.
```

## Concepts Practiced

This project demonstrates several basic Python and Streamlit concepts:

- Variables
- User input
- Conditional statements
- `if`, `elif`, and `else`
- Comparison operators
- Python indentation
- Streamlit number inputs
- Streamlit buttons
- Displaying dynamic results
- Building a simple browser-based Python application

## Author

Created as part of a Python programming learning assignment.