import sqlite3
from passlib.context import CryptContext


class db_accessor:
    """Provides and interface for communicating
    with the database"""
    def __init__(self, db_name="auboutique.db"):
        self.db_name = db_name
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def connect(self):
        """Connect to the database"""
        self.con = sqlite3.connect(self.db_name)
        self.con.execute("PRAGMA foreign_keys=1")

    def close(self):
        """Close connection to the database"""
        self.con.close()


    def add_account(self, account_info):
        """Add an account to the database"""
        cur = self.con.cursor()
        # Hash the password
        hashed_password = self.pwd_context.hash(account_info["password"])

        try:
            # Try adding the user info
            cur.execute("""INSERT INTO user ('name', email, username, hashed_password)
                            VALUES (?, ?, ?, ?)""",
                            (account_info["name"], account_info["email_address"], account_info["username"], hashed_password))
            user_id = cur.lastrowid
            # print(user_id)
            self.con.commit()
            return user_id
        except sqlite3.IntegrityError:
            # Catch errors related to the db schema
            # This is likely an error raised because the username
            # or email is already in use
            return -1
    
    def get_user_id(self, account_credentials):
        """Validate credentails and return user id"""
        cur = self.con.cursor()
        user_record = cur.execute("""SELECT rowid, hashed_password FROM user WHERE username=?""",
                                  (account_credentials["username"],)).fetchone()
        if user_record is None:
            return -1
        user_id, correct_password_hash = user_record
        # Check if passwords match (the password was hashed)
        if self.pwd_context.verify(account_credentials["password"], correct_password_hash):
            return user_id
        else:
            return -1
        

    def get_product(self, product_id):
        """Return the data of the product with id `product_id`"""
        cur = self.con.cursor()
        cur.execute("""SELECT product.*, user.username, AVG(rating.rating) AS avg_rating, COUNT(rating.rating) AS rating_count FROM product LEFT JOIN 'transaction' ON product.rowid='transaction'.product_id
                       JOIN user ON product.owner_id=user.rowid 
                       LEFT JOIN rating ON product.rowid=rating.product_id WHERE product.rowid=? GROUP BY product.rowid""", (product_id,))
        product_data = cur.fetchone()
        return product_data
        

    def get_products(self, owner_id=None):
        """Return a list of all products in the database
        if `owner_id` is provided, retun a list of all products
        belonging to that owner
        """
        cur = self.con.cursor()
        if owner_id is None:
            products = cur.execute("""SELECT product.*, user.username, AVG(rating.rating) AS avg_rating, COUNT(rating.rating) AS rating_count FROM product
                                    LEFT JOIN 'transaction' ON product.rowid='transaction'.product_id
                                    JOIN user ON product.owner_id=user.rowid 
                                    LEFT JOIN rating ON product.rowid=rating.product_id GROUP BY product.rowid;""")
        else:
            products = cur.execute("""SELECT product.*, user.username, AVG(rating.rating) AS avg_rating, COUNT(rating.rating) AS rating_count FROM product
                                    LEFT JOIN 'transaction' ON product.rowid='transaction'.product_id
                                    JOIN user ON product.owner_id=user.rowid
                                    LEFT JOIN rating ON product.rowid=rating.product_id WHERE product.owner_id=? GROUP BY product.rowid""", (owner_id,))


        return products.fetchall()
    
    def add_product_info(self, product_info):
        """Add a product to the databse"""
        cur = self.con.cursor()
        try:
            cur.execute("""INSERT INTO product (owner_id, 'name', price, currency, quantity, 'description')
                           VALUES (?, ?, ?, ?, ?, ?)""",
                           (product_info["user_id"], product_info["name"], product_info["price"], product_info["currency"], product_info["quantity"], product_info["description"]))
        except sqlite3.IntegrityError:
            return -1
        else:
            self.con.commit()
            product_id = cur.lastrowid
            return product_id
    
    def add_product_image_file_name(self, product_id, file_name):
        """Add an image name to a product record"""
        cur = self.con.cursor()
        cur.execute("""UPDATE product SET image_name=? WHERE rowid=?""",
                       (file_name, product_id))
        self.con.commit()

    def get_all_owners(self):
        """Get a list of all users that own at least
        one product"""
        cur = self.con.cursor()
        owners = cur.execute("""SELECT DISTINCT user.rowid, user.username FROM user JOIN product ON user.rowid=product.owner_id""").fetchall()
        return owners

    def get_user_products(self, user_id):
        """Get a list of products owned by a specific user"""
        cur = self.con.cursor()
        products = cur.execute("""SELECT product.*, AVG(rating.rating), COUNT(rating.rating) FROM product
                                    LEFT JOIN rating ON product.rowid=rating.product_id WHERE product.owner_id=? GROUP BY product.rowid""", (user_id,)).fetchall()
        return products

    def get_product_transactions(self, product_id):
        cur = self.con.cursor()
        transactions = cur.execute("""SELECT time_bought, username, 'user'.rowid, pickup_time, quantity FROM 'transaction'
                                   JOIN user ON buyer_id=user.rowid WHERE product_id=?""", (product_id, )).fetchall()
        return transactions

    
    def buy_product(self, transaction_info, pickup_time):
        """Add a record for a user buying a certain product"""
        cur = self.con.cursor()
        # Make sure the item is not already bought
        try:
            cur.execute("SELECT quantity FROM product WHERE rowid=?", (transaction_info["product_id"],))

            cur_quantity = cur.fetchone()
            if cur_quantity is None: return False
            cur_quantity = cur_quantity[0]
            if cur_quantity - transaction_info["quantity"] < 0: return False
            
            cur.execute("""UPDATE 'product' SET quantity=quantity-? WHERE rowid=?""",
                            (transaction_info["quantity"], transaction_info["product_id"]))

            cur.execute("""INSERT INTO 'transaction' (product_id, buyer_id, pickup_time, quantity) VALUES (?, ?, ?, ?)""",
                                (transaction_info["product_id"], transaction_info["user_id"],
                                 pickup_time, transaction_info["quantity"]))
        except sqlite3.IntegrityError:
            return False
        else:
            self.con.commit()
            return True
    def get_product_owner(self, product_id):
        """Get the id of the owner of the product having the id `product_id`"""
        cur = self.con.cursor()
        res = cur.execute("SELECT owner_id FROM product WHERE rowid=?", (product_id,)).fetchone()
        if res is None:
            return None
        return res[0]
    
    def get_username(self, user_id):
        """Get the username of a username through their id"""
        cur = self.con.cursor()
        cur.execute("SELECT username FROM user WHERE rowid=?", (user_id,))
        username = cur.fetchone()
        if username is None: return None
        return username[0]
    
    def get_accepted_requests(self, user_id):
        """Get list of users_ids for users that that `user_id`
        accepted messages from"""
        cur = self.con.cursor()
        cur.execute("SELECT requester_id FROM accepted_request WHERE accepter_id=?", (user_id,))
        res1 = cur.fetchall()
        cur.execute("SELECT requester_id FROM accepted_request WHERE requester_id=?", (user_id,))
        res2 = cur.fetchall()
        return [row[0] for row in res1 + res2]
    
    def add_accepted_request(self, accepter_id, requester_id):
        """Get list of users_ids for users that that `user_id`
        accepted messages from"""
        cur = self.con.cursor()
        try:
            cur.execute("INSERT INTO accepted_request (accepter_id, requester_id) VALUES (?, ?)", (accepter_id, requester_id))
        except sqlite3.IntegrityError:
            return False
        self.con.commit()
        return True
    
    
    def add_rating(self, user_id, product_id, rating):
        cur = self.con.cursor()
        cur.execute("UPDATE rating SET rating=? WHERE user_id=? AND product_id=?", (rating, user_id, product_id))
        if cur.rowcount == 1:
            self.con.commit()
            return True
        
        try:
            cur.execute("INSERT INTO rating (user_id, product_id, rating) VALUES (?, ?, ?)", (user_id, product_id, rating))
        except sqlite3.IntegrityError:
            return False
        else:
            self.con.commit()
            return True
    def get_bought_products(self, user_id):
        cur = self.con.cursor()
        cur.execute("""SELECT *, MAX(pickup_time), SUM('transaction'.quantity) FROM 'transaction'
                    JOIN product on product_id=product.rowid WHERE buyer_id=? GROUP BY product_id""", (user_id,))
        return cur.fetchall()
    def get_most_sold_products(self, limit=4):
        cur = self.con.cursor()
        products = cur.execute("""SELECT product.*, user.username, AVG(rating.rating), COUNT(rating.rating),
                                COALESCE(SUM('transaction'.quantity), 0) AS sold_amount FROM product
                                LEFT JOIN 'transaction' ON product.rowid='transaction'.product_id
                                JOIN user ON product.owner_id=user.rowid 
                                LEFT JOIN rating ON product.rowid=rating.product_id GROUP BY product.rowid
                                ORDER BY sold_amount DESC LIMIT ?;""", (limit,))
        return cur.fetchall()