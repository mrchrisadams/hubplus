from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^attribute/(?P<object_id>[\w\._-]+)/(?P<object_class>[\w_]+)/(?P<fieldname>[\w_]+)/(?P<default>[\w_]*)$','plus_lib.views.field', {},name='attribute'),
)

