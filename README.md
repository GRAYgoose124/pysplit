
# monosplit

monosplit is your friendly neighborhood Python file splitter! It takes a hefty Python file and splits it into a neat module with smaller, manageable files. It's not too stupid, either!  It figures out which imports are needed in each new file and keeps them intact. If a main function or standard main block is detected, it's moved the new module main at `__main__.py`.

# Installation
monosplit is available on PyPI! Install it with pip:

```bash
pip install monosplit
```

```bash 
git clone https://github.com/GRAYgoose124/pysplit.git 
pip install [-e] monosplit 
```

# Usage
Add some `# pragma newfile("name")` statements to the file you want to split and run:
```bash 
monosplit your_python_file.py
```

Watch as your file is transformed into a tidy module with smaller files. This new directory module can be imported or ran similarly to the original file!

# Testing
Run the tests with the unittest module:

```bash 
python -m unittest discover tests 
```

# License
PySplit is released under the MIT license.
