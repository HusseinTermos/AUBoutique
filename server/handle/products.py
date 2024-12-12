from formatting import *
import base64
from datetime import datetime, timedelta
import os
from search import search_products
import json
import requests
import requests.exceptions
from time import sleep

cache = {}
def convert_price(price, origin_currency, target_currency): # TODO: make the request
    def helper(origin_currency):
        #TODO: use fewer API calls if possible
        ##################################################################
        # try:
        #     response = requests.get("https://v6.exchangerate-api.com/v6/2483d8a27383c07816aa886d/latest/USD").json()
            
        # except requests.exceptions.JSONDecodeError:
        #     return None

        # The below is temporary. Before the demo, we shoudl replace it
        # with the above line to actually send requests to the API
        ##################################################################
        with open("server/example_response.json") as r:
            response = json.loads(r.read())
        ##################################################################
        rates = response["rates"]
        cache[origin_currency] = (datetime.now(), rates)
    if not ((origin_currency in cache) and (cache[origin_currency][0] + timedelta(0, 0, 0, 0, 1)) >= datetime.now()):
        helper(origin_currency)
    return cache[origin_currency][1][target_currency] * price



def structure_product_data(product_data):
    """Reformat product data for convenient access"""
    new_product_data = {"name": product_data["name"]["content"].decode(),
                        "price": int(product_data["price"]["content"]),
                        "owner_id": int(product_data["owner_id"]["content"]),
                        "description": product_data["description"]["content"].decode(),
                        "image":{"content": product_data["image"]["content"],
                        "extension":product_data["image_file_ext"]["content"].decode()}}
    return new_product_data



def handle_add_product(request, db, product_imgs_dir_name):
    """Process product info and add them to the database"""
    def add_product(db, product_info):
        # Decode image data
        image_content = base64.b64decode(product_info["image"]["content"])
        ext = product_info["image"]["extension"]
        del product_info["image"]
        # Add product info the database
        product_id = db.add_product_info(product_info)
        if product_id == -1:
            return False
        # Save product image and add its file name to the database
        product_image_file_name = str(product_id) + "_" + product_info["name"] + ext
        product_image_file_path = os.path.join(product_imgs_dir_name, product_image_file_name)
        with open(product_image_file_path, "wb") as image_file:
            image_file.write(image_content)
        db.add_product_image_file_name(product_id, product_image_file_name)
        return True
    
    
    body = request["body"]
    if add_product(db, body):
        return build_http_response(status_code=200,
                                    body=prep_json({"message": "Product successfully added."}))
    else:
        return build_http_response(status_code=400,
                                    body=prep_json({"message": "Invalid product info."}))


def handle_get_product(db, product_id, currency, product_imgs_dir_name):
    """Provide data of a certain product"""
    def get_product(db, product_id):
        product_tuple = db.get_product(product_id)
        if product_tuple == None:
            return None
        return format_product_data(product_tuple, product_imgs_dir_name, currency)
    product_data = get_product(db, product_id)
    if product_data is None:
        return build_http_response(status_code=404, body=prep_json({"message": "Invalid product id"}))
    else:
        return build_http_response(status_code=200, body=prep_json({"message": "Product data successfully found",
                                                                    "product_data": product_data}))

    
def format_product_data(product_tuple, product_imgs_dir_name, target_currency):
    img_file_path = os.path.join(product_imgs_dir_name, product_tuple[4])
    with open(img_file_path, 'rb') as image_file:
        image = image_file.read()
        image = base64.b64encode(image).decode()
    return {"id": product_tuple[0],
            "date_time_added": product_tuple[1],
            "owner_id": product_tuple[2],
            "owner_name": product_tuple[9],
            "name": product_tuple[3],
            "image": image,
            # product_tuple[6] is the current currency
            "price": convert_price(product_tuple[5], product_tuple[6], target_currency), 
            "currency": target_currency,
            "quantity": product_tuple[7],
            "description": product_tuple[8],
            "available": product_tuple[7] > 0,
            "avg_rating": product_tuple[10],
            "rating_count": product_tuple[11]}


def handle_get_products(db, product_imgs_dir_name, currency, owner_id=None, active_users=None):
    assert owner_id is None or active_users is not None
    """Provide a list of all products and their data"""
    def get_products(db, owner_id):
        # Get a raw list of all products
        product_tuples = db.get_products(owner_id)
        product_jsons = []
        # Put the list of products in a convenient format
        for product_tuple in product_tuples:
            product_jsons.append(format_product_data(product_tuple, product_imgs_dir_name, currency))
            
        return product_jsons
    products = get_products(db, owner_id)
    json_data = {"message": "Products sent successfully.", "products": products}
    if owner_id is not None:
        json_data["is_online"] = owner_id in active_users
    return build_http_response(status_code=200,
                                body=prep_json(json_data))


def handle_get_owners(db, actice_users, user_id):
    """Returns a list of owners excluding `user_id`"""
    def get_owners(db, actice_users):
        # Get all owners data
        owners = db.get_all_owners()
        owners_dicts = []
        for owner in owners:
            # Exclude the user
            if owner[0] == user_id: continue
            owners_dicts.append({
                "id": owner[0],
                "username": owner[1],
                "status": owner[0] in actice_users
            })
        return owners_dicts
    owners = get_owners(db, actice_users)
    return build_http_response(status_code=200,
                               body=prep_json({"message": "Owners sent successfully.", "owners": owners}))

