import django
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured


class UserInGroupMixin(UserPassesTestMixin):
    """
    Given a list/tuple of names of "allowed groups", checks if request.user belongs to any of those groups.
    If so, test_func returns True, otherwise it returns False.

    test_func will throw an error if the <class>.allowed_groups attribute is not defined or if
    any of the group names defined in <class>.allowed_groups do not correspond to the name of
    any existing group object.

    If the code is run while testing the last one will not be checked, as many tests often dont define
    every group that is allowed to access the views being tested.
    """
    allowed_groups = None

    def test_func(self):
        user_groups = self.request.user.groups.all()
        if self.allowed_groups is None:
            raise ImproperlyConfigured(
                '{0} is missing the allowed_groups attribute.'
                'The allowed_groups attribute must be a list or tuple of group names'
                'Define {0}.allowed_groups, or override '
                '{0}.test_func().'.format(self.__class__.__name__)
            )
        if not settings.TEST:  # If code is not being run as part of "./manage.py test" or "python manage.py test"
            try:
                allowed_groups = [Group.objects.get(name=group_name) for group_name in self.allowed_groups]
            except django.contrib.auth.models.Group.DoesNotExist:
                raise AttributeError(
                    'One or more of the group names defined in {0}.allowed_groups '
                    'do not correspond to the name of any registered group'.format(self.__class__.__name__)
                )

            return any(g in allowed_groups for g in user_groups)
        else:
            allowed_groups = self.allowed_groups
            return any(g.name in allowed_groups for g in user_groups)
