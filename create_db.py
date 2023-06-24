import pymysql.cursors
import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv('.env')
    # Connect to the database
    connection = pymysql.connect(host=os.getenv('HOST'),
                                 user=os.getenv('USER'),
                                 password=os.getenv('PASSWORD'),
                                 database=os.getenv('DATABASE'),
                                 cursorclass=pymysql.cursors.DictCursor)

    with connection:
        with connection.cursor() as cursor:
            # sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
            cursor.execute('DROP TABLE IF EXISTS book;')
            # Create tables
            sql = 'CREATE TABLE `book` (' \
                  '`id` INT AUTO_INCREMENT PRIMARY KEY, ' \
                  '`title` VARCHAR(255) NOT NULL, ' \
                  '`id_author` INT NOT NULL, ' \
                  '`publication_year` INT NOT NULL, ' \
                  '`main_genre` VARCHAR(255) NOT NULL,' \
                  '`description` VARCHAR(255) NOT NULL, ' \
                  '`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'
            cursor.execute(sql)

            # Insert data
            sql = "INSERT INTO `book`(`title`, `id_author`, `publication_year`, `main_genre`, `description`) VALUES " \
                  "('Book 1', 1, 2020, 'Fiction', 'Description of Book 1')," \
                  "('Book 2', 2, 2015, 'Mystery', 'Description of Book 2')," \
                  "('Book 3', 3, 2018, 'Science Fiction', 'Description of Book 3')," \
                  "('Book 4', 4, 2012, 'Fantasy', 'Description of Book 4')," \
                  "('Book 5', 5, 2017, 'Thriller', 'Description of Book 5')," \
                  "('Book 6', 1, 2019, 'Romance', 'Description of Book 6')," \
                  "('Book 7', 3, 2016, 'Historical Fiction', 'Description of Book 7')," \
                  "('Book 8', 2, 2021, 'Mystery', 'Description of Book 8')," \
                  "('Book 9', 4, 2014, 'Fantasy', 'Description of Book 9')," \
                  "('Book 10', 5, 2022, 'Science Fiction', 'Description of Book 10');"
            cursor.execute(sql)

            # Save changes to the database
            connection.commit()

            # cursor.execute("SELECT * FROM book;")
            # result = cursor.fetchall()
            # print(result)
