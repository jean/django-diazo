import os
import zipfile
from codemirror.widgets import CodeMirrorTextarea
from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django_diazo.actions import enable_theme
from django_diazo.models import Theme
from django_diazo.utils import theme_path


class ThemeForm(forms.ModelForm):
    upload = forms.FileField(required=False, label=_('Zip file'),
                             help_text=_('Will be unpacked in media directory.'))
    rules_editor = forms.CharField(required=False, widget=CodeMirrorTextarea())

    class Meta:
        model = Theme

    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs and kwargs['instance']:
            rules = os.path.join(theme_path(kwargs['instance']), 'rules.xml')

            if os.path.exists(rules):
                fp = open(rules)
                if not 'initial' in kwargs:
                    kwargs['initial'] = {'rules_editor': fp.read()}
                else:
                    kwargs['initial'].update({'rules_editor': fp.read()})
                fp.close()
        super(ThemeForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(ThemeForm, self).save(commit)
        instance.save()  # We need the pk

        if 'upload' in self.files:
            f = self.files['upload']
            if zipfile._check_zipfile(f):
                z = zipfile.ZipFile(f)
                # Unzip uploaded theme
                z.extractall(theme_path(instance))

        path = theme_path(instance)
        if not os.path.exists(path):
            os.makedirs(path)

        rules = os.path.join(theme_path(instance), 'rules.xml')

        fp = open(rules, 'w')
        if self.cleaned_data['rules_editor']:
            fp.write(self.cleaned_data['rules_editor'])
        elif hasattr(settings, 'DIAZO_INITIAL_RULES_FILE') and \
                settings.DIAZO_INITIAL_RULES_FILE and \
                os.path.exists(settings.DIAZO_INITIAL_RULES_FILE):
            init_rules = open(settings.DIAZO_INITIAL_RULES_FILE)
            fp.write(init_rules.read())
        fp.close()

        if instance.enabled:
            for t in Theme.objects.all():
                t.enabled = False
                t.save()
        return instance


class ThemeAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled',)
    actions = [enable_theme]
    form = ThemeForm

    def get_fieldsets(self, request, obj=None):
        "Hook for specifying fieldsets for the add form."
        upload_classes = ()
        editor_classes = ('collapse',)
        if obj:
            upload_classes = ('collapse',)
            editor_classes = ()
        return (
            (None, {'fields': ('name', 'slug', 'prefix', 'rules', 'enabled', 'debug')}),
            (_('Built-in settings'), {'classes': ('collapse',), 'fields': ('path', 'url', 'builtin',)}),
            (_('Upload theme'), {'classes': upload_classes, 'fields': ('upload',)}),
            (_('Rules editor'), {'classes': editor_classes, 'fields': ('rules_editor',)}),
        )


admin.site.register(Theme, ThemeAdmin)