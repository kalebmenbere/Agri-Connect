import mysql.connector

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root"
)

mycursor = mydb.cursor()
mycursor.execute("CREATE DATABASE IF NOT EXISTS agriconnect_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
print("Database created successfully!")
