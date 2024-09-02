from django import template

register = template.Library()

@register.simple_tag
def get_username(user):
    username = user.username if user.is_authenticated else 'Guest'
    if len(username) > 10:
        return username[:10]
    return username