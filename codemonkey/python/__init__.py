import ast


class _ImportsFinder(ast.NodeVisitor):
    """find all imports
    :ivar imports: (list - tuple) (module, name, asname, level)
    """

    def __init__(self):
        ast.NodeVisitor.__init__(self)
        self.imports = []

    def visit_Import(self, node):
        """callback for 'import' statement"""
        self.imports.extend((None, n.name, n.asname, None) for n in node.names)
        ast.NodeVisitor.generic_visit(self, node)

    def visit_ImportFrom(self, node):
        """callback for 'import from' statement"""
        self.imports.extend((node.module, n.name, n.asname, node.level) for n in node.names)
        ast.NodeVisitor.generic_visit(self, node)


def ast_imports(file_path):
    """get list of import from python module
    :return: (list - tuple) (module, name, asname, level)
    """
    with open(file_path, "r") as fp:
        text = fp.read()
    mod_ast = ast.parse(text, file_path)
    finder = _ImportsFinder()
    finder.visit(mod_ast)
    return finder.imports
