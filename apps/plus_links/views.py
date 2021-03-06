from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import simplejson
from models import Service, Link
from forms import LinkForm
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound
from apps.plus_permissions.api import secure_resource



@login_required
@secure_resource(obj_schema={'target':'any'})
def add_link(request, target):
    if request.POST :
        form = LinkForm(request.POST)

        if form.is_valid() :
            link = target.create_Link(request.user, target=target, 
                                      text = form.cleaned_data['text'],
                                      url = form.cleaned_data['url'],
                                      service=form.cleaned_data['service'])

            return render_to_response('plus_links/one_link.html',{'text':link.text, 'url':link.url})
        else :
            print form.errors
            return render_to_response('plus_links/error.html',{'errors':form.errors})

            
@login_required
@secure_resource(Link)
def remove_link(request, link) :

    try :
        link.delete()
        data = simplejson.dumps({'deleted':deleted})
    except Exception, e :
        data = simplejson.dumps({'error':'%s'%e})

    return HttpResponse(data, mimetype='application/json')

