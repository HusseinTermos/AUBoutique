import json

def build_http_response(status_code, body, headers={"Content-Type":"application/json"}):
    """Formats the response according to the HTTP protocol"""
    status_messages = {200: "OK", 400: "Bad Request", 403: "Forbidden", 409: "Conflict", 404: "Page Not Found"}
    response =  f'HTTP/1.1 {status_code} {status_messages[status_code]}\r\n'
    for title, val in headers.items():
        response += f"{title}: {val}\r\n"
    response += f"Content-Length: {len(body)}\r\n"
    response = response.encode()
    response += b"\r\n" + body
    return response


def process_request(message):
    """Parses the HTTP response and extracts
    important fields"""
    first_line, rest = message.split(b'\r\n', 1)
    first_line = first_line.decode()
    method, url, version = first_line.split(' ', 2)
    headers, body = rest.split(b'\r\n\r\n', 1)
    headers = headers.decode()
    headers = headers.split('\r\n')
    headers_dict = {}
    for header in headers:
        field_name, value = header.split(": ", 1)
        headers_dict[field_name] = value
    
    res = {
        "method": method,
        "url": url,
        "version": version,
        "headers": headers_dict
    }
    
    if len(body) != 0:
        if headers_dict["Content-Type"] == "application/json":
            body = json.loads(body)
        elif headers_dict["Content-Type"] == "text/plain":
            body = body.decode()
        elif headers_dict["Content-Type"].startswith("multipart/form-data"):
            headers_dict["Content-Type"] = headers_dict["Content-Type"].split("; boundary=", 1)
            boundary = headers_dict["Content-Type"][1].encode()
            form_parts = body.split(boundary)[1:-1]
            form_parts_dicts = {}
            for part in form_parts:
                part = part[2:-4]
                part_headers, content = part.split(b"\r\n\r\n", 1)
                part_headers = part_headers.decode().split("; ")[1:]
                field_name = part_headers[0].split('=')[1][1:-1]
                cur_part = {}
                for header in part_headers[1:]:
                    header_name, val = header.split("=")
                    if val[0] == val[-1] == '"': val = val[1:-1]

                    cur_part[header_name] = val

                cur_part["content"] = content
                form_parts_dicts[field_name] = cur_part

            body = form_parts_dicts

        res["body"] = body

    return res


def prep_json(x):
    return json.dumps(x).encode()
