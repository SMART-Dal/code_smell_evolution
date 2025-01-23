from datetime import datetime as dt
from typing import Union
from utils import hashgen

class CorpusMetrics:
    def __init__(self):
        self.repos_info: dict = {}
        self.smell_metrics: dict = {}
    
    def add_repo_avg_commit_span(self, repo_name, avg_commit_span): #not used
        if repo_name not in self.repos_info:
            self.repos_info[repo_name] = {}
        self.repos_info[repo_name]["avg_commit_span"] = avg_commit_span
        
    def add_repo_avg_days_span(self, repo_name, avg_days_span): #not used
        if repo_name not in self.repos_info:
            self.repos_info[repo_name] = {}
        self.repos_info[repo_name]["avg_days_span"] = avg_days_span
        
    def add_smell_avg_commit_span(self, smell_name, avg_commit_span):
        if smell_name not in self.smell_metrics:
            self.smell_metrics[smell_name] = {}
        if "avg_commit_span" not in self.smell_metrics[smell_name]:
            self.smell_metrics[smell_name]["avg_commit_span"] = []
        self.smell_metrics[smell_name]["avg_commit_span"].append(avg_commit_span)
        
    def add_smell_avg_days_span(self, smell_name, avg_days_span):
        if smell_name not in self.smell_metrics:
            self.smell_metrics[smell_name] = {}
        if "avg_days_span" not in self.smell_metrics[smell_name]:
            self.smell_metrics[smell_name]["avg_days_span"] = []
        self.smell_metrics[smell_name]["avg_days_span"].append(avg_days_span)
        
    def add_smell_ref_count(self, smell_name, ref_type, ref_count):
        if smell_name not in self.smell_metrics:
            self.smell_metrics[smell_name] = {}
        if "ref_count" not in self.smell_metrics[smell_name]:
            self.smell_metrics[smell_name]["ref_count"] = {}
        if ref_type not in self.smell_metrics[smell_name]["ref_count"]:
            self.smell_metrics[smell_name]["ref_count"][ref_type] = 0
        self.smell_metrics[smell_name]["ref_count"][ref_type] += ref_count
        
# class RepositoryInfo:
#     def __init__(self, repo_name):
#         self.repo_name: str = repo_name
        
#         self.commit_span_history: list[int] = []
#         self.days_span_history: list[int] = []
        
#         self.smells_info: dict = {}    
        
ARCH_SMELL = "Architecture"
DESIGN_SMELL = "Design"
IMP_SMELL = "Implementation"
VALID_SMELL_KINDS = frozenset({ARCH_SMELL, DESIGN_SMELL, IMP_SMELL})
    
class Smell:
    def __init__(self, package_name, smell_kind, smell_name, cause):
        self._validate_smell_kind(smell_kind)
        
        self.package_name: str = package_name
        self.type_name: str = None
        self.method_name: str = None
        
        self.method_start_ln: int = None
        self.method_end_ln: int = None
        
        self.smell_kind: str = smell_kind  # Architecture, Design, Implementation
        self.smell_name: str = smell_name  # e.g. "God Class", "Feature Envy", "Long Method", "Eager Test"
        self.cause: str = cause

    def _validate_smell_kind(self, smell_kind):
        if smell_kind not in VALID_SMELL_KINDS:
            raise ValueError(f"Invalid smell kind: {smell_kind}.")
    
    def to_dict(self):
        return {
            "package_name": self.package_name,
            "type_name": self.type_name,
            "method_name": self.method_name,
            "method_start_ln": self.method_start_ln,
            "method_end_ln": self.method_end_ln,
            "smell_kind": self.smell_kind,
            "smell_name": self.smell_name,
            "cause": self.cause
        }
        
    def hash(self):
        if self.smell_kind == IMP_SMELL:
            instance_data = tuple(value for key, value in vars(self).items() if key != 'method_start_ln')
        else:
            instance_data = tuple(value for value in vars(self).values())
        
        return hashgen(instance_data)
    
    def full_hash(self):
        return hashgen(tuple(vars(self).values()))
    
    def copy(self):
        new_smell = Smell(
            self.package_name,
            self.smell_kind,
            self.smell_name,
            self.cause
        )
        new_smell.type_name = self.type_name
        new_smell.method_name = self.method_name
        new_smell.method_start_ln = self.method_start_ln
        new_smell.method_end_ln = self.method_end_ln
        return new_smell

