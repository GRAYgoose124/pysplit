import re
import ast


def split_file_into_module(filename):
    """Split a file into a module

    Usage:

    Apply # pragma: newfile("filename.py") at each point where you want to split the file.
    The new file will be created with the contents of the file between the previous pragma
    and the current pragma.

    - Imports will be automatically copied to the appropriate files.
    - Top-level functions and classes will be exported in the __all__ variable in the
    __init__.py file.
    """
    split_file(filename)


def extract_exports(lines):
    exports = []
    for line in lines:
        match = re.match(r"^\s*(def|class)\s+(\w+)", line)
        if match:
            exports.append(match.group(2))
    return exports


def parse_imports(line):
    tree = ast.parse(line)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                yield alias.name


def parse_possible_import_references(lines):
    tree = ast.parse("".join(lines))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            yield node.id


def parse_body_for_used_imports(lines, imports):
    """Parse the body of a file to find which imports are actually referenced"""
    used_imports = set()
    for name in parse_possible_import_references(lines):
        if name in imports:
            used_imports.add(name)
    return used_imports


def split_file(filename):
    with open(filename, "r") as file:
        lines = file.readlines()

    current_file = None
    file_contents = {}
    all_exports = {}
    imports = {}

    for line in lines:
        # track imports
        if line.startswith("import ") or line.startswith("from "):
            for name in parse_imports(line):
                imports[name] = line
            continue

        # each file starts with a pragma that delineates the new file
        pragma_match = re.match(r'# pragma: newfile\("(.+)"\)', line)
        if pragma_match:
            if current_file:
                all_exports[current_file] = extract_exports(file_contents[current_file])
            current_file = pragma_match.group(1)
            file_contents[current_file] = []
        # append to the current file
        elif current_file:
            file_contents[current_file].append(line)

    if current_file:
        all_exports[current_file] = extract_exports(file_contents[current_file])

    for new_filename, contents in file_contents.items():
        exports = all_exports[new_filename]
        used_imports = parse_body_for_used_imports(contents, imports)
        print(
            f"Creating {new_filename} with exports {exports} and imports {used_imports}"
        )
        with open(new_filename, "w") as new_file:
            for name in used_imports:
                if name in imports:
                    new_file.write(imports[name])
            if exports:
                new_file.write(f"__all__ = {exports}\n")
            new_file.writelines(contents)

    # Update the original file to re-export symbols
    with open("__init__.py", "w") as file:
        for new_filename, exports in all_exports.items():
            if exports:
                module_name = re.sub(r"\.py$", "", new_filename)
                file.write(f"from {module_name} import *\n")
        file.write(f"\n__all__ = {[x for y in all_exports.values() for x in y]}")

    return list(file_contents.keys())
