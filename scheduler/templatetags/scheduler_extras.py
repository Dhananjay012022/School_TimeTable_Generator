from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """
    Safely get mapping[key] in templates:
    {{ my_dict|get_item:some_key }}
    """
    if mapping is None:
        return None
    try:
        return mapping.get(key)
    except Exception:
        return None


@register.filter
def day_name(day_int):
    """
    Day integer (1..6) -> name.
    Usage: {{ period.day|day_name }}
    """
    mapping = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
    }
    return mapping.get(day_int, f"Day {day_int}")
