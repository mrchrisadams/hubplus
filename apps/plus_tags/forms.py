from django import forms
from django.utils.translation import ugettext_lazy as _

class AddTagForm(forms.Form):
    tagged_class = forms.CharField(max_length=100)
    tagged_id = forms.IntegerField()
    tag_type = forms.CharField(max_length=100)
    #should match the regex in plus_explore.urls.explore_filtered apart from the '+' sign being excluded
    tag_value = forms.RegexField(min_length=2, max_length=18, regex="^[ \w\._-]*$", error_messages={'invalid':_('Invalid tag name. ')})
