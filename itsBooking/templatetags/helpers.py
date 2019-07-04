import calendar

from django import template

register = template.Library()


@register.filter(name='in_group')
def user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='nob_day')
def get_norwegian_day_name(day):
    nob_days = ['Mandag', 'Tirsdag', 'Onsdag', 'Torsdag', 'Fredag', 'Lørdag', 'Søndag']
    translation = dict(zip(calendar.day_name, nob_days))
    return translation.get(day, None)


@register.filter('available_slots')
def get_available_reservation_slots(reservation):
    return reservation.booking_interval.assistants.count() - reservation.connections.count()


@register.filter
def name(user):
    if user.first_name and user.last_name:
        return user.first_name + ' ' + user.last_name
    elif user.first_name:
        return user.first_name
    return user.username


@register.filter
def first_name(user):
    if user.first_name:
        return user.first_name.split(" ")[0]
    return user.username

@register.filter(name='already_made_reservation')
def user_has_made_reservation_for_interval(user, reservation_interval):
    for rc in reservation_interval.connections.all():
        if user == rc.student:
            return True
    return False

@register.filter('student_count')
def student_count_in_reservation_interval(booking_interval):
    count=0;
    for reservation in booking_interval.reservation_intervals.all():
        if reservation.connections.first() is not None:
            count+=1;
    return  count

