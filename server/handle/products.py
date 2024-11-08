from formatting import *
import base64
from datetime import datetime, timedelta
import os
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




def handle_get_products(db, product_imgs_dir_name, owner_id=None):
    """Provide a list of all products and their data"""
    def get_products(db, owner_id):
        # Get a raw list of all products
        product_tuples = db.get_products(owner_id)
        product_jsons = []
        # Put the list of products in a convenient format
        for product_tuple in product_tuples:
            img_file_path = os.path.join(product_imgs_dir_name, product_tuple[4])
            with open(img_file_path, 'rb') as image_file:
                image = image_file.read()
                image = base64.b64encode(image).decode()
            product_jsons.append({"id": product_tuple[0],
                                    "date_time_added": product_tuple[1],
                                    "owner_id": product_tuple[2],
                                    "owner_name": product_tuple[8],
                                    "name": product_tuple[3],
                                    "image": image,
                                    "price": product_tuple[5],
                                    "description": product_tuple[6],
                                    "available": product_tuple[7] is None})
                
        return product_jsons
    products = get_products(db, owner_id)
    return build_http_response(status_code=200,
                                body=prep_json({"message": "Products sent successfully.", "products": products}))


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

def handle_get_user_products(db, product_imgs_dir_name, user_id):
    """Returns a list of products for sale by a specific user"""
    def get_products(db, product_imgs_dir_name, user_id):
        # Get all products of the user
        product_tuples = db.get_user_products(user_id)
        product_jsons = []
        for product_tuple in product_tuples:
            # Read image data of the product
            img_file_path = os.path.join(product_imgs_dir_name, product_tuple[4])
            with open(img_file_path, 'rb') as image_file:
                image = image_file.read()
                image = base64.b64encode(image).decode()
            # Put data in a convenient format
            product_jsons.append({"id": product_tuple[0],
                                    "date_time_added": product_tuple[1],
                                    "name": product_tuple[3],
                                    "image": image,
                                    "price": product_tuple[5],
                                    "description": product_tuple[6],
                                    "buyer_name": product_tuple[7],
                                    "date_time_bought": product_tuple[8]})
                
        return product_jsons
    user_products =  build_http_response(status_code=200,
                               body=prep_json({"message": "user products collected successfully.",
                                               "products": get_products(db, product_imgs_dir_name, user_id)}))
    return user_products

def handle_buy_product(request, db):
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

