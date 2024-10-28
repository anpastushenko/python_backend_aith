import uvicorn
import math
import json


def factorial(n):
    return math.factorial(n) if n >= 0 else None


def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def mean(data):
    return sum(data) / len(data) if data else None


async def app(scope, receive, send):
    path = scope["path"].strip("/")
    method = scope["method"]
    
    if method == "GET" and path.startswith("factorial"):
        n = parse_query_param(scope, "n")
        if n is not None:
            result = factorial(n)
            return await respond(send, 200, {"result": result})
        return await respond(send, 400, {"error": "Invalid or missing parameter 'n'"})

    elif method == "GET" and path.startswith("fibonacci"):
        n = parse_path_param(path, 1)
        if n is not None:
            result = fibonacci(n)
            return await respond(send, 200, {"result": result})
        return await respond(send, 400, {"error": "Invalid path parameter"})

    elif method == "POST" and path == "mean":
        body = await receive_body(receive)
        try:
            numbers = json.loads(body)
            result = mean([float(x) for x in numbers])
            return await respond(send, 200, {"result": result})
        except (ValueError, json.JSONDecodeError):
            return await respond(send, 400, {"error": "Invalid data"})

    return await respond(send, 404, {"error": "Not found"})


def parse_query_param(scope, param):
    query = scope["query_string"].decode()
    try:
        return int(query.split("=")[1])
    except:
        return None


def parse_path_param(path, index):
    try:
        return int(path.split("/")[index])
    except:
        return None


async def receive_body(receive):
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if not message.get("more_body", False):
            break
    return body


async def respond(send, status, body):
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [[b"content-type", b"application/json"]],
    })
    await send({
        "type": "http.response.body",
        "body": json.dumps(body).encode(),
    })

if __name__ == "__main__":
    uvicorn.run("hw1:app", port=8000, log_level="info")
