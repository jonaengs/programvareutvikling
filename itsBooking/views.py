from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView, DetailView

from assignments.models import Exercise
from booking.models import BookingInterval, ReservationConnection
from booking.models import Course
from communications.models import Announcement
from itsBooking.templatetags.helpers import user_in_group


class Home(LoginRequiredMixin, TemplateView):
    template_name = 'itsBooking/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['course_list'] = Course.objects.all()
        return context

    def dispatch(self, request, *args, **kwargs):
        if user_in_group(request.user, 'course_coordinators'):
            try:
                kwargs.update({
                    'slug': request.user.supervising_course.slug
                })
            except ObjectDoesNotExist:
                return HttpResponse("Denne brukeren har ingen tilknyttede emner. "
                                    "Vennligs kontakt superbruker for å få ordne dette")
            return HttpResponseRedirect(reverse('course_landing_page', kwargs=kwargs))
        return super().dispatch(request, *args, **kwargs)


class LoginView(SuccessMessageMixin, LoginView):
    template_name = 'itsBooking/login.html'

    def get_form(self):
        form = super().get_form()
        form.fields['username'].widget.attrs['class'] = 'uk-input uk-form-large'
        form.fields['password'].widget.attrs['class'] = 'uk-input uk-form-large'
        return form


class LogoutView(SuccessMessageMixin, LogoutView):
    pass


def populate_db(request):
    # runs the populate_db.py file, emptying and then filling the database with dummy data
    if settings.DEBUG:
        from . import populate_db
        messages.success(request, 'Database flushed and populated successfully!')
        return LogoutView.as_view()(request)
    raise PermissionDenied()


class AssistantLandingPage(DetailView):
    model = Course
    template_name = 'landing/landing_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        context['announcements'] = Announcement.objects.filter(course=course)
        context['booking_intervals'] = BookingInterval.objects.filter(
            Q(assistants=self.request.user)
            & Q(course=Course.objects.get(slug=self.kwargs['slug']))
        )
        context.update({'course': course,
                        'exercise_list': course.exercise_uploads.filter(approved__isnull=True)})
        return context


class StudentLandingPage(DetailView):
    model = Course
    template_name = 'landing/landing_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reservations'] = ReservationConnection.objects.filter(
            Q(student=self.request.user)
            & Q(reservation_interval__booking_interval__course=Course.objects.get(slug=self.kwargs['slug']))
        )
        context['exercise_list'] = Exercise.objects.filter(student=self.request.user)
        return context


class CourseCoordinatorLandingPage(DetailView):
    model = Course
    template_name = 'landing/landing_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        booking_intervals = BookingInterval.objects.filter(course=self.object)
        assistants_registered_for_bi = []
        booked_counter, available_intervals, full_booking_intervals = 0, 0, 0
        for booking_interval in booking_intervals:
            # Assistants registered for a booking interval
            for assistant in booking_interval.assistants.all():
                assistants_registered_for_bi.append(assistant)
            # Share of reservation_intervals booked by students
            for reservation_interval in booking_interval.reservation_intervals.all():
                available_intervals += booking_interval.assistants.count()
                booked_counter += reservation_interval.connections.count()
            # Number of full booking intervals
            if booking_interval.max_available_assistants == booking_interval.assistants.count():
                full_booking_intervals += 1
        context['assistants_registered_for_bi'] = list(set(assistants_registered_for_bi))
        context['booked_ri_count'] = booked_counter
        context['available_rintervals_count'] = available_intervals  # Reservation intervals available for students
        context['full_bi_count'] = full_booking_intervals
        context['available_bintervals_count'] = booking_intervals.all().count()  # Number of available booking intervals
        context['available_assistants'] = Course.objects.get(pk=self.object.pk).assistants.all().count()
        context['total_opening_time'] = booking_intervals.filter(max_available_assistants__gt=0).all().count() * 2

        # Percentages for progress bar at cc_overview
        context['assistant_percent'] = round(
            len(context['assistants_registered_for_bi']) / context['available_assistants'] * 100) \
            if context['available_assistants'] != 0 else 0
        context['student_percent'] = round(context['booked_ri_count'] / context['available_rintervals_count'] * 100) \
            if context['available_rintervals_count'] != 0 else 0
        context['max_studass_percent'] = round(context['full_bi_count'] / context['available_bintervals_count'] * 100) \
            if context['available_bintervals_count'] != 0 else 0

        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        # context["announcements"] = Announcement.objects.filter(course=course)
        context["announcements"] = Announcement.objects.filter(course=course).order_by('-id')  # [:10]

        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        context.update({'course': course,
                        'exercise_list': course.exercise_uploads.filter(approved__isnull=True)})

        return context


class LandingPageDelegator(View):
    delegator = {
        'students': StudentLandingPage.as_view(),
        'assistants': AssistantLandingPage.as_view(),
        'course_coordinators': CourseCoordinatorLandingPage.as_view(),
    }

    def dispatch(self, request, *args, **kwargs):
        # if user not logged in or not in any groups -> 403, if user is missing groups -> Login page
        if not request.user.is_authenticated or not request.user.groups.all():
            raise PermissionDenied
        request_user_group = self.request.user.groups.first().name

        return self.delegator.get(request_user_group, LoginView.as_view())(request, *args, **kwargs)
