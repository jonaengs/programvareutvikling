from django import forms

from booking.models import ReservationInterval
from itsBooking.templatetags.helpers import get_available_reservation_slots


class ReservationConnectionForm(forms.Form):
    reservation_pk = forms.IntegerField(widget=forms.HiddenInput())

    def clean(self):
        reservation = ReservationInterval.objects.get(pk=self.cleaned_data['reservation_pk'])
        if get_available_reservation_slots(reservation) <= 0:
            raise forms.ValidationError('No assistants available for this reservation interval')
