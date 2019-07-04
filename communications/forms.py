from django import forms

from .models import Announcement


class AnnouncementForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['class'] = 'uk-form uk-textarea uk-form-small'
        self.fields['content'].widget.attrs['class'] = 'uk-form uk-textarea uk-form-small'

    class Meta:
        model = Announcement
        fields = ('title', 'content',)
