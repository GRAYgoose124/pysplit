import re
import ast
import logging

log = logging.getLogger(__name__)


def detect_main_block(tree, source) -> list[str]:
    """
    Detect the main block of code in a source string, whether it's in a function or if statement.
    Then return the whole block, including the if statement or def main.
    """

    class MainBlockVisitor(ast.NodeVisitor):
        def __init__(self):
            self.main_block = None
            self.start_lineno = None
            self.end_lineno = None

        def visit_If(self, node):
            # Check if the node is 'if __name__ == "__main__":'
            if (
                isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "__name__"
                and isinstance(node.test.comparators[0], ast.Str)
                and node.test.comparators[0].s == "__main__"
            ):
                self.start_lineno = node.lineno
                self.end_lineno = node.end_lineno
                self.main_block = ast.get_source_segment(source, node)
            # Continue traversing child nodes
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            # Check if the node is 'def main():'
            if node.name == "main":
                self.start_lineno = node.lineno
                self.end_lineno = node.end_lineno
                self.main_block = ast.get_source_segment(source, node)
            # Continue traversing child nodes
            self.generic_visit(node)

    visitor = MainBlockVisitor()
    visitor.visit(tree)

    if visitor.main_block:
        return (visitor.start_lineno, visitor.end_lineno), visitor.main_block
    else:
        return None, None


def extract_exports(lines):
    return [
        match.group(2)
        for line in lines
        if (match := re.match(r"^(def|class)\s+(\w+)", line))
    ]


def extract_top_level_defines(lines):
    """things like log = logging.getLogger(__name__)"""
    return {
        match.group(1): line
        for line in lines
        if (match := re.match(r"^(\w+)\s*=", line))
    }


def parse_body_extract_exports(tree):
    """exports are top level def/class and not indented"""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if node.col_offset == 0:
                yield node.name


def parse_imports(line):
    tree = ast.parse(line)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                yield alias.asname or alias.name


def parse_body_for_all_imports(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                yield alias.name


def parse_body_for_used_ports(tree, ports: dict | list[str]):
    """Find all ports used in a body of code.

    Ports can be either a dict or a list. If it's a dict, then the keys are the
    default library name and the values are the import line. If it's a list,
    it's just the names to be exported.

    """
    used_ports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id in ports:
                used_ports.add(node.id)

    return used_ports


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
        source = file.read()
    lines = source.split("\n")
    tree = ast.parse(source)

    exports, imports, tldefines = {}, {}, {}
    file_contents, up_to_first_pragma = {}, []
    current_file = None
    newlines = 0

    import_pattern = re.compile(r"^(import|from)\s+(\w+)")
    pragma_pattern = re.compile(r'# pragma: newfile\("(.+)"\)')

    for line in lines:
        if line == "\n":
            newlines += 1
            if newlines > 1:
                continue
        else:
            newlines = 0

        # track imports
        if import_pattern.match(line):
            for name in parse_imports(line):
                imports[name] = line
            continue

        # each file starts with a pragma that delineates the new file
        pragma_match = pragma_pattern.match(line)
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

    # extract exports for last file
    if current_file:
        exports[current_file] = extract_exports(file_contents[current_file])

    # convert all contents to buffers
    for filename, contents in file_contents.items():
        file_contents[filename] = "\n".join(contents)

    # parse imports to add "as alias" back in imports[alias] = default_name
    for name, line in imports.copy().items():
        for node in parse_imports(line):
            if name not in imports:
                imports[name] = line

    # tldefines (ohgodthisspaghetti)
    tldefines = extract_top_level_defines(up_to_first_pragma)

    # create the new files
    created_filenames = []

    # Update the __init__ file to re-export symbols from the new module directory like the old file.
    with open("__init__.py", "w") as file:
        log.debug("Building __init__.py file")
        for new_filename, used_exports in exports.items():
            if used_exports:
                module_name = re.sub(r"\.py$", "", new_filename)
                file.write(f"from .{module_name} import *\n")

        file.write(f"\n__all__ = {[x for y in exports.values() for x in y]}\n")
    created_filenames.append("__init__.py")

    # Detect the main block and create a __main__.py file with the appropriate module imports
    up_to_first_pragma = "\n".join(
        [
            line
            for line in up_to_first_pragma
            if not (line.startswith("import ") or line.startswith("from "))
        ]
    )

    _, detected_main = detect_main_block(tree, source)
    main_block = up_to_first_pragma + detected_main if detected_main else ""
    if main_block is not None:
        with open("__main__.py", "w") as main_file:
            log.debug("Building __main__.py file")

            # Add necessary imports
            used_imports = parse_body_for_used_ports(ast.parse(main_block), imports)
            for name in used_imports:
                main_file.write(f"{imports[name]}\n")
            main_file.write("\n")

            # Add necessary exports from the __init__.py file
            used_exports = parse_body_for_used_ports(
                ast.parse(main_block), [x for y in exports.values() for x in y]
            )
            for name in used_exports:
                main_file.write(f"from . import {name}\n")
            main_file.write("\n")

            # Add the main block or call main()
            main_file.write(main_block)
        created_filenames.append("__main__.py")
        # Maybe generalize for below: Only real difference is how main deals with interports.
        # We are depending on tld's being included as part of up_to_first_pragma.
        # file_contents["__main__.py"] = main_block
        # tree = ast.parse(main_block)
        # exports["__main__.py"] = parse_body_for_used_ports(
        #     tree, [x for y in exports.values() for x in y]
        # )
        # imports["__main__.py"] = parse_body_for_used_ports(tree, imports)
        # created_filenames.append("__main__.py")

    # create the new files
    for new_filename, contents in file_contents.items():
        ctree = ast.parse(contents)
        used_exports = exports[new_filename]
        used_imports = parse_body_for_used_ports(ctree, imports)
        used_tldefines = parse_body_for_used_ports(ctree, tldefines)
        used_interports = parse_body_for_used_ports(
            ctree, [x for y in exports.values() for x in y]
        )

        with open(new_filename, "w") as new_file:
            # regular imports
            for name in used_imports:
                new_file.write(f"{imports[name]}\n")

            # inter package imports
            for name in used_interports:
                if name not in used_exports:
                    new_file.write(f"from . import {name}\n")

            # now write imports from tldefines
            for k, v in tldefines.items():
                for name in imports:
                    if name in v and k in used_tldefines:
                        new_file.write(f"{imports[name]}\n")

            # and the top level defines themselves
            for k, v in tldefines.items():
                if k in used_tldefines:
                    new_file.write(f"{v}\n")

            # now the exports
            if used_exports:
                new_file.write(f"\n__all__ = {used_exports}\n\n\n")

            # hack: strip main block from the file if detected
            span, detected_main = detect_main_block(ctree, contents)
            if detected_main and new_filename != "__main__.py":
                contents = contents.replace(detected_main, "")

            new_file.writelines(contents)
    created_filenames.extend(file_contents.keys())

    return created_filenames
