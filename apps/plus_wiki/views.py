from django.conf import settings

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404, HttpResponse
from django.db.models import Q
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.db import models

from django.template import RequestContext
from apps.plus_groups.models import TgGroup
from apps.plus_permissions.api import secure_resource, TemplateSecureWrapper, PlusPermissionsNoAccessException, has_access
from apps.plus_wiki.models import WikiPage, VersionDelta
from apps.plus_wiki.forms import EditWikiForm
from apps.plus_lib.parse_json import json_view
from apps.plus_lib.utils import AttrDict
from reversion import revision
from reversion.models import Version
from datetime import datetime
import simplejson as json

# HTMLDIFF
# --------
#http://codespeak.net/lxml/lxmlhtml.html#html-diff
from lxml.html.diff import htmldiff  # doesn't take not of changes in markup

#html_annotate -- nice for seeing who wrote what in a document

#from apps.plus_lib.htmldiff import htmldiff # this approach could be much better (bickings script) but I couldn't get it quite right. And I actually think it would take a lot of work to do this well.

def htmldiffer(ver_1, ver_2):
    content = htmldiff(ver_2.content, ver_1.content)
    license = htmldiff(ver_2.license, ver_1.license)
    title = htmldiff(ver_2.title, ver_1.title)
    return {'content': content, 'license':license, 'title':title}


@login_required
@secure_resource(TgGroup)
def edit_wiki(request, group, page_name, template_name="plus_wiki/create_wiki.html", current_app='plus_groups', **kwargs):
    try:
        secure_page = WikiPage.objects.plus_get(request.user, name=page_name, in_agent=group.get_ref())
    except WikiPage.DoesNotExist:
        raise Http404
    contributors = get_contributors(request.user, secure_page)
    try:
        secure_page.get_all_sliders
        perms_bool = True
    except PlusPermissionsNoAccessException:
        perms_bool = False

    return render_to_response(template_name, 
                              {'page':TemplateSecureWrapper(secure_page),
                               'form_action':reverse(current_app + ":create_WikiPage", args=[secure_page.in_agent.obj.id, secure_page.name]),
                               'contributors':contributors,
                               'tags':get_tags(request.user, secure_page),
                               'permissions':perms_bool}, 
                              context_instance=RequestContext(request, current_app=current_app))

@revision.create_on_success
@login_required
@secure_resource(TgGroup)
def create_wiki_page(request, group, page_name, template_name="plus_wiki/create_wiki.html", current_app='plus_groups', **kwargs):
    """creates OR saves WikiPages
    """
    form = EditWikiForm(request.POST)
    try:
        obj = WikiPage.objects.plus_get(request.user, name=page_name, in_agent=group.get_ref())
    except:
        raise Http404

    if form.is_valid():
        title = form.cleaned_data['title']
        content = form.cleaned_data['content']
        license = form.cleaned_data['license']
        if request.POST.get('preview', None):
            return render_to_response(template_name, 
                                      {'page':TemplateSecureWrapper(obj),
                                       'data':form.data,
                                       'preview_content': content,
                                       'form_action':reverse(current_app + ":create_WikiPage", args=[obj.in_agent.obj.id, obj.name])}, 
                                      context_instance=RequestContext(request, current_app=current_app))
        else:
            if obj.stub: # we should change the "created_by" on the genericreference/permissions system to "owner"
                obj.created_by = request.user
                revision.comment = 'Original'
            else:
                revision.comment = form.cleaned_data['what_changed']

            revision.user = request.user
            diff = htmldiffer(AttrDict({'title':title, 'content':content, 'license': license}), obj)
            diff = json.dumps(diff)
            #XXX this diff needs to only include things in the proximity of an insertion or deletion
            revision.add_meta(VersionDelta, delta=diff)
            obj.title = title
            obj.name_from_title()
            obj.content = content
            obj.license = license
            obj.stub = False
            obj.save()
            return HttpResponseRedirect(reverse(current_app + ':view_WikiPage', args=[group.id, obj.name]))

    return render_to_response(template_name, 
                              {'page':TemplateSecureWrapper(obj),
                               'revision':revision,
                               'data':form.data,
                               'errors': form.errors,
                               'form_action':reverse(current_app + ":create_WikiPage", args=[obj.in_agent.obj.id, obj.name])}, 
                              context_instance=RequestContext(request, current_app=current_app))

