CREATE TABLE user (
    rowid INTEGER PRIMARY KEY,
    'name' VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL   
);
CREATE TABLE accepted_request (
    accepter_id INT NOT NULL,
    requester_id INT NOT NULL,
    FOREIGN KEY (accepter_id) REFERENCES user(rowid),
    FOREIGN KEY (requester_id) REFERENCES user(rowid),
    PRIMARY KEY (accepter_id, requester_id)
);
CREATE TABLE product (
    rowid INTEGER PRIMARY KEY,
    time_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    owner_id INT,
    'name' VARCHAR(50) NOT NULL,
    image_name VARCHAR(100) UNIQUE,
    price INT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    quantity INT NOT NULL,
    'description' VARCHAR(200) NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user(rowid)
);

CREATE TABLE 'transaction' (
    rowid INTEGER PRIMARY KEY,
    time_bought DATETIME DEFAULT CURRENT_TIMESTAMP,
    product_id INT,
    buyer_id INT,
    pickup_time DATETIME NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES product(rowid),
    FOREIGN KEY (buyer_id) REFERENCES user(rowid)
);

CREATE TABLE rating (
    product_id INT,
    user_id INT,
    rating INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES product(rowid),
    FOREIGN KEY (user_id) REFERENCES user(rowid),
	CONSTRAINT rating_val CHECK (rating IN (1, 2, 3, 4, 5)),
	UNIQUE(user_id, product_id)
);