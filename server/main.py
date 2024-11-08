import socket
import sys
import threading
import regex as re
from db import db_accessor
import os
from handle import *
from formatting import *

PRODUCT_IMAGES_DIR_NAME = "product_images"
SERVER_ADDRESS = ''

active_users = {}

def main():
    # Verify that port is provided
    if len(sys.argv) != 2:
        print("Usage: python server.py [PORT]")
        sys.exit(1)
    
    PORT = int(sys.argv[1])

    # Set up the socket and prepare for TCP connections
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_ADDRESS, PORT))
    server_socket.listen()
    
    # Create the file directory for product images if not already created
    try:
        os.mkdir(PRODUCT_IMAGES_DIR_NAME)
    except FileExistsError: pass


    print("server startup complete")
    # Listen for connection requests and handle every client in a
    # separate thread
    while True:
        client_socket, addr = server_socket.accept()
        print("Connection established.")
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()


def handle_request(request, db):
    """
    Handles HTTP requests sent to the server
    """
    match (request["url"], request["method"]):
        case ("/", "GET"):
            return home()
        case ("/register", "POST"):
            return handle_register(request, db)
        case ("/login", "POST"):
            return handle_login(request, db)
        case ("/products", "GET"):
            return handle_get_products(db, PRODUCT_IMAGES_DIR_NAME)
        case (url, "GET") if url.startswith("/products/"):
            owner_id = int(url[10:])
            return handle_get_products(db, PRODUCT_IMAGES_DIR_NAME, owner_id=owner_id)
        case ("/products", "POST"): 
            return handle_add_product(request, db, PRODUCT_IMAGES_DIR_NAME)
        case (url, "GET") if url.startswith("/owners/"):
            user_id = int(url[8:])
            return handle_get_owners(db, active_users, user_id)
        case (url, "GET") if url.startswith("/my_products/"):
            user_id = int(url[13:])
            return handle_get_user_products(db, PRODUCT_IMAGES_DIR_NAME, user_id)
        case ("/buy_product", "POST"):
            return handle_buy_product(request, db)
        

def set_user_active(user_id, messaging_socket):
    db = db_accessor()
    db.connect()
    username = db.get_username(user_id)
    db.close()
    if username is None:
        raise ValueError("Invalid user id")
    if username in active_users:
        raise ValueError("user already connected from diff socket")
    active_users[user_id] = {"socket": messaging_socket, 
                             "username": username, "accepted_req":set(), "pending": set()}

def handle_client(client_socket, addr):
    """
    Establishes connection made to the server
    """
    print("started_handling")   
    # Check which type of connection a socket is establishing
    socket_type = client_socket.recv(1)
    if socket_type == b'1':
        handle_socket_1(client_socket)
    elif socket_type == b'2':
        handle_socket_2(client_socket)
    else:
        raise ValueError("Invalid socket type")
    
def get_user_messaging_id(messaging_socket):
    """Gets the id of the user associated with a 
    messaging socket
    """
    messaging_socket.send(b"?")
    try:
        user_id = messaging_socket.recv(10)
    except ConnectionResetError:
        print("Connection closed")
    while True:
        try:
            user_id = int(user_id.decode())
        except ValueError:
            print("Invalid user id")
            messaging_socket.send(b'I') # Id is not an integer
        else:
            messaging_socket.send(b'!') # Successfully received id
            return user_id


def handle_send_message(message_request, db):
    """Relays chatmessages between users
    """
    sender_id = message_request["sender"]
    recipient_id = message_request["recipient"]
    message = message_request["message"]
    # Make sure the recipient is online
    if recipient_id not in active_users:
        to_send = format_message_response(f"CHAT_REJECT")
    # Make sure the recipient accepted the chat request from the sender
    elif sender_id not in active_users[recipient_id]["accepted_req"]:
        to_send = format_message_response(f"CHAT_REJECT")
    else:
        db.connect()
        sender_username = db.get_username(sender_id)
        db.close()
        to_send = format_message_response(f"NEW_MSG {sender_id} {sender_username} {message}")
    return recipient_id, to_send

