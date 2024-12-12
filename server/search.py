from rapidfuzz import process, fuzz
import os
import base64
def custom_match(s: str, t: str):
    s = s.lower()
    t = t.lower()
    return max(fuzz.partial_token_ratio(s, t), fuzz.partial_ratio(s, t))
def search_products(db, query, product_imgs_dir_name):
    def get_products(db, product_imgs_dir_name):
        # Get a raw list of all products
        product_tuples = db.get_products()
        product_name_to_info = {}
        # Put the list of products in a convenient format
        for product_tuple in product_tuples:
            product_name = product_tuple[3]
            if product_name not in product_name_to_info: 
                product_name_to_info[product_name] = []
            img_file_path = os.path.join(product_imgs_dir_name, product_tuple[4])
            with open(img_file_path, 'rb') as image_file:
                image = image_file.read()
                image = base64.b64encode(image).decode()

            product_name_to_info[product_name].append({ "id": product_tuple[0],
                                                        "date_time_added": product_tuple[1],
                                                        "owner_id": product_tuple[2],
                                                        "image": image,
                                                        "owner_name": product_tuple[9],
                                                        "name": product_name,
                                                        "price": product_tuple[5],
                                                        "currency": product_tuple[6],
                                                        "quantity": product_tuple[7],
                                                        "available": product_tuple[8] is None,
                                                        "avg_rating": product_tuple[10]})
                
        return product_name_to_info
    products = get_products(db, product_imgs_dir_name)
    product_names = [product_name for product_name in products.keys()]
    results = sorted([(s, custom_match(query, s)) for s in product_names], key=lambda x: x[1], reverse=True)
    close_matches = []
    for product_name, score in results:
        if score < 70: break
        close_matches += products[product_name]
    return close_matches
    


    