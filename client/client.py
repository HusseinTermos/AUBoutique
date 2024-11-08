#Client

'''
Content:
1-imports
2-url
3-main function
4-login function
5-register function
6-directing_to_products function
7-view_owner_products function
8-view_all_products function
9-displaying_products function
10-view_user_products_buyers function
11-adding products to the store function
12-buying products
13-display_image function
14-send_http_request
15-parse_http_resp
16-request
17-send_message function --text messaging
18-set_connection function --text messaging
19-initiate_chat --text messaging
20-chat --text messaging
21-start_text_listener --text messaging
22-chats
23-slow_print
24-display_products_details
'''



#1-imports
from socket import *
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta
import json
import base64
import threading
import time
import sys


#2-url
url = "http://localhost:9999"


#3-main function
def main():
    #global list of chat requests
    global chat_requests
    chat_requests = []

    #socket
    global sock1, sock2
    sock1 = socket(AF_INET, SOCK_STREAM)
    sock1.connect(('localhost', 9999))
    sock1.send(b'1')

    #welcoming
    slow_print("\n ---- Welcome to AUBoutique ---- \n")


    #choice of registering or login in
    slow_print("If you already have an account: Enter 1 \nTo create an account: Enter 2\n")
    

    choice = int(input("Please choose an option: "))
    
    #redirecting
    while True:
        try:
            if choice == 1:
                user_id  = login()
                break
            elif choice == 2:
                user_id = register()
                break
            else:
                choice = int(input("Please choose a valid option: "))
        except ValueError:
            print("Invalid input. Please enter a number!")
            choice = int(input("Please choose an option: "))
    
    #start sock2 (for chatting)
    sock2 = set_connection('localhost', 9999, user_id)

    #thread for listening (sock2)
    start_text_listener(sock2, user_id)

    #take to store
    directing_to_store(user_id)



#4-login function
def login():
     while True:
     
        #prompt the user to enter the credentials
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        
        #prepare data
        credentials = { "username": username, "password": password }
        
        #send the credentials for the server for authentication
        try:
            status_code, headers, response_data = request("POST", f"{url}/login", credentials)
        
            #if credentials are correct
            if status_code == 200:
                user_id = response_data.get("user_id")
                slow_print("Login successful. Redirecting to AUBoutique...\n")
                print("-" * 50)
                return user_id
            
            #if credentials are wrong
            else:
                slow_print("Login failed. Please check your username and password\n")

        except (ConnectionError, TimeoutError, OSError) as e:
            slow_print(f"An error occurred: {e}. Please try again.\n")
        #login function done





    
#5-register function
def register():
    while True:
        #prompt the user to enter the credentials
        slow_print("Please enter your data as requested... ")
        name = input("Enter your Full name: ")
        email_address = input("Enter your email address: ")
        username = input("Choose a username: ")
        password = input("Please note that the password must be at least 8 characters and has UpperCase and lowercase letters and special characters\nChoose a password: ")
        
        registration_data = {"name": name, "email_address": email_address,
                       "username": username, "password": password}
        
        #send credentials for the server
        try:
            status_code, headers, response_data = request("POST", f"{url}/register", registration_data)
        
            #if registration successful
            if status_code == 200:
                user_id = response_data.get("user_id")
                slow_print("Registration successful. Redirecting to AUBoutique...")
                print("-" * 50)
                return user_id
            
            #if credentials are wrong
            else:
                slow_print("Registration failed. Please try again\n")

        except (ConnectionError, TimeoutError, OSError) as e:
            slow_print(f"An error occurred: {e}. Please try again.\n")
            
    #Register function done






#6-function to give the user to either view a particular owner 
#or all the list of products
def directing_to_store(user_id):
    
    while True:

        #give choice to use functionalities found in the AUBoutique
        slow_print(
            "\n ---- AUBoutique Home ---- \n" +
            "To view all products: Enter 1\n" + 
            "To view products of a particular owner or send chat request to an owner: Enter 2\n" +
            "To view buyers of your products: Enter 3\n"+
            "To add a product for sale: Enter 4\n"+
            "To navigate to chatting: Enter 5\n"+
            "To Quit: Enter -1\n", delay=0.015
            )
        
        #take the choice and redirect to the function
        choice = int(input("Please choose an option: "))
        if choice == 1:
            view_all_products(user_id)
            
        elif choice == 2:
            view_owner_products(user_id)
            
        elif choice == 3:
            view_user_products_buyers(user_id)

        elif choice == 4:
            add_products(user_id)

        elif choice == 5:
            chats(user_id)

        elif choice == -1:
            sys.exit(1)

        else:
            slow_print("Please try again entering a valid option\n")



