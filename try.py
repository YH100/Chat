import sqlite3

with sqlite3.connect("project2018.db") as conn:
    sql = "SELECT * FROM reg_users;"
    f = conn.execute(sql)
    print f.fetchall()