def get_contributors(user, obj):
    """Get all users who have a revision on this object in their revision_set
    """
    content_type = ContentType.objects.get(model=obj._inner.__class__.__name__.lower())
    return User.objects.plus_filter(user, revision__version__object_id__exact=str(obj.id), revision__version__content_type=content_type, distinct=True)


from apps.plus_tags.models import get_tags_for_object 

def get_tags(user, obj):
    """Get all the tags on this object
    """
    return get_tags_for_object(obj._inner, user)

from apps.plus_permissions.api import TemplateSecureWrapper


@secure_resource(TgGroup)
def view_wiki_page(request, group, page_name, template_name="plus_wiki/wiki.html", current_app='plus_groups', **kwargs):
    try:
        obj = WikiPage.objects.plus_get(request.user, name=page_name, in_agent=group.get_ref())
    except WikiPage.DoesNotExist:
        raise Http404
    version_list = Version.objects.get_for_object(obj._inner)
    version = Version.objects.get_for_date(obj._inner, datetime.now())
    contributors = get_contributors(request.user, obj)
    contributors = [TemplateSecureWrapper(contributor) for contributor in contributors]
    can_comment = False
    try:
        obj.comment
        can_comment = True
    except :
        pass # no permission
    try:
        obj.get_all_sliders
        perms_bool = True
    except PlusPermissionsNoAccessException:
        perms_bool = False
        
    edit = has_access(request.user, obj, 'WikiPage.Editor')
    
    return render_to_response(template_name, {
            'page':TemplateSecureWrapper(obj), 
            'version':version, 
            'contributors':contributors,
            'can_comment':can_comment,
            'version_list':version_list,
            'tags':get_tags(request.user, obj),
            'permissions':perms_bool,
            'can_edit': edit,
            'comparable':version_list.count()>1}, context_instance=RequestContext(request, current_app=current_app))






@login_required
@json_view
@secure_resource(TgGroup)
def view_version(request, group, page_name, **kwargs):
    ver_id = int(request.GET['ver_id'])
    ver = Version.objects.get(id=ver_id)
    obj = ver.get_object_version().object
    return {'title':obj.title, 'content':obj.content, 'license':obj.license}

from django.template.defaultfilters import date, time

@login_required
@revision.create_on_success
@secure_resource(TgGroup, required_interfaces=['Editor'])
def revert_wiki_page(request, group, page_name, current_app='plus_groups', **kwargs):
    try:
        obj = WikiPage.objects.plus_get(request.user, name=page_name, in_agent=group.get_ref())
    except WikiPage.DoesNotExist:
        raise Http404
    ver_id = int(request.GET['ver_id'])
    ver = Version.objects.get(id=ver_id)
    ver.revert()

    revision.user = request.user
    revision.add_meta(VersionDelta, delta="change")
    revision.comment = 'Reverted to version by %s written on %s at %s' %(ver.revision.user.display_name, date(ver.revision.date_created), time(ver.revision.date_created))

    return HttpResponseRedirect(reverse(current_app + ':view_WikiPage', args=[group.id, obj.name]))


@login_required
@secure_resource(TgGroup)
@json_view
def compare_versions(request, group, page_name, **kwargs):
    ver_1 = Version.objects.get(id=int(request.GET['ver_1'])).object_version.object
    ver_2 = Version.objects.get(id=int(request.GET['ver_2'])).object_version.object
    return htmldiffer(ver_1, ver_2)


@login_required
@secure_resource(TgGroup)
def delete_stub_page(request, group, page_name, current_app='plus_groups', **kwargs):
    try:
        obj = WikiPage.objects.plus_get(request.user, name=page_name, in_agent=group.get_ref(), stub=True)
        obj.delete()
    except WikiPage.DoesNotExist:
        pass
    return HttpResponseRedirect(reverse(current_app + ':group', args=[group.id]))
        
