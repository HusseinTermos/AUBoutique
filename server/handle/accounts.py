from formatting import *
from validation import *


def handle_register(request, db):

    def register(account_info, db):
        # Validate the format of provided info
        name = account_info["name"]
        email = account_info["email_address"]
        username = account_info["username"]
        password = account_info["password"]
        if not validate_name(name): raise ValueError("Invalid name.")
        if not validate_email(email): raise ValueError("Invalid email.")
        if not validate_username(username): raise ValueError("Invalid username.")
        if not validate_password(password): raise ValueError("Invalid password.")
        
        user_id = db.add_account(account_info)
        if user_id == -1: raise ValueError("Email or username already in use.")    
        
        return user_id

    body = request["body"]
    try:
        user_id = register(body, db)
    except ValueError as e:
        if "Invalid" in str(e):
            response = build_http_response(status_code=400,
                                            body=prep_json({"message": str(e)}))
        elif "Email" in str(e):
            response = build_http_response(status_code=400,
                                body=prep_json({"message": "Email or username already in use."}))
    else:
        response = build_http_response(status_code=200,
                                        body=prep_json({"message": "Account created successfully",
                                                "user_id": user_id}))
    return response
        

def handle_login(request, db):
    """Validate credentials and facilitate login"""
    def login(account_credentials, db):
        user_id = db.get_user_id(account_credentials)
        if user_id == -1: raise ValueError("Invalid username or password")
        return user_id
    body = request["body"]
    try:
        user_id = login(body, db)
    except ValueError as e:
        response = build_http_response(status_code=403,
                                        body=prep_json({"message":str(e)}))
    else:
        response = build_http_response(status_code=200,
                                        body=prep_json({"message":"Login successful.", "user_id": user_id}))
    return response

