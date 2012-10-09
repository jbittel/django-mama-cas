from string import lower

from django import template


register = template.Library()

@register.filter
def field_type(field):
    """
    Returns a lowercased string containing the type of the associated field.
    This is used in templates for targeting markup and styles based on the
    type of field.
    """
    return lower(field.field.__class__.__name__)
