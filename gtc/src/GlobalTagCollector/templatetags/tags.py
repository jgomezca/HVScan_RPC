from django import template

from django.utils.html import escape




register = template.Library()

def get_badge_class(value):
    """Get badge class by entry status"""
    d = {
        'O': 'badge-info',
        'A': 'badge-success',
        'R': 'badge-inverse',
        'I': 'badge-important',
        'P': '',
    }
    return d.get(value, '')
register.filter('get_badge_class', get_badge_class)

@register.simple_tag
def active(request, pattern):
    """

    """
    import re
    if re.search(pattern, request.get_full_path()):
        return 'active'
    return ''

#register = template.Library()

#def current_time(format_string):
#    return datetime.datetime.now().strftime(format_string)
#
#register.simple_tag(current_time)

#from django import template
import datetime
class CurrentTimeNode(template.Node):
    """

    """

    def __init__(self, format_string):
        self.format_string = format_string
    def render(self, context):
        """

        """
        return datetime.datetime.now().strftime(self.format_string)



from django import template
def do_current_time(parser, token):
    """

    """
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, format_string = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
    if not (format_string[0] == format_string[-1] and format_string[0] in ('"', "'")):
        raise template.TemplateSyntaxError("%r tag's argument should be in quotes" % tag_name)
    return CurrentTimeNode(format_string[1:-1])

register.tag('current_time', do_current_time)






#from django import template

#register = template.Library()
#http://djangosnippets.org/snippets/361/
from django.template import  Node, TemplateSyntaxError, Variable


class AddParameter(Node):
    """

    """

    def __init__(self, varname, value):
        self.varname = Variable(varname)
        self.value = Variable(value)

    def render(self, context):
        """

        """
        req = Variable('request').resolve(context)
        params = req.GET.copy()
        params[self.varname.resolve(context)] = self.value.resolve(context)
        return '%s?%s' % (req.path, params.urlencode())


def addurlparameter(parser, token):
    """

    """
    from re import split
    bits = split(r'\s+', token.contents, 2)
    if len(bits) < 2:
        raise TemplateSyntaxError, "'%s' tag requires two arguments" % bits[0]
    return AddParameter(bits[1],bits[2])

register.tag('addurlparameter', addurlparameter)




class DelParameter(Node):
    """

    """

    def __init__(self, varname):
        self.varname = Variable(varname)

    def render(self, context):
        """

        """
        req = Variable('request').resolve(context)
        params = req.GET.copy()
        params[self.varname.resolve(context)] = ""
        return '%s?%s' % (req.path, params.urlencode())


def delurlparameter(parser, token):
    """

    """
    from re import split
    bits = split(r'\s+', token.contents, 1)
    if len(bits) < 1:
        raise TemplateSyntaxError, "'%s' tag requires one argument" % bits[0]
    return DelParameter(bits[1])

register.tag('delurlparameter', delurlparameter)

class HiddenParameters(Node):
    """

    """

    def __init__(self, varname):
        self.varname = Variable(varname)

    def render(self, context):
        """

        """
        req = Variable('request').resolve(context)
        params = req.GET.copy()
        params[self.varname.resolve(context)] = ""
        rezults = ""
        for name, values in params.lists():
            for value in values:
                rezults += "<input type='hidden'' name='%s' value='%s' />" % (escape(name), escape(value))

        return rezults


def hiddenparameters(parser, token):
    """

    """
    from re import split
    bits = split(r'\s+', token.contents, 1)
    if len(bits) < 1:
        raise TemplateSyntaxError, "'%s' tag requires one argument" % bits[0]
    return HiddenParameters(bits[1])

register.tag('hiddenparameters', hiddenparameters)