def handle_get_user_products(db, product_imgs_dir_name, user_id, currency):
    """Returns a list of products for sale by a specific user"""
    def get_products(db, product_imgs_dir_name, user_id):
        # Get all products of the user
        product_tuples = db.get_user_products(user_id)
        product_jsons = []
        for product_tuple in product_tuples:
            product_id = product_tuple[0]
            transaction_tuples = db.get_product_transactions(product_id)
            transactions = []
            for transaction_tuple in transaction_tuples:
                transactions.append({"date_time_bought": transaction_tuple[0],
                                     "buyer_username": transaction_tuple[1],
                                     "buyer_id": transaction_tuple[2],
                                     "pickup_time": transaction_tuple[3],
                                     "quantity": transaction_tuple[4]
                })

            # Read image data of the product
            img_file_path = os.path.join(product_imgs_dir_name, product_tuple[4])
            with open(img_file_path, 'rb') as image_file:
                image = image_file.read()
                image = base64.b64encode(image).decode()

            # Put data in a convenient format
            product_jsons.append({  "id": product_id,
                                    "date_time_added": product_tuple[1],
                                    "name": product_tuple[3],
                                    "image": image,
                                    "price": convert_price(product_tuple[5], product_tuple[6], currency),
                                    "currency": currency,
                                    "quantity": product_tuple[7],
                                    "description": product_tuple[8],
                                    "avg_rating": product_tuple[9],
                                    "rating_count": product_tuple[10],
                                    "transactions": transactions})
        return product_jsons
    
    user_products =  build_http_response(status_code=200,
                               body=prep_json({"message": "user products collected successfully.",
                                               "products": get_products(db, product_imgs_dir_name, user_id)}))
    return user_products

def handle_buy_product(request, db): # TODO: decrement product count
    """Facilitates buying products"""
    def buy_product(db, transaction_info):
        owner_id = db.get_product_owner(transaction_info["product_id"])
        # Can't buy your own product
        if owner_id == transaction_info["user_id"]:
            return None
        # Assume pickup time is after 2 days
        pickup_time_obj = datetime.now() + timedelta(2)
        pickup_time = pickup_time_obj.strftime("%Y-%m-%d %H:%M:%S")
        # Add the "buying" record to the database
        if not db.buy_product(transaction_info, pickup_time):
            return None
        else:
            return pickup_time
    pickup_time = buy_product(db, request["body"])
    if pickup_time is not None:
        return build_http_response(status_code=200, body=prep_json({"message": "Successfully bought product.", "pickup_time": pickup_time}))
    else:
        return build_http_response(status_code=400, body=prep_json({"message": "Invalid purchase request"}))

def handle_search_products(db, query, currency, product_imgs_dir_name):
    res = search_products(db, query, product_imgs_dir_name)
    for product in res:
        product["price"] = convert_price(product["price"], product["currency"], currency)

    return build_http_response(status_code=200, body=prep_json({"message": "Results found successfully.", "results": res}))

def handle_add_rating(request, db):
    def add_rating(db, user_id, product_id, rating):
        return db.add_rating(user_id, product_id, rating)
    user_id = request["body"]["user_id"]
    product_id = request["body"]["product_id"]
    rating = request["body"]["rating"]
    if rating not in range(1, 6):
        return build_http_response(status_code=400, body=prep_json({"message": "Invalid rating."}))
    
    success = add_rating(db, user_id, product_id, rating)
    if success:
        return build_http_response(status_code=200, body=prep_json({"message": "Rating added successfully"}))
    else:
        return build_http_response(status_code=400, body=prep_json({"message": "Rating addition failed"}))

def handle_get_bought_products(user_id, db, product_imgs_dir_name, currency):
    def get_bought_products(user_id, db):
        bought_products_tuples = db.get_bought_products(user_id)
        bought_products = []
        for product_tuple in bought_products_tuples:
            img_file_path = os.path.join(product_imgs_dir_name, product_tuple[10])
            with open(img_file_path, 'rb') as image_file:
                image = image_file.read()
                image = base64.b64encode(image).decode()
            bought_products.append({"time_bought": product_tuple[1],
                                    "id": product_tuple[2],
                                    "pickup_time": product_tuple[4],
                                    "quantity_bought": product_tuple[16],
                                    "owner_id": product_tuple[8],
                                    "name": product_tuple[9],
                                    "image": image,
                                    "price": convert_price(product_tuple[11], product_tuple[12], currency),
                                    "currency": currency,
                                    "quantity": product_tuple[13],
                                    "description": product_tuple[14],
                                    "last_pickup": product_tuple[15],
                                    "owner_name": db.get_username(product_tuple[8])
                                })
        return bought_products
        
    
    bought_products = get_bought_products(user_id, db)
    if bought_products is not None:
        return build_http_response(status_code=200, body=prep_json({"message": "Bought products retrieved successfully",
                                                                    "bought_products": bought_products}))
    else:
        return build_http_response(status_code=404, body=prep_json({"message": "Something went wrong"}))
    

def handle_get_most_sold_products(db, product_imgs_dir_name, currency):
    def get_most_sold_products(db, product_imgs_dir_name):
        product_tuples = db.get_most_sold_products(limit=4)
        product_data = []
        for product_tuple in product_tuples:
            product_data.append(format_product_data(product_tuple, product_imgs_dir_name, currency))
            product_data[-1]["total_sales"] = product_tuple[12]
        return product_data
    
    most_sold_products = get_most_sold_products(db, product_imgs_dir_name)
    return build_http_response(status_code=200, body=prep_json(
        {"message": "Most sold products successfully retrieved",
         "most_sold_products": most_sold_products}))