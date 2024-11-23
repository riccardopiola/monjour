import re
from typing import TypeVar, Generic

T = TypeVar('T')
class RegexParser(Generic[T]):
    classes: dict[str, str]
    regex_flags: int

    cases: dict[T, str]
    re_cases: dict[T, re.Pattern]

    def __init__(self, regex_flags: int = re.IGNORECASE):
        self.classes = {}
        self.regex_flags = regex_flags
        self.combined_regex = None
        self.combined_regex_map = []
        self.cases = {}
        self.re_cases = {}

    def define_classes(self, classes: dict[str, str]):
        for name, regex in classes.items():
            if not re.match(r"^[A-Za-z0-9_]+$", name):
                raise ValueError("Invalid class name")
            self.classes[name] = regex

    def add_case(self, discriminator: T, pattern: str):
        self.cases[discriminator] = pattern

    def build(self):
        if self.combined_regex is not None:
            return
        # Build the combined regex
        for discriminator, pattern in self.cases.items():
            # Replace class names with their definitions
            for match in re.finditer(r"(?<!\\)\{([A-Za-z0-9_]+)(?::([^\}]+))?\}", pattern):
                ident = match.group(1)
                if (class_name := match.group(2)) is None:
                    class_name = ident
                if class_name not in self.classes:
                    raise ValueError(f"Class {class_name} not defined")
                replacement = rf"(?P<{ident}>{self.classes[class_name]})"
                pattern = pattern.replace(match.group(0), replacement)
            # Add this case
            self.re_cases[discriminator] = re.compile(pattern)

    def parse(self, string: str) -> tuple[T, dict]|None:
        # This will throw if build() was not called
        # better than using an if statement that will get called thousands of times
        # print(string)
        for discriminator, re_pattern in self.re_cases.items():
            match = re_pattern.match(string)
            # print(re_pattern, match)
            if match:
                return discriminator, match.groupdict()
        return None