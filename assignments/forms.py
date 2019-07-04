from django import forms

from assignments.models import Exercise


class ExerciseFeedbackForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['feedback_text'].widget.attrs['class'] = 'uk-form uk-textarea uk-form-small'
        self.fields['approved'].widget = forms.RadioSelect(
            choices=[
                (True, 'Godkjenn'),
                (False, 'Underkjenn')
            ],
            attrs={'class': 'uk-radio'},
        )
        self.fields['approved'].required = True

    class Meta:
        model = Exercise
        fields = ('feedback_text', 'approved',)
