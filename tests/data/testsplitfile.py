import os
import sys
import sqlite3
import requests


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