def handle_request_chat(message_request, db):
    """Relays chat requests between users
    """

    sender_id = message_request["sender"]
    recipient_id = message_request["recipient"]
    db.connect()
    sender_username = db.get_username(sender_id)
    db.close()
    to_send = f"CHAT_REQUEST {sender_id} {sender_username}"
    length = str(len(to_send)).rjust(3, '0')
    to_send = length + " " + to_send
    # Mark the sender as "pending" a response to a char request from
    # the recipient
    active_users[recipient_id]["pending"].add(sender_id)
    return recipient_id, to_send

def handle_accept_chat(message_request, db):
    """Handles informing both parties that messaging has began"""
    requester = message_request["requester"]
    accepter = message_request["accepter"]
    # User may have canceled the request
    # The chatting session should end
    if requester not in active_users[accepter]["pending"]:
        requester_username = db.get_username(requester)
        to_send = format_message_response(f"END {requester_username}")
        return accepter, to_send
    else:
        active_users[accepter]["pending"].remove(requester)
        active_users[accepter]["accepted_req"].add(requester)
        active_users[requester]["accepted_req"].add(accepter)
        to_send = format_message_response("CHAT_ACCEPT").encode()
        return requester, to_send
def handle_reject_chat(message_request, db):
    """Handles informing the requester that 
    a messaging request was rejected"""

    requester = message_request["requester"]
    rejecter = message_request["rejecter"]
    if requester not in active_users[rejecter]["pending"]:
        requester_username = db.get_username(requester)
        to_send = format_message_response(f"END {requester_username}")
        return rejecter, to_send
    else:
        active_users[rejecter]["pending"].remove(requester)
        to_send = format_message_response("CHAT_REJECT").encode()
        return requester, to_send
    
def handle_cancel_request(message_request, db):
    """Handles informing request receivers that 
    the chat request has been canceled"""
    recipient_id, sender_id = message_request["receiver"], message_request["canceler"]
    # Check that the user did issue the request that he is now
    # trying to cancel
    if not sender_id in active_users[recipient_id]["pending"]:
        requester_username = db.get_username(recipient_id)
        to_send = format_message_response(f"END {requester_username}")
        return sender_id, to_send
        
    active_users[recipient_id]["pending"].remove(sender_id)
    db.connect()
    sender_username = db.get_username(sender_id)
    db.close()
    to_send = f"CANCEL_REQUEST {sender_id} {sender_username}".encode()
    size = str(len(to_send)).rjust(3, '0').encode()
    return size + b' ' + to_send


def handle_end_chat(message_request, db):
    """Handles informing parties that the chatting session
    has ended
    """
    users = message_request["users"]
    if (users[0] in active_users[users[1]]["accepted_req"] and
        users[1] in active_users[users[0]]["accepted_req"]):
        db.connect()
        username = db.get_username(users[0])
        db.close()
        return users[1], format_message_response(f"END {username}").encode()
    else: raise Exception()


def handle_message_request(message_request):
    """Handles responding to requests related to chat
    and updating the state of data appropriately through
    dedicated functions"""
    db = db_accessor()
    match message_request["request"]:
        case "send":
            recipient_id, to_send = handle_send_message(message_request, db)
            active_users[recipient_id]["socket"].send(to_send.encode())
            print("message sent")
        case "request":
            recipient_id, to_send = handle_request_chat(message_request, db)
            active_users[recipient_id]["socket"].sendall(to_send.encode())
            print("request sent")
        case "accept":
            print("accepttt")
            recipient_id, to_send = handle_accept_chat(message_request, db)
            active_users[recipient_id]["socket"].sendall(to_send)
            print("acceptance sent")
        case "reject":
            recipient_id, to_send = handle_reject_chat(message_request, db)
            active_users[recipient_id]["socket"].sendall(to_send)
            print("rejection sent")
        case "cancel":
            recipient_id, to_send = handle_cancel_request(message_request, db)
            active_users[recipient_id].sendall(to_send)
            print("cancelation sent")
        case "end":
            recipient_id, to_send = handle_end_chat(message_request, db)
            active_users[recipient_id]["socket"].sendall(to_send)
            print("END sent")
            

            