class CommitInfo:
    def __init__(self, commit_hash, commit_datetime):
        self.commit_hash = commit_hash
        self.datetime: dt = commit_datetime
    
    def to_dict(self):
        return {
            "commit_hash": self.commit_hash,
            "datetime": self.datetime.isoformat()
        }    

class SmellInstance:
    def __init__(self, new_smell, initial_commit_info):
        self.smell_history: list[Smell] = [new_smell]
        self.versions: list[CommitInfo] = [initial_commit_info]
        
        self.is_alive: bool = True
        self.commit_span: int = None
        self.days_span: int = None
        
        self.introduced_by_refactorings: list[Refactoring] = []  # Refactorings that introduced the smell
        self.removed_by_refactorings: list[Refactoring] = []  # Refactorings that helped to remove the smell
    
    def latest_smell(self) -> Smell:
        return self.smell_history[-1]
    
    def add_new_version(self, changed_method_start_ln, commit_info):
        new_smell_version = self.latest_smell().copy()
        new_smell_version.method_start_ln = changed_method_start_ln
        self.smell_history.append(new_smell_version)
        
        self.versions.append(commit_info)
        
    def add_removed_version(self, commit_info):
        self.versions.append(commit_info)
        
    # def introduced_at(self, commit_hash, datetime):
    #     self.introduced = CommitInfo(commit_hash, datetime)
    
    # def removed_at(self, commit_hash, datetime):
    #     self.removed = CommitInfo(commit_hash, datetime)
        
    # def add_moved_at(self, commit_hash, datetime):
    #     self.move_sequence.append(CommitInfo(commit_hash, datetime))
    def get_file_path(self):
        smell = self.latest_smell()
        slash_pkg_path = smell.package_name.replace('.', '/') if smell.package_name else ''
        extension = f"{smell.type_name}.java" if smell.type_name else ''
        return f"{slash_pkg_path}/{extension}" if slash_pkg_path and extension else ''
        
    def to_dict(self):
        return {
            "smell_versions": [s.to_dict() for s in self.smell_history],
            "commit_versions": [c.to_dict() for c in self.versions],
            "is_alive": self.is_alive,
            "commit_span": self.commit_span,
            "days_span": self.days_span,
            "introduced_by_refactorings": [r.to_dict() for r in self.introduced_by_refactorings],
            "removed_by_refactorings": [r.to_dict() for r in self.removed_by_refactorings]
        }
        
        
# class _Smell:
#     def __init__(self, package_name, smell_name, cause):
#         self.package_name: str = package_name
#         self.smell_name: str = smell_name
#         self.cause: str = cause
        
# class ArchitectureSmell(_Smell):
#     kind = "Architecture Smell"
#     def __init__(self, package_name, smell_name, cause):
#         super().__init__(package_name, smell_name, cause)
        
#     def to_dict(self):
#         return {
#             "smell_type": self.kind,
#             "smell_name": self.smell_name,
#             "package_name": self.package_name,
#             "cause": self.cause
#         }
    
#     def __hash__(self):
#         return hash(tuple(vars(self).values()))
    
#     def __eq__(self, other):
#         if isinstance(other, ArchitectureSmell):
#             return vars(self) == vars(other)
#         return False
        
# class DesignSmell(_Smell):
#     kind = "Design Smell"
#     def __init__(self, package_name, smell_name, cause):
#         super().__init__(package_name, smell_name, cause)
#         self.type_name: str = None
        
#     def to_dict(self):
#         return {
#             "smell_type": self.kind,
#             "smell_name": self.smell_name,
#             "package_name": self.package_name,
#             "type_name": self.type_name,
#             "cause": self.cause
#         }
        
