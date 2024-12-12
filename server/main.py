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
        print("Usage: python main.py [PORT]")
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


def handle_request(request, db, addr):
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
        case (url, "GET") if url.startswith("/product/"):
            product_id, currency = url[9:].split('?currency=', 1)
            product_id = int(product_id)
            return handle_get_product(db, product_id, currency, PRODUCT_IMAGES_DIR_NAME)
        case (url, "GET") if url.startswith("/products/"):
            owner_id, currency = url[10:].split("?currency=", 1)
            owner_id = int(owner_id)
            return handle_get_products(db, PRODUCT_IMAGES_DIR_NAME, currency, owner_id=owner_id, active_users=active_users)
        case (url, "GET") if url.startswith("/products"):
            currency = url[19:]
            return handle_get_products(db, PRODUCT_IMAGES_DIR_NAME, currency)
        case ("/products", "POST"): 
            return handle_add_product(request, db, PRODUCT_IMAGES_DIR_NAME)
        case (url, "GET") if url.startswith("/owners/"):
            user_id = int(url[8:])
            return handle_get_owners(db, active_users, user_id)
        case (url, "GET") if url.startswith("/my_products/"):
            user_id, currency = url[13:].split("?currency=", 1)
            user_id = int(user_id)
            return handle_get_user_products(db, PRODUCT_IMAGES_DIR_NAME, user_id, currency)
        case ("/buy_product", "POST"):
            return handle_buy_product(request, db)
        case (url, "GET") if url.startswith("/search?q="):
            query, currency = url[10:].split("&currency=", 1)
            return handle_search_products(db, query, currency, PRODUCT_IMAGES_DIR_NAME)
        case ("/messaging_info", "POST"):
            return handle_post_messaging_info(request, active_users, addr)
        case (url, "GET") if url.startswith("/messaging_info"):
            requested_id = int(url[16:])
            return handle_get_messaging_info(request, active_users, requested_id)
        case ("/rating", "POST"):
            return handle_add_rating(request, db)
        case (url, "GET") if url.startswith("/bought_products?user_id="):
            user_id, currency = url[25:].split("&currency=", 1)
            user_id = int(user_id)
            return handle_get_bought_products(user_id, db, PRODUCT_IMAGES_DIR_NAME, currency)
        case (url, "GET") if url.startswith("/most_sold"):
            currency = url[20:]
            return handle_get_most_sold_products(db, PRODUCT_IMAGES_DIR_NAME, currency)


def handle_client(client_socket, addr):
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
            response = handle_request(processed_request, db, addr)
            db.close()
            client_socket.sendall(response)
            print("response sent")
    print("Closing connection...")
    for user_id in active_users:
        if active_users[user_id][2] == addr:
            u = user_id
            break
    del active_users[u]
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
