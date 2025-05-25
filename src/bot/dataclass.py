from dataclasses import dataclass
from typing import Callable, Union

@dataclass
class FieldConfig:
    display_name: str
    unit: str = ""
    format_func: Callable[[Union[str, int, float, bool]], str] = lambda x: str(x)


FIELDS = {
    "priceCur": FieldConfig("Ціна", "грн"),
    "priceWithDiscount": FieldConfig("Ціна зі знижкою", "грн"),
    "priceSrp": FieldConfig("Рекомендована роздрібна ціна", "грн"),
    "isHidden": FieldConfig(
        "Наявність",
        "",
        lambda v: "Є в наявності" if v is False else "Немає в наявності"
    ),
}
