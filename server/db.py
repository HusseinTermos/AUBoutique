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
        

    def get_products(self, owner_id=None):
        """Return a list of all products in the database
        if `owner_id` is provided, retun a list of all products
        belonging to that owner
        """
        cur = self.con.cursor()
        if owner_id is None:
            products = cur.execute("""SELECT product.*, 'transaction'.buyer_id, user.name FROM product LEFT JOIN 'transaction' ON product.rowid='transaction'.product_id
                                      JOIN user ON product.owner_id=user.rowid""")
        else:
            products = cur.execute("""SELECT product.*, 'transaction'.buyer_id, user.name FROM product LEFT JOIN 'transaction' ON product.rowid='transaction'.product_id
                                      JOIN user ON product.owner_id=user.rowid WHERE product.owner_id=?""", (owner_id,))


        return products.fetchall()
    
    def add_product_info(self, product_info):
        """Add a product to the databse"""
        cur = self.con.cursor()
        try:
            cur.execute("""INSERT INTO product (owner_id, 'name', price, 'description')
                           VALUES (?, ?, ?, ?)""",
                           (product_info["user_id"], product_info["name"], product_info["price"], product_info["description"]))
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
        products = cur.execute("""SELECT product.*, user.username, 'transaction'.time_bought FROM product LEFT JOIN 'transaction' ON product.rowid='transaction'.product_id
                                    LEFT JOIN user ON 'transaction'.buyer_id=user.rowid WHERE product.owner_id=?""", (user_id,)).fetchall()
        return products

    
    def buy_product(self, transaction_info, pickup_time):
        """Add a record for a user buying a certain product"""
        cur = self.con.cursor()
        # Make sure the item is not already bought
        try:
            cur.execute("""INSERT INTO 'transaction' (product_id, buyer_id, pickup_time) VALUES (?, ?, ?)""",
                                (transaction_info["product_id"], transaction_info["user_id"], pickup_time))

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
        username = cur.fetchone()[0]
        if username is None: return None
        return username
    
        