#7-function to view products of a particular owner
def view_owner_products(user_id):
    
    #request list from server and printing it 
    try:
        status_code, headers, response_data = request("GET", f"{url}/owners/{user_id}")

        owners = response_data["owners"]

        #go back if no owners
        if not owners:
            slow_print("Sorry, no owners available!")
            directing_to_store(user_id)

        else:
            
            #display ownres numbred acc to typical enumerating
            slow_print("\n--- Viewing Owners ---\n")
            for i, owner in enumerate(owners):
                owner_status = "online" if owner['status'] else "offline"
                slow_print(f"{i + 1}. {owner['username']} ({owner_status})\n")
            
            #give choice to text message with an owner
            choice_messaging = int(input("To chat with a specific owner, enter his/her number"
                                            +"\nTo choose view the products of a specific owner, enter 0"
                                            +"\nTo return to homepage, enter -1: "))
            
            #return to main
            if choice_messaging == -1:
                directing_to_store(user_id)

            #view products of specific owner
            elif choice_messaging == 0:
                #get choice of usr
                # Error handling try catch 
                while True:
                    choice = int(input("Please Enter -1 to return to homepage " +
                                        "\nOr select an owner by number: "))
                    if choice == -1:
                        directing_to_store(user_id)
                    elif choice-1 < 0 or choice-1 >= len(owners):
                        slow_print("Invalid selection. Please try again.")
                    else:
                        break
                
                #mapping no. to id
                owner_id = owners[choice-1]["id"]

                #request list of owner products from server and printing it 
                status_code, headers, response_data = request("GET", f"{url}/products/{owner_id}")

                #now i need to print the data provided by server (owner's products)
                product_map = display_products(response_data)

                #prompting the user to choose product to buy
                #give choice to return first
                #a loop to ensure the input is valid
                while True:
                    try:
                        #prompt to take choice
                        product_choice = input("\nTo buy a product, enter the number of the product in form: b[no. of product], e.g: b2,"
                                            +"\nTo view product image with all details, enter the number of the product in form: v[no. of product], e.g: v3,"
                                            +"\nOr enter 0 to chat with the owner,"
                                            + "\nOr enter -1 to return to homepage: ")
                        
                        #buy the product
                        if product_choice[0] == 'b':
                            if 1 <= int(product_choice[1]) <= len(product_map):
                                selected_product_id = product_map[int(product_choice[1]) - 1]
                                buy_product(user_id, selected_product_id)

                        #view full details along with the pic
                        elif product_choice[0] == 'v':
                            if 1 <= int(product_choice[1:]) <= len(product_map):
                                selected_product_id = product_map[int(product_choice[1:]) - 1]
                                display_products_details(response_data["products"][int(product_choice[1:]) - 1])

                        #returning to main page
                        elif int(product_choice) == -1:
                            directing_to_store(user_id)

                        #chat with the owner after viewing his products
                        elif int(product_choice) == 0:
                            slow_print("Chat request is being sent...")
                            owner_id = owners[choice-1]["id"]
                            owner_is_online = owners[choice-1]["status"]
                            owner_username = owners[choice-1]["username"]
                            initiate_chat(sock1, sock2, user_id, owner_id, owner_username, owner_is_online)
                    
                    except ValueError:
                        slow_print("Invalid input. Please enter a valid number!")


            #send chat request to chosen owner
            else:
                #send chat request and initiate chat
                slow_print("Chat request is being sent...")

                #info for initiating chat
                owner_id = owners[choice_messaging-1]["id"]
                owner_is_online = owners[choice_messaging-1]["status"]
                owner_username = owners[choice_messaging-1]["username"]

                #initiate chat
                initiate_chat(sock1, sock2, user_id, owner_id, owner_username, owner_is_online)
          
    except (ConnectionError, TimeoutError, OSError) as e:
        slow_print(f"An error occurred: {e}. Please try again.\n")






