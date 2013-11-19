import os
import zipfile
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django_diazo.models import Theme, ThemeUserAgent


class ThemeForm(forms.ModelForm):
    upload = forms.FileField(required=False, label=_('Zip file'),
                             help_text=_('Will be unpacked in media directory.'))

    class Meta:
        model = Theme

    def save(self, commit=True):
        instance = super(ThemeForm, self).save(commit)
        instance.save()  # We need the pk

        if 'upload' in self.files:
            f = self.files['upload']
            z = zipfile.ZipFile(f)
            z.extractall(instance.theme_path(False))

        path = instance.theme_path()
        if not os.path.exists(path):
            os.makedirs(path)

        return instance


class UserAgentInline(admin.TabularInline):
    model = ThemeUserAgent
    fields = ['sort', 'pattern', 'allow']
    extra = 1


class ThemeAdmin(admin.ModelAdmin):
    inlines = [UserAgentInline]
    list_display = ('name', 'enabled', 'debug', 'sort', 'theme_url', 'theme_path',)
    list_editable = ('enabled', 'debug',)
    exclude = ('builtin', 'url', 'path',)
    list_filter = ('enabled', 'debug',)
    form = ThemeForm

    def get_fieldsets(self, request, obj=None):
        """Hook for specifying fieldsets for the different forms."""
        if not obj:
            return (
                (None, {'fields': ('name', 'slug', 'enabled', 'debug', 'sort', 'prefix',)}),
                (_('Upload theme'), {'fields': ('upload',)}),
            )
        elif obj.builtin:
            return (
                (None, {'fields': ('name', 'slug', 'enabled', 'debug', 'sort', 'prefix',)}),
            )


admin.site.register(Theme, ThemeAdmin)