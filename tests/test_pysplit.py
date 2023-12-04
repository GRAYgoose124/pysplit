import unittest
from pathlib import Path
import os, tempfile, shutil
from monosplit import split_file_into_module


class TestSplitFileIntoModule(unittest.TestCase):
    def test_split_file_into_module(self):
        path = Path(__file__).parent / "data/testsplitfile.py"
        with tempfile.TemporaryDirectory() as tmpdirname:
            shutil.copy(path, tmpdirname)
            os.chdir(tmpdirname)
            split_file_into_module("testsplitfile.py")
            os.remove("testsplitfile.py")

            for file in os.listdir():
                with open(file, "r") as f:
                    print(f"Contents of {file}")
                    print(f.read())

            self.assertTrue(os.path.exists("__init__.py"))
            self.assertTrue(os.path.exists("__main__.py"))
            self.assertTrue(os.path.exists("database.py"))
            self.assertTrue(os.path.exists("network.py"))
            self.assertTrue(os.path.exists("math_operations.py"))