#8-view_all_prodcts
def view_all_products(user_id):
    try:
        status_code, headers, response_data = request("GET", f"{url}/products")
        
        # Check if the request was successful
        if status_code == 200: #OK HTTP
            #display products with main details
            product_map = display_products(response_data)

        while True:
            #give choices for navigating
            product_choice = input("\nTo buy a product, enter the number of the product in form: b[no. of product], e.g: b2,"
                                    +"\nTo view product image with all details, enter the number of the product in form: v[no. of product], e.g: v3,"
                                    +"\nOr enter -1 to return to homepage:  ")
            
            #go back to home page
            if product_choice == "-1":
                break

            #buy the product
            elif product_choice[0] == 'b':
                if 1 <= int(product_choice[1]) <= len(product_map):
                    selected_product_id = product_map[int(product_choice[1]) - 1]
                    buy_product(user_id, selected_product_id)
                    

            #view full details along with the pic
            elif product_choice[0] == 'v':
                if 1 <= int(product_choice[1:]) <= len(product_map):
                    selected_product_id = product_map[int(product_choice[1:]) - 1]
                    display_products_details(response_data["products"][int(product_choice[1:]) - 1])

    except (ConnectionError, TimeoutError, OSError) as e:
            slow_print(f"An error occurred: {e}. Please try again.\n")




#9-displaying products
def display_products(data):
    #product map is used to save the numbering of products
    #it'll be needed for buying process
    product_map = []
    slow_print("\n--- Available Products ---\n", delay=0.015)
    for i, product in enumerate(data["products"]):
        #display_image(product["image"]) # HN SHOULD NOT BE CALLED D8RE, MY LAPTOP IS CRYING
        product_data = f"""
        Product Number:     {i + 1}
        Product Name:       {product["name"]}
        Price:              ${product["price"]}
        Available:          {"Yes" if product["available"] else "No"}
        """
    
        slow_print(product_data, delay=0.01)
        print("-" * 50)
        product_map.append(product['id'])
    return product_map





#10-displaying user's product buyers
def view_user_products_buyers(user_id):

    #request
    try:
        status_code, headers, response_data = request("GET", f"{url}/my_products/{user_id}")
        
        # Check if the request was successful
        if status_code == 200:
            slow_print("\n--- Buyers of Your Products ---\n")
            for product in response_data["products"]:
                buyer_info = f"""
                Product Name:   {product["name"]}
                Buyer:          {product["buyer_name"]}
                """
                slow_print(buyer_info)
                print("-" * 30)

        choice = int(input("Press -1 to return to homepage"))
        if choice == "-1":
            directing_to_store(user_id)

    except (ConnectionError, TimeoutError, OSError) as e:
        slow_print(f"An error occurred: {e}. Please try again.\n")





#11-adding products to the store
def add_products(user_id):
    while True:

        #info taking
        slow_print("Enter the required information for your product as instructed:\n")
        name = input("Enter the name of your product: ")
        image_path = input("Enter the path of your image: ")

        #read image
        try:
            with open(image_path, "rb") as image_file:
                image = image_file.read()
        except FileNotFoundError:
            slow_print("Image file not found. Please check the path and try again.\n")
            continue
        except Exception as e:
            slow_print(f"An error occurred while reading the image file: {e}\n")
            continue
        
        #continue info taking
        price = input("Enter the price of your product: ")
        description = input("Enter the description of your product: ")
        ext_i = image_path.rfind('.')
        ext = image_path[ext_i:] if ext_i != -1 else ''
        product_data = {
            "name": name, 
            "image": {"content": base64.b64encode(image).decode(), "extension": ext},
            "price": price, 
            "description": description,
            "user_id": user_id
        }

        try:
            status_code, headers, response_data = request("POST", f"{url}/products", product_data)
        
            #if the item was added
            if status_code == 200:
                slow_print("Your product has been successfully added!\n")
                print("-" * 50)
                choice = input("Do you want to add another product? If yes press 1, else press -1 to return to homepage.")

                #if the user chooses 0, the loop stops. Else, the user keeps adding new products
                if choice == '-1':
                    directing_to_store(user_id)

            #if product was not added
            else:
                slow_print("Addition of product failed. Please try again.")
    
        except (ConnectionError, TimeoutError, OSError) as e:
            slow_print(f"An error occurred: {e}. Please try again.\n")
  



#12-buying products
def buy_product(user_id, product_id):
    try:
        #prepare info
        product_info = {
            "user_id": user_id, 
            "product_id": product_id
        }

        #send info of product to be bought
        status_code, headers, response_data = request("POST", f"{url}/buy_product", product_info)
        
        #pickup time printing
        if status_code == 200:
            collection_date = response_data["pickup_time"]
            slow_print(f"Product purchased successfully! Please collect it from the AUB Post Office on {collection_date}.")
            print("-" * 50)

        #purchase failed
        else:
            slow_print("Purchase failed. The product may no longer be available.")
            
    except (ConnectionError, TimeoutError, OSError) as e:
        slow_print(f"An error occurred while attempting to buy the product: {e}\n")



