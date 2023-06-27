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
            cursor.execute('DROP TABLE IF EXISTS api_key;')

            # Create tables
            sql = 'CREATE TABLE `book` (' \
                  '`id` INT AUTO_INCREMENT PRIMARY KEY, ' \
                  '`cover_url` VARCHAR(255),' \
                  '`title` VARCHAR(255) NOT NULL, ' \
                  '`author` VARCHAR(255) NOT NULL, ' \
                  '`publication_year` INT NOT NULL, ' \
                  '`main_genre` VARCHAR(255) NOT NULL,' \
                  '`description` TEXT NOT NULL, ' \
                  '`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'
            cursor.execute(sql)

            sql = 'CREATE TABLE `api_key` (' \
                  '`id_api` INT AUTO_INCREMENT PRIMARY KEY,' \
                  '`email` VARCHAR(255) NOT NULL UNIQUE ,' \
                  '`api_key` VARCHAR(64) NOT NULL,' \
                  '`requests_count` INT,' \
                  '`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'
            cursor.execute(sql)

            # Insert data
            default_cover = os.getenv('DEFAULT_COVER_IMG')
            sql = "INSERT INTO `book`(`cover_url`, `title`, `author`, `publication_year`, `main_genre`, " \
                  "`description`) VALUES " \
                  f"('{default_cover}', 'Book 1', 'Author of Book 1', 2020, 'Fiction', 'Description of Book 1')," \
                  f"('{default_cover}', 'Book 2', 'Author of Book 2', 2015, 'Mystery', 'Description of Book 2')," \
                  f"('{default_cover}', 'Book 3', 'Author of Book 3', 2018, 'Science Fiction', 'Description of Book 3')," \
                  f"('{default_cover}', 'Book 4', 'Author of Book 4', 2012, 'Fantasy', 'Description of Book 4')," \
                  f"('{default_cover}', 'Book 5', 'Author of Book 5', 2017, 'Thriller', 'Description of Book 5')," \
                  f"('{default_cover}', 'Book 6', 'Author of Book 6', 2020, 'Romance', 'Description of Book 6')," \
                  f"('{default_cover}', 'Book 7', 'Author of Book 7', 2003, 'Historical Fiction', 'Description of Book 7')," \
                  f"('{default_cover}', 'Book 8', 'Author of Book 8', 2021, 'Mystery', 'Description of Book 8')," \
                  f"('{default_cover}', 'Book 9', 'Author of Book 9', 2014, 'Fantasy', 'Description of Book 9')," \
                  f"('{default_cover}', 'Book 10', 'Author of Book 10', 2022, 'Science Fiction', 'Description of Book 10');"
            cursor.execute(sql)

            # Save changes to the database
            connection.commit()

            # cursor.execute("SELECT * FROM book;")
            # result = cursor.fetchall()
            # print(result)
