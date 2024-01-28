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

    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    result = cursor.execute("SELECT link FROM sermons WHERE author=:author AND title=:title", ({"author": author, "title": title}))
    if len(result.fetchall()) > 0:
        print(title + " by " + author + " already in database")
        return
    cursor.execute("INSERT into sermons VALUES(:author, :title, :link)",
                   ({"author": author, "title": title, "link": link}))
    connection.commit()

    file_name_title = clean_file_name(title)
    dir_name_author = clean_file_name(author)
    # remove dash from the front if present
    sermon_path = sermons_path + dir_name_author + "/" + file_name_title + ".txt"
    if not os.path.exists(sermons_path + dir_name_author):
        os.makedirs(sermons_path + dir_name_author)
    if os.path.isfile(sermon_path):
        print(title + " by " + author + " already saved in files")
        return
    sermon_file = open(sermon_path, "w+")
    sermon_file.write(text)
    sermon_file.close()
    
def clean_file_name(file_name):
    new_file_name = ""
    for char in file_name:
        if char.isalnum():
            new_file_name += char.lower()
        if char.isspace():
            new_file_name += '-' # replace spaces with dashes
    # replace multiple dashes with one dash
    new_file_name = re.sub('-+', '-', new_file_name)
    if new_file_name[0] == '-':
        new_file_name = new_file_name[1:]
    return new_file_name

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

def rm_leading_spaces(text):
    search_index = 0
    while text[search_index].isspace():
        search_index += 1
    return text[search_index:]

def check_db():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    result = cursor.execute("SELECT COUNT(*) FROM sermons")
    print(result.fetchall())
    result = cursor.execute("SELECT TOP 10 * FROM sermons")
    print(result.fetchall())
    
####################################################
def main(args):
    """ Main entry point of the app """
    setup_database()
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
