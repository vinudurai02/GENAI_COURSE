from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional


app = FastAPI(
    title="Learning Calculator API",
    description="A simple FastAPI calculator for learning GET, POST, validation and API concepts.",
    version="1.0"
)


# --------------------------------------------------
# In-memory storage
# --------------------------------------------------

calculation_history = []


# --------------------------------------------------
# Pydantic Model
# Used for POST request body
# --------------------------------------------------

class Calculation(BaseModel):
    a: float
    b: float
    operation: str


# --------------------------------------------------
# 1. ROOT ENDPOINT
# GET /
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Calculator API is running",
        "docs": "/docs"
    }


# --------------------------------------------------
# 2. SIMPLE GET
# GET /add?a=10&b=20
# Query Parameters
# --------------------------------------------------

@app.get("/add")
def add(a: float, b: float):
    result = a + b

    return {
        "operation": "add",
        "a": a,
        "b": b,
        "result": result
    }


# --------------------------------------------------
# 3. MORE GET ENDPOINTS
# --------------------------------------------------

@app.get("/subtract")
def subtract(a: float, b: float):
    return {
        "operation": "subtract",
        "a": a,
        "b": b,
        "result": a - b
    }


@app.get("/multiply")
def multiply(a: float, b: float):
    return {
        "operation": "multiply",
        "a": a,
        "b": b,
        "result": a * b
    }


@app.get("/divide")
def divide(a: float, b: float):

    if b == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot divide by zero"
        )

    return {
        "operation": "divide",
        "a": a,
        "b": b,
        "result": a / b
    }


# --------------------------------------------------
# 4. PATH PARAMETER
# GET /square/10
# --------------------------------------------------

@app.get("/square/{number}")
def square(number: float):
    return {
        "number": number,
        "result": number * number
    }


# --------------------------------------------------
# 5. OPTIONAL QUERY PARAMETER
# GET /power?number=2&power=3
# power defaults to 2
# --------------------------------------------------

@app.get("/power")
def power(number: float, power: int = 2):
    return {
        "number": number,
        "power": power,
        "result": number ** power
    }


# --------------------------------------------------
# 6. POST REQUEST
# POST /calculate
# Body:
# {
#   "a": 10,
#   "b": 5,
#   "operation": "add"
# }
# --------------------------------------------------

@app.post("/calculate")
def calculate(data: Calculation):

    operation = data.operation.lower()

    if operation == "add":
        result = data.a + data.b

    elif operation == "subtract":
        result = data.a - data.b

    elif operation == "multiply":
        result = data.a * data.b

    elif operation == "divide":

        if data.b == 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot divide by zero"
            )

        result = data.a / data.b

    else:
        raise HTTPException(
            status_code=400,
            detail="Operation must be add, subtract, multiply or divide"
        )

    calculation = {
        "id": len(calculation_history) + 1,
        "a": data.a,
        "b": data.b,
        "operation": operation,
        "result": result
    }

    calculation_history.append(calculation)

    return calculation


# --------------------------------------------------
# 7. GET ALL CALCULATION HISTORY
# GET /history
# --------------------------------------------------

@app.get("/history")
def get_history():
    return {
        "count": len(calculation_history),
        "calculations": calculation_history
    }


# --------------------------------------------------
# 8. GET ONE CALCULATION
# GET /history/1
# --------------------------------------------------

@app.get("/history/{calculation_id}")
def get_calculation(calculation_id: int):

    for calculation in calculation_history:

        if calculation["id"] == calculation_id:
            return calculation

    raise HTTPException(
        status_code=404,
        detail="Calculation not found"
    )


# --------------------------------------------------
# 9. DELETE HISTORY
# DELETE /history
# --------------------------------------------------

@app.delete("/history")
def clear_history():

    calculation_history.clear()

    return {
        "message": "Calculation history cleared"
    }