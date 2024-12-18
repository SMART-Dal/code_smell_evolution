class _Smell:
    def __init__(self, package_name, smell_name, cause):
        self.package_name: str = package_name
        self.smell_name: str = smell_name
        self.cause: str = cause
        
class ArchitectureSmell(_Smell):
    kind = "Architecture Smell"
    def __init__(self, package_name, smell_name, cause):
        super().__init__(package_name, smell_name, cause)
        
class DesignSmell(_Smell):
    kind = "Design Smell"
    def __init__(self, package_name, smell_name, cause):
        super().__init__(package_name, smell_name, cause)
        self.type_name: str = None
        
class ImplementationSmell(_Smell):
    kind = "Implementation Smell"
    def __init__(self, package_name, smell_name, cause):
        super().__init__(package_name, smell_name, cause)
        self.type_name: str = None
        self.method_name: str = None
        self.start_line: int = None
        self.range: tuple = None
        
class TestabilitySmell(_Smell):
    kind = "Testability Smell"
    def __init__(self, package_name, smell_name, cause):
        super().__init__(package_name, smell_name, cause)
        self.type_name: str = None
        
class TestSmell(_Smell):
    kind = "Test Smell"
    def __init__(self, package_name, smell_name, cause):
        super().__init__(package_name, smell_name, cause)
        self.type_name: str = None
        self.method_name: str = None
        self.start_line: int = None
        self.range: tuple = None
        
        
        
class _RefactoringChanges:
    def __init__(self):
        self.file_path: str = None
        self.range: tuple = None
        self.code_element_type: str = None
        self.code_element: str = None

class Refactoring:
    def __init__(self, url, type_name, commit_hash):
        self.url: str = url
        self.type_name: str = type_name
        self.commit_hash: str = commit_hash
        self.changes: list[_RefactoringChanges] = [] # right side locations
        
    def add_change(self, file_path, range, code_element_type, code_element):
        change = _RefactoringChanges()
        change.file_path = file_path
        change.range = range
        change.code_element_type = code_element_type
        change.code_element = code_element
        self.changes.append(change)