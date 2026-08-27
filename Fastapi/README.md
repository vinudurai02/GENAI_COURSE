# FastAPI Calculator API

A simple calculator REST API built using **Python and FastAPI**.

This project is designed to learn the fundamentals of FastAPI, including API endpoints, HTTP methods, query parameters, path parameters, request bodies, Pydantic validation, error handling, JSON responses, and interactive API documentation.

## Features

The Calculator API supports:

- Addition
- Subtraction
- Multiplication
- Division
- Square calculation
- Power calculation
- POST-based calculations
- Calculation history
- Retrieve individual calculations
- Clear calculation history
- Input validation
- Error handling
- Automatic Swagger API documentation

## Technologies Used

- Python 3
- FastAPI
- Uvicorn
- Pydantic

## Project Structure

```text
fastapi-calculator/
│
├── calculator.py
└── README.md
```

## Installation

### 1. Create a Project Folder

```bash
mkdir fastapi-calculator
cd fastapi-calculator
```

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

macOS/Linux:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

### 4. Install Required Packages

```bash
pip install fastapi uvicorn
```

## Running the Application

Start the FastAPI application using Uvicorn:

```bash
uvicorn calculator:app --reload --port 8001
```

The API will run at:

```text
http://127.0.0.1:8001
```

## Interactive API Documentation

FastAPI automatically generates Swagger documentation.

Open:

```text
http://127.0.0.1:8001/docs
```

The `/docs` page can be used to test all API endpoints directly from the browser.

---

# API Endpoints

## 1. Home

**Method:** `GET`

**Endpoint:**

```text
/
```

Example response:

```json
{
    "message": "Calculator API is running",
    "docs": "/docs"
}
```

---

## 2. Addition

**Method:** `GET`

**Endpoint:**

```text
/add
```

Example request:

```text
/add?a=10&b=20
```

Example response:

```json
{
    "operation": "add",
    "a": 10,
    "b": 20,
    "result": 30
}
```

Here, `a` and `b` are **query parameters**.

---

## 3. Subtraction

**Method:** `GET`

Example:

```text
/subtract?a=20&b=5
```

Response:

```json
{
    "operation": "subtract",
    "a": 20,
    "b": 5,
    "result": 15
}
```

---

## 4. Multiplication

**Method:** `GET`

Example:

```text
/multiply?a=10&b=5
```

Response:

```json
{
    "operation": "multiply",
    "a": 10,
    "b": 5,
    "result": 50
}
```

---

## 5. Division

**Method:** `GET`

Example:

```text
/divide?a=100&b=20
```

Response:

```json
{
    "operation": "divide",
    "a": 100,
    "b": 20,
    "result": 5
}
```

The API also handles division by zero.

Example:

```text
/divide?a=100&b=0
```

The server returns an error response instead of attempting the calculation.

---

## 6. Square

This endpoint demonstrates a **path parameter**.

**Method:** `GET`

Example:

```text
/square/10
```

Here:

```text
10
```

is passed as part of the URL.

Response:

```json
{
    "number": 10,
    "result": 100
}
```

---

## 7. Power

This endpoint demonstrates query parameters and default values.

**Method:** `GET`

Example:

```text
/power?number=2&power=3
```

Response:

```json
{
    "number": 2,
    "power": 3,
    "result": 8
}
```

If `power` is not supplied, the application uses the default value defined in the Python function.

---

# POST Calculator

The `/calculate` endpoint demonstrates how a client can send JSON data to FastAPI.

**Method:** `POST`

**Endpoint:**

```text
/calculate
```

Example request body:

```json
{
    "a": 100,
    "b": 20,
    "operation": "divide"
}
```

Example response:

```json
{
    "id": 1,
    "a": 100,
    "b": 20,
    "operation": "divide",
    "result": 5
}
```

Supported operations are:

```text
add
subtract
multiply
divide
```

## Pydantic Validation

The POST request uses a Pydantic model:

```python
class Calculation(BaseModel):
    a: float
    b: float
    operation: str
```

This tells FastAPI that the client must provide:

```text
a           → number
b           → number
operation   → string
```

FastAPI automatically validates incoming data before executing the calculation.

---

# Calculation History

Calculations performed through the POST `/calculate` endpoint are stored temporarily in a Python list.

## View All History

**Method:** `GET`

```text
/history
```

Example response:

```json
{
    "count": 2,
    "calculations": [
        {
            "id": 1,
            "a": 100,
            "b": 20,
            "operation": "divide",
            "result": 5
        },
        {
            "id": 2,
            "a": 10,
            "b": 5,
            "operation": "multiply",
            "result": 50
        }
    ]
}
```

## View One Calculation

**Method:** `GET`

Example:

```text
/history/1
```

This returns the calculation with ID `1`.

If the requested calculation does not exist, FastAPI returns a `404` error.

---

# Delete Calculation History

**Method:** `DELETE`

```text
/history
```

This removes all calculations currently stored in memory.

Example response:

```json
{
    "message": "Calculation history cleared"
}
```

---

# Understanding the API Flow

The basic communication flow is:

```text
CLIENT
Postman / Browser / Swagger
        │
        │ HTTP Request
        ▼
     UVICORN
        │
        ▼
     FASTAPI
        │
        ▼
   Python Function
        │
        ▼
   Calculation
        │
        ▼
  JSON Response
        │
        ▼
      CLIENT
```

For example:

```text
POSTMAN

POST /calculate

{
    "a": 10,
    "b": 20,
    "operation": "add"
}

        │
        ▼

FASTAPI

        │
        ▼

Pydantic validates data

        │
        ▼

Python calculates

10 + 20 = 30

        │
        ▼

FastAPI returns JSON

        │
        ▼

POSTMAN

{
    "result": 30
}
```

# GET vs POST

### GET

GET is mainly used to **retrieve information**.

Example:

```text
GET /add?a=10&b=20
```

The parameters are included in the URL.

### POST

POST is commonly used when the client needs to **send data to the server for processing or creation**.

Example:

```text
POST /calculate
```

with JSON body:

```json
{
    "a": 10,
    "b": 20,
    "operation": "add"
}
```

# API Testing

The API can be tested using:

- Browser
- FastAPI Swagger `/docs`
- Postman
- Other frontend applications
- Other APIs or services

For GET endpoints, the browser can be used directly.

For POST and DELETE requests, Swagger or Postman provides an easier testing interface.

# Important Note About History

The calculation history is stored in a normal Python list.

It is **not stored in a database**.

Therefore, when the Uvicorn server is stopped or restarted, the calculation history will be lost.

A future version of the project could use:

```text
FastAPI
   ↓
Python
   ↓
SQLite Database
```

to permanently store calculation history.

# Concepts Learned

This project demonstrates:

- FastAPI application creation
- Uvicorn web server
- REST API basics
- Client-server communication
- HTTP methods
- GET requests
- POST requests
- DELETE requests
- Query parameters
- Path parameters
- JSON request bodies
- JSON responses
- Pydantic models
- Data validation
- HTTP status codes
- Error handling
- In-memory data storage
- Swagger API documentation

## Future Improvements

Possible improvements include:

- Add SQLite database storage
- Add PUT endpoints
- Delete individual calculations
- Add calculation timestamps
- Add more mathematical operations
- Create a Streamlit frontend
- Connect Streamlit to the FastAPI backend
- Add automated API tests

## Author

Created as a learning project to understand Python, FastAPI, REST APIs, and client-server communication.