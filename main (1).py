from fastapi import FastAPI, HTTPException, Request
import sqlite3
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import logging
import ast
import astor

app = FastAPI()

# Define the origins that are allowed to communicate with your FastAPI backend
origins = [
    "http://localhost:3000",  # React frontend
    "http://127.0.0.1:3000"  # Alternate localhost
]

# Add CORS middleware to FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow these origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Data Structure for the AST Node
class Node:
    def __init__(self, type: str, left=None, right=None, value=None):
        self.type = type  # "operator" or "operand"
        self.left = left
        self.right = right
        self.value = value

# Helper function to create AST from rule string (naive parsing, better parsing can be applied)
def create_ast(rule_string: str) -> Node:
    if "AND" in rule_string:
        parts = rule_string.split("AND", 1)
        return Node(type="operator", left=create_ast(parts[0].strip()), right=create_ast(parts[1].strip()), value="AND")
    elif "OR" in rule_string:
        parts = rule_string.split("OR", 1)
        return Node(type="operator", left=create_ast(parts[0].strip()), right=create_ast(parts[1].strip()), value="OR")
    else:
        return Node(type="operand", value=rule_string)


# SQLite initialization
def init_db():
    conn = sqlite3.connect('rules.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_string TEXT
    )
    ''')
    conn.commit()
    conn.close()

# Endpoint to create a rule (without Pydantic, raw JSON handling)
@app.post("/create_rule")
async def create_rule(request: Request):
    try:
        body = await request.json()
        rule_string = body.get("rule_string")
        if not rule_string:
            raise HTTPException(status_code=400, detail="rule_string is required")

        # Create AST from the rule string
        rule_ast = create_ast(rule_string)

        # Save rule in SQLite database
        conn = sqlite3.connect('rules.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rules (rule_string) VALUES (?)", (rule_string,))
        conn.commit()
        conn.close()

        return {"message": "Rule created successfully", "rule_ast": str(rule_ast)}

    except Exception as e:
        logging.error(f"Error processing the request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")

# Function to evaluate the rule (updated)
def evaluate_ast(node: Node, data: dict) -> bool:
    if node.type == "operand":
        # Safely evaluate simple condition using a dict-based approach
        condition = node.value.replace(" ", "")
        for key in data.keys():
            condition = condition.replace(key, str(data[key]))
        try:
            return eval(condition)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid condition: {node.value}")
    elif node.type == "operator":
        left_result = evaluate_ast(node.left, data)
        right_result = evaluate_ast(node.right, data)
        if node.value == "AND":
            return left_result and right_result
        elif node.value == "OR":
            return left_result or right_result
    return False

# Endpoint to evaluate a rule (updated)
@app.post("/evaluate_rule")
async def evaluate_rule(request: Request):
    try:
        body = await request.json()
        rule_id = body.get("rule_id")
        data = body.get("data")

        if not rule_id or not isinstance(rule_id, int):
            raise HTTPException(status_code=400, detail="rule_id is required and should be an integer")
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="data should be a valid JSON object")

        # Fetch rule from SQLite based on rule_id
        conn = sqlite3.connect('rules.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rule_string FROM rules WHERE id=?", (rule_id,))
        rule_row = cursor.fetchone()

        if rule_row is None:
            raise HTTPException(status_code=404, detail="Rule not found")

        rule_string = rule_row[0]
        rule_ast = create_ast(rule_string)
        result = evaluate_ast(rule_ast, data)

        return {"rule": rule_string, "data": data, "result": result}

    except Exception as e:
        logging.error(f"Error processing the request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")


# Function to combine rule strings based on AND or OR conditions
def combine_asts(rule_strings, condition="and"):
    """
    Combine multiple rule strings using a given logical condition ('and' or 'or').

    Parameters:
    - rule_strings: List of rule strings to combine
    - condition: A string, either "and" or "or", to combine the conditions.
    
    Returns:
    - Combined rule string
    """
    if condition == "and":
        combined_string = " AND ".join(f"({rule})" for rule in rule_strings)
    elif condition == "or":
        combined_string = " OR ".join(f"({rule})" for rule in rule_strings)
    else:
        raise ValueError("Condition must be either 'and' or 'or'")

    return combined_string

# Updated endpoint to combine multiple rules using AND/OR
@app.post("/combine_rules")
async def combine_rules(request: Request):
    try:
        body = await request.json()
        rule_ids = body.get("rule_ids")
        condition = body.get("condition", "or").lower()  # Default to OR if no condition is provided

        if not isinstance(rule_ids, list) or not all(isinstance(rule_id, int) for rule_id in rule_ids):
            raise HTTPException(status_code=400, detail="rule_ids should be a list of integers")

        if condition not in ["and", "or"]:
            raise HTTPException(status_code=400, detail="Condition must be 'and' or 'or'")

        conn = sqlite3.connect('rules.db')
        cursor = conn.cursor()

        rule_strings = []
        for rule_id in rule_ids:
            cursor.execute("SELECT rule_string FROM rules WHERE id=?", (rule_id,))
            rule_row = cursor.fetchone()
            if rule_row:
                rule_string = rule_row[0]
                rule_strings.append(rule_string)

        # Combine rule strings
        combined_rule_string = combine_asts(rule_strings, condition)

        # Log the combined rule string for debugging
        print("Combined Rule String:", combined_rule_string)

        return {
            "message": "Rules combined",
            "combined_rule": combined_rule_string
        }

    except Exception as e:
        logging.error(f"Error processing the request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing the request: {str(e)}")


# Endpoint to fetch all rules
@app.get("/rules")
def get_rules():
    try:
        conn = sqlite3.connect('rules.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, rule_string FROM rules")
        rules = cursor.fetchall()
        conn.close()

        # Format the rules as a list of dictionaries
        rules_list = [{"id": rule[0], "rule_string": rule[1]} for rule in rules]
        return {"rules": rules_list}

    except Exception as e:
        logging.error(f"Error fetching rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching rules: {str(e)}")

# Initialize the database when the app starts
@app.on_event("startup")
def startup_event():
    init_db()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