#     def __hash__(self):
#         return hash(tuple(vars(self).values()))
        
#     def __eq__(self, other):
#         if isinstance(other, DesignSmell):
#             return vars(self) == vars(other)
#         return False
        
# class ImplementationSmell(_Smell):
#     kind = "Implementation Smell"
#     def __init__(self, package_name, smell_name, cause):
#         super().__init__(package_name, smell_name, cause)
#         self.type_name: str = None
#         self.method_name: str = None
#         self.start_line: int = None
#         self.range: tuple = None
        
#     def to_dict(self):
#         return {
#             "smell_type": self.kind,
#             "smell_name": self.smell_name,
#             "package_name": self.package_name,
#             "type_name": self.type_name,
#             "method_name": self.method_name,
#             "cause": self.cause,
#             "start_line": self.start_line,
#             "range": self.range
#         }
    
#     def get_file_path(self):
#         slash_pkg_path = self.package_name.replace('.', '/') if self.package_name else ''
#         extension = f"{self.type_name}.java" if self.type_name else ''
#         return f"{slash_pkg_path}/{extension}" if slash_pkg_path and extension else ''
        
#     def __hash__(self):
#         # Exclude start_line from the hash calculation
#         return hash(tuple(value for key, value in vars(self).items() if key != 'start_line'))
    
#     def __eq__(self, other):
#         if isinstance(other, ImplementationSmell):
#             return all(
#                 key == 'start_line' or vars(self)[key] == vars(other)[key]
#                 for key in vars(self)
#             )
#         return False
        
# class TestabilitySmell(_Smell):
#     kind = "Testability Smell"
#     def __init__(self, package_name, smell_name, cause):
#         super().__init__(package_name, smell_name, cause)
#         self.type_name: str = None
        
#     def to_dict(self):
#         return {
#             "smell_type": self.kind,
#             "smell_name": self.smell_name,
#             "package_name": self.package_name,
#             "type_name": self.type_name,
#             "cause": self.cause
#         }
        
#     def __hash__(self):
#         return hash(tuple(vars(self).values()))
    
#     def __eq__(self, other):
#         if isinstance(other, TestabilitySmell):
#             return vars(self) == vars(other)
#         return False
        
# class TestSmell(_Smell):
#     kind = "Test Smell"
#     def __init__(self, package_name, smell_name, cause):
#         super().__init__(package_name, smell_name, cause)
#         self.type_name: str = None
#         self.method_name: str = None
#         self.range: tuple = None
    
#     def to_dict(self):
#         return {
#             "smell_type": self.kind,
#             "smell_name": self.smell_name,
#             "package_name": self.package_name,
#             "type_name": self.type_name,
#             "method_name": self.method_name,
#             "cause": self.cause,
#             "range": self.range
#         }
        
#     def __hash__(self):
#         return hash(tuple(vars(self).values()))
        
#     def __eq__(self, other):
#         if isinstance(other, TestSmell):
#             return vars(self) == vars(other)
#         return False
        
class _RefactoringChange:
    def __init__(self, file_path, range, code_element_type, code_element):
        self.file_path: str = file_path
        self.range: tuple = range
        self.code_element_type: str = code_element_type
        self.code_element: str = code_element
    
    def to_dict(self):
        return {
            "file_path": self.file_path,
            "range": self.range,
            "code_element_type": self.code_element_type,
            "code_element": self.code_element
        }

class Refactoring:
    def __init__(self, url, type_name, commit_hash):
        self.url: str = url
        self.type_name: str = type_name
        self.commit_hash: str = commit_hash
        self.changes: list[_RefactoringChange] = [] # right side locations
        
    def add_change(self, file_path, range, code_element_type, code_element):
        self.changes.append(_RefactoringChange(file_path, range, code_element_type, code_element))
        
    def to_dict(self):
        return {
            "url": self.url,
            "type_name": self.type_name,
            "commit_hash": self.commit_hash,
            "changes": [c.to_dict() for c in self.changes]
        }