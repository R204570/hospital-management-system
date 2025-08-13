from django import template

register = template.Library()

@register.filter
def filter(queryset, attribute):
    """Filter a queryset to only include items with attribute=True"""
    if not queryset:
        return []
    return [item for item in queryset if getattr(item, attribute, False)]

@register.filter
def sub(value, arg):
    """Subtract the arg from the value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def mul(value, arg):
    """Multiply the value by the arg"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def divide(value, arg):
    """Divide the value by the arg"""
    try:
        return int(value) / int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0 