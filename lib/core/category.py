from typing import Self

class Category:
    name: str
    emoji: str|None
    children: list[str]

    def __init__(self, name, emoji: str|None = None, children: list[str]|list[Self] = []):
        self.name = name
        self.emoji = emoji
        if len(children) > 0:
            if isinstance(children[0], Category):
                self.children = list(map(lambda x: x.name, children)) # type: ignore
            else:
                self.children = children # type: ignore
        else:
            self.children = []
