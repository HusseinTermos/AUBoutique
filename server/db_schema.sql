DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS 'transaction';

CREATE TABLE user (
    rowid INTEGER PRIMARY KEY,
    'name' VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL   
);

CREATE TABLE product (
    rowid INTEGER PRIMARY KEY,
    time_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    owner_id INT,
    'name' VARCHAR(50) NOT NULL,
    image_name VARCHAR(100) UNIQUE,
    price INT NOT NULL,
    'description' VARCHAR(200) NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES user(rowid)
);

CREATE TABLE 'transaction' (
    rowid INTEGER PRIMARY KEY,
    time_bought DATETIME DEFAULT CURRENT_TIMESTAMP,
    product_id INT UNIQUE,
    buyer_id INT,
    pickup_time DATETIME NOT NULL,
    FOREIGN KEY (product_id) REFERENCES product(rowid),
    FOREIGN KEY (buyer_id) REFERENCES user(rowid)
);

