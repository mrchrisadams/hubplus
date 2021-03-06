from django import forms
import html5lib
from html5lib import sanitizer, serializer, treebuilders, treewalkers


class HTMLField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(HTMLField, self).__init__(*args, **kwargs)

    def clean(self, value):
        chars = super(HTMLField, self).clean(value)
        #chars = chars.encode('utf-8') # should really find out where we have decoded input to unicode and do it there instead
        p = html5lib.HTMLParser(tokenizer=sanitizer.HTMLSanitizer, tree=treebuilders.getTreeBuilder("dom")) # could use Beautiful Soup here instead
        s = serializer.htmlserializer.HTMLSerializer(omit_optional_tags=False)
        dom_tree = p.parseFragment(chars) #encoding="utf-8")  - unicode input seems to work fine
        
        walker = treewalkers.getTreeWalker("dom")
        stream = walker(dom_tree)
        gen = s.serialize(stream)
        out = ""
        for i in gen:
            out += i
        return out

class AttrDict(dict):
    """A dict whose items can also be accessed as member variables.

    >>> d = attrdict(a=1, b=2)
    >>> d['c'] = 3
    >>> print d.a, d.b, d.c
    1 2 3
    >>> d.b = 10
    >>> print d['b']
    10

    # but be careful, it's easy to hide methods
    >>> print d.get('c')
    3
    >>> d['get'] = 4
    >>> print d.get('a')
    Traceback (most recent call last):
    TypeError: 'int' object is not callable
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self

def i_debug(f):
    def g(*args, **kwargs):
        try :
            f(*args,**kwargs)
        except Exception, e :
            import ipdb
            ipdb.set_trace()
    return g



def make_name(s):
    """Turn the argument into a name suitable for a URL """
    s=s.strip()
    s=s.replace(' ','_')
    s=s.replace('/','_')
    s=s.replace(',','')
    s=s.lower()
    if isinstance(s,str):
        s = unicode(s,"utf-8")
    return s


from messages.models import Message
def message_user(sender, recipient, subject, body) :
    m = Message(subject=subject, body=body, sender = sender, recipient=recipient)
    m.save()


from copy import deepcopy
def overlay(d, d2) :
    """ Recursively overlay one dictionary with another
    Rules : if d2 has things not in d, add them
            if d and d2 have value which *isn't* a dictionary, d2 over-rides d
            if d and d2 have item which is a dictionary, 
                        recursively overlay value from d with d2"""
    nd = deepcopy(d)
    for k,v in d2.iteritems() :
        if not nd.has_key(k) :
            nd[k] = v
        elif nd[k].__class__ == dict and d2.__class__ == dict :
            nd[k] = overlay(nd[k],d2[k])
        else :
            nd[k] = d2[k]
    return nd

from django.conf import settings
# Not clever, but keeps a bit of fiddly logic out of the way of everyone else while we decide 
# the right way to handle it
def hub_name() :
    if settings.PROJECT_THEME=='psn' :
        return 'Region'
    else :
        return 'Hub'

def hub_name_plural() :
    if settings.PROJECT_THEME=='psn' :
        return 'Regions'
    else :
        return 'Hubs'

def main_hub_name() :
    if settings.PROJECT_THEME=='psn' :
        return "Main Region"
    else :
        return "Hub"
