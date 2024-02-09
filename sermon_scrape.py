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
    with connection:
        connection.execute("CREATE TABLE IF NOT EXISTS sermons(author, title, link)")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS sermon_index ON sermons(author, title, link)")
    connection.close()

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

    file_name_title = clean_file_name(title)
    dir_name_author = clean_file_name(author)
    sermon_path = sermons_path + dir_name_author + "/" + file_name_title + ".txt"
    if os.path.isfile(sermon_path):
        print(title + " by " + author + " already saved in files")
        return

    connection = sqlite3.connect(database_path)
    try:
        with connection:
            connection.execute("INSERT into sermons VALUES(:author, :title, :link)",
                               ({"author": author, "title": title, "link": link}))
    except sqlite3.IntegrityError:
        print(title + " by " + author + " probably already in database")
    connection.close()

    if not os.path.exists(sermons_path + dir_name_author):
        os.makedirs(sermons_path + dir_name_author)
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
    new_file_name = re.sub('-+', '-', new_file_name)
    if new_file_name[0] == '-':
        new_file_name = new_file_name[1:]
    if new_file_name[-1] == '-':
        new_file_name = new_file_name[:-1]
    return new_file_name

def get_spurgeon_sermons():
    browser = mechanicalsoup.StatefulBrowser()
    browser.set_user_agent('the_lords_bot')
    url = "https://www.spurgeon.org/resource-library/sermons/?fwp_paged="
    author = 'spurgeon'
    page_number = 0
    num_pages = 313
    links = []
    link_names = []
    while page_number < num_pages:
        page_number += 1
        time.sleep(time_between_calls)
        page = browser.get(url + str(page_number))
        sermon_tags = page.soup.find_all(class_='latest-resources__row__single__inner__content')
        for tag in sermon_tags:
            if tag.h2 and tag.h2.a:
                links.append(tag.h2.a["href"])
                link_names.append(tag.h2.a.string.replace(u'\xa0', u' '))
    print("Number of links found: " + str(len(links)))

    for i, sermon_link in enumerate(links):
        time.sleep(time_between_calls)
        sermon_page = browser.get(sermon_link)
        article = sermon_page.soup.find_all(class_='article__body__content')
        if len(article) != 1:
            print("Number of articles found at " + sermon_link + " is " + str(len(article)))
            continue
        article = article[0]
        if article.h2:
            article.h2.decompose()
        try:
            sermon_text = article.get_text().replace(u'\xa0', u' ')
            sermon_title = link_names[i]
            sermon_text = rm_leading_spaces(sermon_text)
            add_sermon(sermon_title, author, sermon_link, sermon_text)
        except:
            print("Error with sermon at " + sermon_link)
            continue

def rm_leading_spaces(text):
    search_index = 0
    while text[search_index].isspace():
        search_index += 1
    return text[search_index:]

def clean_db():
    connection = sqlite3.connect(database_path)
    with connection:
        result = connection.execute("SELECT * FROM sermons")
        for row in result.fetchall():
            title = row[1]
            author = row[0]
            file_name_title = clean_file_name(title)
            dir_name_author = clean_file_name(author)
            sermon_path = sermons_path + dir_name_author + "/" + file_name_title + ".txt"
            if not os.path.isfile(sermon_path):
                print("File " + sermon_path + " not found")
                connection.execute("DELETE FROM sermons WHERE author = :author AND title = :title",
                                   ({"author": author, "title": title}))

def check_db():
    connection = sqlite3.connect(database_path)
    with connection:
        result = connection.execute("SELECT COUNT(*) FROM sermons")
        print("Number of sermons in database: " + str(result.fetchone()[0]))
        result = connection.execute("SELECT * FROM sermons LIMIT 10")
        print('\n'.join(map(str, result.fetchall())))
    connection.close()
    
####################################################
def main(args):
    """ Main entry point of the app """
    setup_database()
    if args.other:
        exit()
    elif args.status:
        pass
    elif args.clean_db:
        clean_db()
    else:
        get_spurgeon_sermons()
    check_db()

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", default=False)
    parser.add_argument("--status", action="store_true", default=False)
    parser.add_argument("--other", action="store_true", default=False)
    parser.add_argument("--clean_db", action="store_true", default=False)
    args = parser.parse_args()
    main(args)