#13-display_image
def display_image(encoded_image):
    image_data = base64.b64decode(encoded_image)
    image_file = BytesIO(image_data)
    img = Image.open(image_file)
    img.save("k.png")
    img.show()


#14-send_http_request
def send_http_request(method, url, json_data=None):

    #host - port - path
    host = 'localhost'
    path = '/' + url.split('localhost')[-1].split('/', 1)[-1]

    #create the string for request
    if json_data:
        body = json.dumps(json_data)
    else:
        body = ""

    request = (
        f"{method} {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: keep-alive\r\n\r\n"
        f"{body}"
    )

    #sending request
    sock1.sendall(request.encode('utf-8'))

    #receive response
    response = b""
    while b"\r\n\r\n" not in response:
        part = sock1.recv(4096)
        response += part
    
    headers, body = response.split(b"\r\n\r\n", 1)
    content_length = int([line.split(b": ")[1] for line in headers.split(b"\r\n") if b"Content-Length" in line][0])
    
    while len(body) < content_length:
        body += sock1.recv(min(4096, content_length - len(body)))
    
    #return the response
    resp = headers.decode('utf-8') + "\r\n\r\n" + body.decode('utf-8')
    return resp


#15-parsing http response
def parse_http_resp(response):
    #extract headers and body from each other
    headers, body = response.split("\r\n\r\n", 1)
    header_lines = headers.split("\r\n")

    #parse status line --it's the fist line of headers
    status_line = header_lines[0].split()
    status_code = int(status_line[1])

    #parsing the headers
    response_headers = {}
    for line in header_lines[1:]:
        key, value = line.split(": ",1)
        response_headers[key] = value
    
    #if there's json --> parse body as json
    json_checker = response_headers.get('Content-Type', '')
    if 'application/json' in json_checker:
        json_data = json.loads(body)
    
    return status_code, response_headers, json_data



#16-wrapper function for better performnce
def request(method, url, json_data=None):
    #call both functions to complete the whole thing
    response = send_http_request(method, url, json_data)
    status_code, headers, json_data = parse_http_resp(response)

    #return needed info
    return status_code, headers, json_data



#17-send_message
def send_message(sock2, user_id, recipient_id, message):
    try:
        content = f"{user_id} {recipient_id} {message}"
        size = str(len(content)).rjust(3, '0')
        sock2.sendall(str(size).encode('utf-8') + b' ' + content.encode('utf-8'))
    except OSError as e:
        slow_print(f"Error sending message: {e}")



#18-set_connection
def set_connection(host, port, user_id):
    try:
        sock2 = socket(AF_INET, SOCK_STREAM)
        sock2.connect((host, port))
        sock2.sendall(b'2')
        server_query = sock2.recv(1)
        if server_query == b'?':
            sock2.sendall(str(user_id).encode('utf-8'))
        server_resp = sock2.recv(1)
        if server_resp != b'!': print("mshkle")
    except (ConnectionRefusedError, OSError) as e:
        slow_print(f"Connection error: {e}. Unable to connect to the server.")
        return None
    return sock2



#19-initiate_chat
def initiate_chat(sock1, sock2, user_id, target_user_id, target_username, user_online):
    #variable for sake of chat_accept
    global response

    # Check if the target user is online
    if user_online:
        request_msg = f"CHAT_REQUEST {user_id} {target_user_id}".encode('utf-8')
        size = str(len(request_msg)).rjust(3, '0').encode('utf-8')
        msg = size + b' ' + request_msg
        sock2.sendall(msg)

        #give choice to cancel request
        response = None
        while True:
            for _ in range(50):
                time.sleep(1)
                if response is not None: break

            if response:
                break
            else:
                req_choice = int(input("Enter 0 to continue waiting for approval \nOr enter 1 to cancel request"))
                if req_choice == 0:
                    continue
                else:
                    slow_print("Your request id being cancelled, please wait!")
                    to_send = f"CANCEL_REQUEST {user_id} {target_user_id}"
                    sock2.sendall("CANCEL_REQUEST")
                    slow_print("Your request has been cancelled, directing back to homepage!")
                    directing_to_store(user_id)

        if response == "CHAT_ACCEPT":
            slow_print("Your messaging request was accepted. You may start chatting.")
            chat(sock2, user_id, target_user_id)
        else:
            slow_print("The user is currently offline or unavailable.")
    else:
        slow_print("User is not online.")
        directing_to_store(user_id)



