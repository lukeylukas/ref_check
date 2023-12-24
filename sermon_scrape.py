#!/usr/bin/env python3
# sermon_scrape.py scrapes sermons from spurgeon.org

import mechanicalsoup
import sqlite3
import os.path

database_path = 'sermon_data.db'
sermons_path = 'sermons/'

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
    elif title.find(" ") != -1 or title.lower() != title:
        print(title + " by " + author + " title not formatted for saving")
        exit()
    elif author.find(" ") != -1 or author.lower() != author:
        print(title + " by " + author + " author not formatted for saving")
        exit()
    # add author, title, link to db
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    result = cursor.execute("SELECT link FROM sermons WHERE author like ':author' AND title like ':title'", ({"author": author, "title": title}))
    if len(result.fetchall()) > 0:
        print(title + " by " + author + " already in database")
        exit()
    cursor.execute("INSERT into sermons VALUES(:author, :title, :link)", ({"author": author, "title": title, "link": link}))
    connection.commit()
    # save text in file using author, title, text
    sermon_path = sermons_path + author + "/" + title + ".txt"
    if not os.path.exists(sermons_path + author):
        os.makedirs(sermons_path + author)
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
    page_number = 0
    num_pages = 1
    links = []
    while page_number < num_pages:
        page_number += 1
        page = browser.get(url + str(page_number))
        sermon_tags = page.soup.find_all(class_='latest-resources__row__single')
        for tag in sermon_tags:
            if tag.div and tag.div.a:
                links.append(tag.div.a["href"])

    for sermon_link in links:
        sermon_page = browser.get(sermon_link)
        article = sermon_page.soup.find_all(class_='article__body__content')
        if len(article) != 1:
            print("Number of articles found at " + sermon_link + " is " + str(len(article)))
            exit()
        article = article[0]
        sermon_title = article["h2"].string.replace(' ', '_').lower()
        sermon_text = article.get_text()
        add_sermon(sermon_title, author, sermon_link, sermon_text)
        exit() #DELETE

def test_add_sermon():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    #print("Testing bad title")
    #add_sermon("God is Good", "John Tucker", "sermons.com/jt", "This is a test sermon")
    #result = cursor.execute("SELECT link FROM sermons WHERE author like '%?%' AND title like '%?%'", [author, title])
    #record = result.fetchall()
    #if record is None:
    #    print("Negative Title test passed")
    #else:
    #    print("Record inserted when it shouldn't be: " + record)
#
    add_sermon("god_is_good", "john_tucker", "sermons.com/jt", "This is a test sermon")
    result = cursor.execute("SELECT link FROM sermons WHERE author like ':author' AND title like ':title'", ({"author": "john_tucker", "title": "god_is_good"}))
    record = result.fetchall()
    if len(record) == 0:
        print("No record in db for the add_sermon test")
    else:
        print("Record for the positive add_sermon test: " + record[0])

def delete_db_records():
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()
    cursor.execute("DELETE from sermons")
    connection.commit()
    
####################################################
def main():
    """ Main entry point of the app """
    setup_database()
    get_spurgeon_sermons()

if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
