from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


# -------------------------
# GET - Home
# -------------------------

@app.get("/")
def home():
    return {
        "message": "Calculator API is running"
    }


# -------------------------
# GET - Addition
# Example:
# /add?a=10&b=20
# -------------------------

@app.get("/add")
def add(a: float, b: float):
    return {
        "a": a,
        "b": b,
        "operation": "addition",
        "result": a + b
    }


# -------------------------
# GET - Subtraction
# Example:
# /subtract?a=20&b=5
# -------------------------

@app.get("/subtract")
def subtract(a: float, b: float):
    return {
        "a": a,
        "b": b,
        "operation": "subtraction",
        "result": a - b
    }


# -------------------------
# POST model
# -------------------------

class Calculation(BaseModel):
    a: float
    b: float
    operation: str


# -------------------------
# POST - Calculator
# -------------------------

@app.post("/calculate")
def calculate(data: Calculation):

    if data.operation == "add":
        result = data.a + data.b

    elif data.operation == "subtract":
        result = data.a - data.b

    elif data.operation == "multiply":
        result = data.a * data.b

    elif data.operation == "divide":

        if data.b == 0:
            return {
                "error": "Cannot divide by zero"
            }

        result = data.a / data.b

    else:
        return {
            "error": "Invalid operation"
        }

    return {
        "a": data.a,
        "b": data.b,
        "operation": data.operation,
        "result": result
    }