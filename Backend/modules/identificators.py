from dataclasses import dataclass


@dataclass
class Identificator:
    category: str
    item_id: str
    
    def __str__(self) -> str:
        return self.full()
    
    def __hash__(self) -> str:
        return hash(self.full())
    
    def full(self) -> str:
        return f"{self.category}.{self.item_id}"


def parse_identificator(identificator: str) -> Identificator:
    if "." not in identificator:
        raise ValueError(f"Cannot parse identificator with no category separator `.`: `{identificator}`")

    category, item_id = identificator.split(".", 1)
    return Identificator(category, item_id)
    