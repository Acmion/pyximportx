class dependency:
    """
    Stores data about pyximport dependencies.

    If `import_as == false`, then the module was imported as `from module import name0, name1`.

    If `import_as == true`, then the module was imported as `import module as name`.
    """

    module_name: str
    qualifiers: str
    import_as: bool
    last_modified: float

    def __init__(self, module_name: str, qualifiers: str, import_as: bool, last_modified: float):
        self.module_name = module_name
        self.qualifiers = qualifiers
        self.import_as = import_as
        self.last_modified = last_modified

    def generate_cimport(self):
        if self.import_as:
            return f"import cython.cimports.{self.module_name} as {self.qualifiers}"
        else:
            return f"from cython.cimports.{self.module_name} import {self.qualifiers}"

    def generate_string(self):
        return f"{self.module_name}; {self.qualifiers}; {self.import_as}; {self.last_modified}"

    def __str__(self):
        return f"{{ module_name = {self.module_name}, last_modified = {self.last_modified} }}"

    def __repr__(self):
        return f"{{ module_name = {self.module_name}, last_modified = {self.last_modified} }}"

    @classmethod
    def generate_header_string(cls):
        return "module_name; qualifiers; import_as; last_modified"

    @classmethod
    def instantiate_from_string(cls, string: str):
        split = string.split(";")

        module_name = split[0]
        qualifiers = split[1]
        import_as = split[2] == "True"
        last_modified = float(split[3])

        return dependency(module_name, qualifiers, import_as, last_modified)