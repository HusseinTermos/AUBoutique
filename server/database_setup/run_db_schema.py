import sqlite3

con = sqlite3.connect("auboutique.db")
cur = con.cursor()
x = open("server\\db_schema.sql").read().split(';')

for l in x: cur.execute(l)
con.commit()
con.close()