def handle_socket_2(messaging_socket):
    """Handles all traffic related to messaging"""
    db = db_accessor()
    user_id = get_user_messaging_id(messaging_socket)
    set_user_active(user_id, messaging_socket)
    while True:
        message_request = get_message_request(messaging_socket)
        if message_request is None: 
            break
        handle_message_request(message_request)
    print("Closing messaging connection...")
    messaging_socket.close()


def get_message_request(messaging_socket):
    """Handle parsing requests related to chatting
    and formating them"""
    try:
        length = int(messaging_socket.recv(4)[:-1].decode())
    except (ConnectionResetError, ValueError) as e:
        return None
    message = messaging_socket.recv(length).decode()
    print(message)
    if message.startswith("CHAT_REQUEST"):
        print("received: chat request")
        sender, recipient = map(int, message.split(" ")[1:])
        return {"request": "request", "sender": sender, "recipient": recipient}
    elif message.startswith("CHAT_ACCEPT"):
        print("received: chat accept")
        requester, accepter = map(int, message.split(" ")[1:])
        return {"request": "accept", "requester": requester, "accepter": accepter}
    elif message.startswith("CHAT_REJECT"):
        print("received: chat reject")
        requester, rejecter = map(int, message.split(" ")[1:])
        return {"request": "reject", "requester": requester, "rejecter": rejecter}
    elif message.startswith("CANCEL_REQUEST"):
        print("received: cancel request")
        sender, recipient = map(int, message.split(" ")[1:])
        return {"request": "cancel", "canceler": sender, "receiver": recipient}
    elif message.startswith("END"):
        print("received: END")
        users= list(map(int, message.split(" ", 2)[1:]))
        return {"request": "end", "users": users}
    else:
        print("received: new msg")
        sender, recipient, message = message.split(" ", 2)
        return {"request": "send", "sender": int(sender), "recipient": int(recipient), "message": message}
    
def handle_socket_1(client_socket):
    """Handles all HTTP requests to the server"""
    db = db_accessor("auboutique.db")
    while True:
        # Get the raw request
        request = get_request(client_socket)
        if request is None: break
        print("request received")
        # Parse the request
        processed_request = process_request(request)
        # The connection was closed from the client's side
        if processed_request["headers"].get("Connection", None) == "close":
            break
        else:
            db.connect()
            response = handle_request(processed_request, db)
            db.close()
            client_socket.sendall(response)
            print("response sent")
    print("Closing connection...")
    client_socket.close()

def get_request(client_socket):
    """Parses HTTP requests sent to the server"""
    message = b''
    # Read until all header fields are read
    while b"\r\n\r\n" not in message:
        try:
            new_chunk = client_socket.recv(1024)
        except ConnectionResetError:
            new_chunk = b''
        if new_chunk == b'': # connection is closed
            return None
        message += new_chunk
    # Determine what has already been received from the body
    # and what it's total size is
    headers, body = message.split(b"\r\n\r\n", 1)
    body_length_match = re.findall(rb"Content-Length: ([0-9]+)\r\n", headers)
    if body_length_match != []:
        body_length = int(body_length_match[0])
    else:
        body_length = 0
    # Receive the rest of the body
    while len(body) < body_length:
        try:
            new_body_chunk = client_socket.recv(min(1024, body_length-len(body)))
        except ConnectionResetError:
            new_body_chunk = b''
        if new_body_chunk == b'':
            return None
        body += new_body_chunk
    full_message = headers + b"\r\n\r\n" + body

    return full_message

if __name__ == "__main__":
    main()
