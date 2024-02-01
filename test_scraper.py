#!/usr/bin/env python3
# tests the scraper module

import sqlite3
import os.path
import argparse
import sermon_scrape

def test_add_normal_sermon():
    sermon_scrape.setup_database()
    connection = sqlite3.connect(sermon_scrape.database_path)
    test_author = 'John Tucker'
    test_name = 'God is Good'
    test_text = "This is a test sermon"
    test_link = 'sermons.com/jt'
    result_author = 'john-tucker'
    result_name = 'god-is-good'
    print("Add Sermon Test")
    sermon_scrape.add_sermon(test_name, test_author, test_link, test_text)

    with connection:
        result = connection.execute("SELECT link FROM sermons WHERE author=:author AND title=:title", ({"author": test_author, "title": test_name}))
    record = result.fetchall()
    if len(record) != 1:
        print("Test failed.")
        print("Rows returned in query: " + str(len(record)))
        print(record)
    else:
        record = record[0][0]
        # print("Record: " + record)
        if record != test_link:
            print("Test failed. Stored link is " + record)
        else:
            f = open('sermons/' + result_author + '/' + result_name + '.txt', "r")
            if f and f.read() == test_text:
                print("Test passed")
            elif not f:
                print("Test failed. No sermon file found")
            else:
                print("Test failed with the following written to file:\n" + f.read())

    delete_db_records()
    delete_test_file(result_author, result_name)

def test_add_weird_sermon_name():
    sermon_scrape.setup_database()
    connection = sqlite3.connect(sermon_scrape.database_path)
    test_author = 'John T--''&3#$..      uck""er'
    test_name = 'God is Good2Me'
    test_text = "This is a test sermon"
    test_link = 'sermons.com/jt'
    result_author = 'john-t3-ucker'
    result_name = 'god-is-good2me'
    print("Add Weird Sermon Folder Name Test")
    sermon_scrape.add_sermon(test_name, test_author, test_link, test_text)
    with connection:
        result = connection.execute("SELECT link FROM sermons WHERE author=:author AND title=:title", ({"author": test_author, "title": test_name}))
    record = result.fetchall()
    if len(record) != 1:
        print("Test failed.")
        print("Rows returned in query: " + str(len(record)))
        print(record)
    else:
        record = record[0][0]
        # print("Record: " + record)
        if record != test_link:
            print("Test failed. Stored link is " + record)
        else:
            f = open('sermons/' + result_author + '/' + result_name + '.txt', "r")
            if f and f.read() == test_text:
                print("Test passed")
            elif not f:
                print("Test failed. No sermon file found")
            else:
                print("Test failed with the following written to file:\n" + f.read())

    delete_db_records()
    delete_test_file(result_author, result_name)

def delete_db_records():
    connection = sqlite3.connect(sermon_scrape.database_path)
    with connection:
        connection.execute("DROP TABLE IF EXISTS sermons")
    connection.commit()

def delete_test_file(author, title):
    for root, dirs, files in os.walk('sermons/' + author):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
    
####################################################
def main(args):
    """ Main entry point of the app """
    sermon_scrape.setup_database()
    test_add_normal_sermon()
    test_add_weird_sermon_name()
    exit()

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)