#20-start chat
def chat(sock2, user_id, target_user_id):
    global ongoing
    #give choice to end the chat when needed
    slow_print("You can enter messages now \nType '-1' whenever you want to end the chat.",delay=0.01)

    #take message inputs and send them / terminate from chatting 
    while ongoing:
        message = input()
        #chat end
        if not ongoing:
            if message != "-1" and message != "":
                print("Chat was ended, your message will not be delivered")
            break
        
        if message == '-1':
            slow_print("Ending chat.")
            ongoing = False
            to_send = f"END {user_id} {target_user_id}".encode('utf-8')
            length = str(len(to_send)).rjust(3, '0').encode()
            sock2.sendall(length + b' ' + to_send)
            directing_to_store(user_id)
        else:
            send_message(sock2, user_id, target_user_id, message)
    


#21-waiting for request of text messaging
def start_text_listener(sock2, user_id):
    def listen_for_requests():
        global response, ongoing
        while True:
            try:
                #listen for request
                length = int(sock2.recv(4))# HN error handling
                message = sock2.recv(length).decode()
                if message.startswith("CHAT_REQUEST"):
                    sender_id, sender_username = message.split()[1:]
                    chat_requests.append((sender_id, sender_username))
                    slow_print(f"\nNOTIFICATION: You have a chat request from user {sender_username}.\n")
                    slow_print("To accept request and start chatting, please enter -1 to return to homepage, then navigate to chatting! ") # HN ma t2ol "press -1"
                
                elif message.startswith("CANCEL_REQUEST"):
                    target_id, target_username = message.split()[1:]
                    chat_requests.remove((target_id, target_username))

                elif message.startswith("NEW_MSG"):
                    sender_id, sender_username, message = message.split(' ', 3)[1:] # Verify this is the correct chat HN
                    print(f"{sender_username}: {message}")

                elif message.startswith("CHAT_ACCEPT"):
                    ongoing = True
                    response = "CHAT_ACCEPT"

                elif message.startswith("CHAT_REJECT"):
                    ongoing = False
                    response = "CHAT_REJECT"

                elif message.startswith("END"):
                    ongoing = False
                    sender = message.split(' ')[1]
                    slow_print(f"{sender} has ended the chat.\nPress enter to return to homepage!")

                else:
                    sender, message = message.split(' ',1)

            except Exception as e: # HN edited this temporarily
                slow_print(f"Error: Could not receive message request: {e}")
                raise e
                break

    # Start the listening thread
    listener_thread = threading.Thread(target=listen_for_requests, daemon=True)
    listener_thread.start()




#22-chats
def chats(user_id):
    global ongoing
    ctr = 1
    printed_list =[]


    #print avalilable chat requests
    slow_print("\n--- Chat Requests ---\n")
    for id, username in chat_requests:
        printed_list.append(username)
        slow_print(str(ctr) + ". " + username)
        ctr +=1
    
    choice = int(input("Please enter the number of chat request you want to accept: "))

    #check if the request was canceled
    if chat_requests[choice-1][1] == printed_list[choice-1]:
        
        to_send = f"CHAT_ACCEPT {chat_requests[choice-1][0]} {user_id}".encode()
        size = str(len(to_send)).rjust(3, '0').encode()
        ongoing = True
        sock2.sendall(size + b" " + to_send)
        selected_request = chat_requests[choice-1]
        selected_user_id = selected_request[0]
        selected_username = selected_request[1]
        chat_requests.pop(choice-1)
        slow_print(f"You are now chatting with {selected_username}!")
        chat(sock2, user_id, selected_user_id)

    else:
        slow_print(f"{printed_list[choice-1]} has canceled the request")
        slow_print("Going back to homepage...")
        directing_to_store(user_id)



#23-slow_print
def slow_print(text, delay=0.02):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


#24-display_products_details
def display_products_details(data):
    #product map is used to save the numbering of products
    #it'll be needed for buying process
    product_map = []
    slow_print("\n--- Product Details ---\n", delay=0.015)
    display_image(data["image"])
    product_data = f"""
    Product Name:       {data["name"]}
    Date Added:         {data["date_time_added"]}
    Owner:              {data["owner_name"]}
    Price:              ${data["price"]}
    Available:          {"Yes" if data["available"] else "No"}
    Description:        {data["description"]}
    """

    slow_print(product_data, delay=0.01)
    print("-" * 50)
    product_map.append(data['id'])
    return product_map


if __name__ == "__main__":
    main()
    if sock1:
        sock1.close()
    if sock2:
        sock2.close()