
# PySplit

PySplit is your friendly neighborhood Python file splitter! It takes a hefty Python file and splits it into a neat module with smaller, manageable files. It's not too stupid, either!  It figures out which imports are needed in each new file and keeps them intact. If a main function or standard main block is detected, it's moved the new module main at `__main__.py`.

# Installation
Clone the repository and let Poetry do its magic:

```bash 
git clone https://github.com/GRAYgoose124/pysplit.git 
cd pysplit 
poetry install 
```

# Usage
Unleash PySplit on your Python file with a simple command:

```bash 
poetry shell
pysplit your_python_file.py
```

Watch as your file is transformed into a tidy module with smaller files. This new directory module can be imported or ran similarly to the original file!

# Testing
Run the tests with the unittest module:

```bash 
poetry run python -m unittest discover tests 
```

# License
PySplit is released under the MIT license.
