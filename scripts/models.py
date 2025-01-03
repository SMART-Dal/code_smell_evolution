from datetime import datetime as dt
from typing import Union

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
    def __init__(self, smell):
        self.smell: Union[ArchitectureSmell, DesignSmell, ImplementationSmell, TestabilitySmell, TestSmell] = smell
        self.introduced: CommitInfo = None
        self.removed: CommitInfo = None
        self.commit_span: int = None
        self.days_span: int = None
        self.refactorings: list[Refactoring] = []
        
    def introduced_at(self, commit_hash, datetime):
        self.introduced = CommitInfo(commit_hash, datetime)
    
    def removed_at(self, commit_hash, datetime):
        self.removed = CommitInfo(commit_hash, datetime)
        
    def to_dict(self):
        return {
            "smell": self.smell.to_dict(),
            "introduced": self.introduced.to_dict() if self.introduced else None,
            "removed": self.removed.to_dict() if self.removed else None,
            "commit_span": self.commit_span,
            "days_span": self.days_span,
            "refactorings": [r.to_dict() for r in self.refactorings]
        }
        
class _Smell:
    def __init__(self, package_name, smell_name, cause):
        self.package_name: str = package_name
        self.smell_name: str = smell_name
        self.cause: str = cause
        
class ArchitectureSmell(_Smell):
    kind = "Architecture Smell"
    def __init__(self, package_name, smell_name, cause):
        super().__init__(package_name, smell_name, cause)
        
    def to_dict(self):
        return {
            "smell_type": self.kind,
            "smell_name": self.smell_name,
            "package_name": self.package_name,
            "cause": self.cause
        }
    
    def __hash__(self):
        return hash(tuple(vars(self).values()))
    
    def __eq__(self, other):
        if isinstance(other, ArchitectureSmell):
            return vars(self) == vars(other)
        return False
        
class DesignSmell(_Smell):
    kind = "Design Smell"
    def __init__(self, package_name, smell_name, cause):
        super().__init__(package_name, smell_name, cause)
        self.type_name: str = None
        
    def to_dict(self):
        return {
            "smell_type": self.kind,
            "smell_name": self.smell_name,
            "package_name": self.package_name,
            "type_name": self.type_name,
            "cause": self.cause
        }
        
    def __hash__(self):
        return hash(tuple(vars(self).values()))
        
    def __eq__(self, other):
        if isinstance(other, DesignSmell):
            return vars(self) == vars(other)
        return False
        
class ImplementationSmell(_Smell):
    kind = "Implementation Smell"
    def __init__(self, package_name, smell_name, cause):
        super().__init__(package_name, smell_name, cause)
        self.type_name: str = None
        self.method_name: str = None
        self.start_line: int = None
        self.range: tuple = None
        
    def to_dict(self):
        return {
            "smell_type": self.kind,
            "smell_name": self.smell_name,
            "package_name": self.package_name,
            "type_name": self.type_name,
            "method_name": self.method_name,
            "cause": self.cause,
            "start_line": self.start_line,
            "range": self.range
        }
        
    def __hash__(self):
        return hash(tuple(vars(self).values()))
    
    def __eq__(self, other):
        if isinstance(other, ImplementationSmell):
            return vars(self) == vars(other)
        return False
        
class TestabilitySmell(_Smell):
    kind = "Testability Smell"
    def __init__(self, package_name, smell_name, cause):
        super().__init__(package_name, smell_name, cause)
        self.type_name: str = None
        
    def to_dict(self):
        return {
            "smell_type": self.kind,
            "smell_name": self.smell_name,
            "package_name": self.package_name,
            "type_name": self.type_name,
            "cause": self.cause
        }
        
    def __hash__(self):
        return hash(tuple(vars(self).values()))
    
    def __eq__(self, other):
        if isinstance(other, TestabilitySmell):
            return vars(self) == vars(other)
        return False
        
class TestSmell(_Smell):
    kind = "Test Smell"
    def __init__(self, package_name, smell_name, cause):
        super().__init__(package_name, smell_name, cause)
        self.type_name: str = None
        self.method_name: str = None
        self.range: tuple = None
    
    def to_dict(self):
        return {
            "smell_type": self.kind,
            "smell_name": self.smell_name,
            "package_name": self.package_name,
            "type_name": self.type_name,
            "method_name": self.method_name,
            "cause": self.cause,
            "range": self.range
        }
        
    def __hash__(self):
        return hash(tuple(vars(self).values()))
        
    def __eq__(self, other):
        if isinstance(other, TestSmell):
            return vars(self) == vars(other)
        return False
        
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