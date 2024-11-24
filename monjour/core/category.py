from typing import Self

class Category:
    name: str
    emoji: str|None

    def __init__(self, name, emoji: str|None = None, children: list[str]|list[Self] = []):
        self.name = name
        self.emoji = emoji
