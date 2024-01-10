#!/usr/bin/env python3
# sermon_scrape.py scrapes sermons from spurgeon.org

import mechanicalsoup
import sqlite3
import os.path
import time
import argparse
import re

database_path = 'sermon_data.db'
sermons_path = 'sermons/'
time_between_calls = 0.03

def setup_database():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    result = cursor.execute("SELECT name from sqlite_master")
    table_names = result.fetchall()
    if len(table_names) == 0 or table_names[0][0] != 'sermons':
        cursor.execute("CREATE table sermons(author, title, link)")
        connection.commit()
        print("Created the sermons table with author, title and link columns")

def add_sermon(title, author, link, text):
    # test this function by posting fake data. 
    if not title:
        print("No title given")
        exit()
    elif not author:
        print("No author given")
        exit()
    elif not link:
        print("No link given")
        exit()
    elif not text:
        print("No sermon text given")
        exit()
    # ensure no bad sql characters will get in

    # add author, title, link to db
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    result = cursor.execute("SELECT link FROM sermons WHERE author=:author AND title=:title", ({"author": author, "title": title}))
    if len(result.fetchall()) > 0:
        print(title + " by " + author + " already in database")
        exit()
    cursor.execute("INSERT into sermons VALUES(:author, :title, :link)", ({"author": author, "title": title, "link": link}))
    connection.commit()
    # save text in file using author, title, text
    file_name_title = title.replace(" ","").lower()
    dir_name_author = author.replace(" ","").lower()
    sermon_path = sermons_path + dir_name_author + "/" + file_name_title + ".txt"
    if not os.path.exists(sermons_path + dir_name_author):
        os.makedirs(sermons_path + dir_name_author)
    if os.path.isfile(sermon_path):
        print(title + " by " + author + " already saved in files")
        exit()
    sermon_file = open(sermon_path, "w+")
    sermon_file.write(text)
    sermon_file.close()

def get_spurgeon_sermons():
    browser = mechanicalsoup.StatefulBrowser()
    browser.set_user_agent('the_lords_bot')
    url = "https://www.spurgeon.org/resource-library/sermons/?fwp_paged="
    author = 'spurgeon'
    page_number = 0
    num_pages = 313
    links = []
    while page_number < num_pages:
        page_number += 1
        time.sleep(time_between_calls)
        page = browser.get(url + str(page_number))
        sermon_tags = page.soup.find_all(class_='latest-resources__row__single')
        for tag in sermon_tags:
            if tag.div and tag.div.a:
                links.append(tag.div.a["href"])

    for sermon_link in links:
        time.sleep(time_between_calls)
        sermon_page = browser.get(sermon_link)
        article = sermon_page.soup.find_all(class_='article__body__content')
        if len(article) != 1:
            print("Number of articles found at " + sermon_link + " is " + str(len(article)))
            return
        article = article[0]
        sermon_title = article.h2.string
        article.h2.decompose()
        sermon_text = article.get_text()
        sermon_text = rm_leading_spaces(sermon_text)
        add_sermon(sermon_title, author, sermon_link, sermon_text)

def check_db():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    result = cursor.execute("SELECT * FROM sermons") 
    print(result.fetchall())

def test_add_sermon():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    test_author = 'John Tucker'
    test_name = 'God is Good'
    test_text = "This is a test sermon"
    test_link = 'sermons.com/jt'
    add_sermon(test_name, test_author, test_link, test_text)
    result = cursor.execute("SELECT link FROM sermons WHERE author=:author AND title=:title", ({"author": test_author, "title": test_name}))
    record = result.fetchall()
    if len(record) != 1:
        print("Rows returned in query for the add_sermon test: " + str(len(record)))
        print(record)
    else:
        record = record[0][0]
        print("Record for the positive add_sermon test: " + record)
        if record != test_link:
            print("test failed. stored link is " + record)
            return
        f = open('sermons/john_tucker/god_is_good.txt', "r")
        if f and f.read() == test_text:
            print("Test passed")
        elif not f:
            print("No sermon file found")
        else:
            print("Test failed with the following written to file:\n" + f.read())

def delete_db_records():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    cursor.execute("DELETE from sermons")
    connection.commit()

def delete_test_file():
    test_file_path = 'sermons/john_tucker/god_is_good'
    if os.path.exists(test_file_path):
        os.rmdir("sermons/john_tucker")

def rm_leading_spaces(text):
    search_index = 0
    while text[search_index].isspace():
        search_index += 1
    return text[search_index:]
    
####################################################
def main(args):
    """ Main entry point of the app """
    setup_database()
    # if arg test, tst then delete then quit 
    if args.test:
        test_add_sermon()
        delete_db_records()
        delete_test_file()
        exit()
    if args.other:
        exit()
    get_spurgeon_sermons()
    check_db()

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", default=False)
    parser.add_argument("--other", action="store_true", default=False)
    args = parser.parse_args()
    main(args)
