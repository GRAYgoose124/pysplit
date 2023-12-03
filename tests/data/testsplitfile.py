import os
import sys
import sqlite3
import requests


# This will be included with the main file, if you want to ensure that
# it is exported as part of the library, add a newfile pragma before any
# code you want to export via __all__.
class UtilityClass:
    def method_one(self):
        return "Method one of UtilityClass"


def this_exe():
    return os.path.dirname(sys.executable)


# pragma: newfile("database.py")
class DatabaseConnector:
    def connect(self):
        return sqlite3.connect("database.db")


def query_database(query):
    connection = DatabaseConnector().connect()
    cursor = connection.cursor()
    cursor.execute(query)


# pragma: newfile("network.py")
class NetworkRequester:
    def fetch(self, url):
        return requests.get(url)


def send_request(url):
    return f"Request sent to {url}"


# pragma: newfile("math_operations.py")
class MathOperations:
    def add(self, a, b):
        return a + b


def subtract(a, b):
    return a - b


if __name__ == "__main__":
    print("This is the main file.")
    MO = MathOperations()
    print(MO.add(1, 2))
    print(subtract(1, 2))
    print(send_request("http://example.com"))
    print(this_exe())
