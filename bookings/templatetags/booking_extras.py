from django import template


register = template.Library()


@register.filter
def seat_range(capacity):
    try:
        capacity_value = int(capacity)
    except (TypeError, ValueError):
        return []

    if capacity_value < 1:
        return []

    return range(1, capacity_value + 1)
