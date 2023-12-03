import re
import ast


def detect_main_block(lines):
    """Detect the main block of code in a file, whether it's in a function or if statement.

    Then return the whole block, including the if statement or def main .
    """
    main_block = []
    in_main_block = False
    for line in lines:
        if in_main_block:
            main_block.append(line)
        elif re.match(r"if __name__ == \"__main__\":", line):
            in_main_block = True
            main_block.append(line)
        elif re.match(r"def main\(\):", line):
            in_main_block = True
            main_block.append(line)
    if main_block:
        return main_block


def extract_exports(lines):
    return [
        match.group(2)
        for line in lines
        if (match := re.match(r"^(def|class)\s+(\w+)", line))
    ]


def parse_imports(line):
    tree = ast.parse(line)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                yield alias.name


def parse_body_for_used_ports(lines, ports):
    tree = ast.parse("".join(lines))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id in ports:
                yield node.id


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
    with open(filename, "r") as file:
        lines = file.readlines()

    exports, imports = {}, {}
    file_contents, up_to_first_pragma = {}, []
    current_file = None
    newlines = 0

    for line in lines:
        if line == "\n":
            newlines += 1
            if newlines > 1:
                continue
        else:
            newlines = 0

        # track imports
        if line.startswith("import ") or line.startswith("from "):
            for name in parse_imports(line):
                imports[name] = line
            continue

        # each file starts with a pragma that delineates the new file
        pragma_match = re.match(r'# pragma: newfile\("(.+)"\)', line)
        if pragma_match:
            if current_file:
                exports[current_file] = extract_exports(file_contents[current_file])

            current_file = pragma_match.group(1)
            file_contents[current_file] = []
        # append to the current file
        elif current_file:
            file_contents[current_file].append(line)
        else:
            # this is the main block
            up_to_first_pragma.append(line)

    # extract exports
    if current_file:
        exports[current_file] = extract_exports(file_contents[current_file])

    # create the new files
    for new_filename, contents in file_contents.items():
        used_exports = exports[new_filename]
        used_imports = parse_body_for_used_ports(contents, imports)

        with open(new_filename, "w") as new_file:
            for name in used_imports:
                if name in imports:
                    new_file.write(imports[name])
            if used_exports:
                new_file.write(f"\n__all__ = {used_exports}\n\n\n")
            new_file.writelines(contents)
    created_filenames = list(file_contents.keys())

    # Update the __init__ file to re-export symbols from the new module directory like the old file.
    with open("__init__.py", "w") as file:
        for new_filename, used_exports in exports.items():
            if used_exports:
                module_name = re.sub(r"\.py$", "", new_filename)
                file.write(f"from .{module_name} import *\n")

        file.write(f"\n__all__ = {[x for y in exports.values() for x in y]}\n")
    created_filenames.append("__init__.py")

    # Detect the main block and create a __main__.py file with the appropriate module imports
    up_to_first_pragma = [
        line
        for line in up_to_first_pragma
        if not (line.startswith("import ") or line.startswith("from "))
    ]
    main_block = up_to_first_pragma + detect_main_block(lines)
    if main_block is not None:
        with open("__main__.py", "w") as main_file:
            # Add necessary imports
            used_imports = parse_body_for_used_ports(up_to_first_pragma, imports)
            for name in used_imports:
                main_file.write(imports[name])
            main_file.write("\n")

            # Add necessary exports from the __init__.py file
            used_exports = parse_body_for_used_ports(
                main_block, [x for y in exports.values() for x in y]
            )
            for name in used_exports:
                main_file.write(f"from . import {name}\n")

            # Add the main block or call main()
            main_file.write("\n\n" + "".join(main_block))
        created_filenames.append("__main__.py")

    return created_filenames
