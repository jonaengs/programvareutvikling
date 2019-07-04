import json

from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.test import TestCase, Client
from django.urls import reverse, reverse_lazy

from .models import Course, ReservationConnection


class StudentTableViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')
        self.username = 'STUDENT'
        self.password = '123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)
        self.student_group = Group.objects.create(name='students')
        self.user.groups.add(self.student_group)
        self.response = self.client.get(reverse('course_detail', kwargs={'slug': self.course.slug}))

    def test_context_data_intervals(self):
        """
        Context['interval'] should should contain elements equal the number of booking intervals each day
        """
        self.assertEqual(200, self.response.status_code)
        self.assertEqual(len(self.response.context['intervals']), len(self.course.booking_intervals.all()) / 5,
                         msg="context['interval'] "
                             "does not contain the elements equal to the number of booking intervals each day")

    def test_context_data_form(self):
        self.assertEqual(200, self.response.status_code)
        self.assertIsNotNone(self.response.context['form'])


class AssistantTableViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')
        self.username = 'ASSISTANT'
        self.password = '123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)
        self.assistants_group = Group.objects.create(name='assistants')
        self.user.groups.add(self.assistants_group)
        self.response = self.client.get(reverse('course_detail', kwargs={'slug': self.course.slug}))

    def test_context_data_intervals(self):
        """
        Context['interval'] should should contain elements equal the number of booking intervals each day
        """
        self.assertEqual(200, self.response.status_code)
        self.assertEqual(len(self.response.context['intervals']), len(self.course.booking_intervals.all()) / 5,
                         msg="context['interval'] "
                             "does not contain the elements equal to the number of booking intervals each day")


class CourseCoordinatorTableViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')
        self.username = 'STUDENT'
        self.password = '123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)
        self.cc_group = Group.objects.create(name='course_coordinators')
        self.user.groups.add(self.cc_group)
        self.response = self.client.get(reverse('course_detail', kwargs={'slug': self.course.slug}))

    def test_context_data(self):
        self.assertIsNotNone(self.response.context)


class CourseViewTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')

    def test_get_course_detail(self):
        response = self.client.get(reverse('course_detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(403, response.status_code, msg='users must be logged in to see booking tables')
        User.objects.create_user(username='USERNAME', password='123')
        self.client.login(username='USERNAME', password='123')
        response = self.client.get(reverse('course_detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(403, response.status_code, 'user must belong to a group')

    def test_max_assistants_update(self):
        # setup variables
        booking_interval = self.course.booking_intervals.first()
        new_max_num_assistants = 3

        response = self.client.get(reverse('update_max_num_assistants'),
                                   {'nk': booking_interval.nk, 'num': new_max_num_assistants})
        self.assertEqual(403, response.status_code, msg="unauthorized users should not be able to access this view")

        # set the course's course_coordinator and login as them
        cc = User.objects.create_user(username='test', password='123')
        booking_interval.course.course_coordinator = cc
        booking_interval.course.save()
        self.client.login(username='test', password='123')
        response = self.client.get(reverse('update_max_num_assistants'),
                                   {'nk': booking_interval.nk, 'num': new_max_num_assistants})
        self.assertEqual(200, response.status_code)
        # for some reason you need to get the booking_interval object again to detect changes to it
        booking_interval.refresh_from_db()
        self.assertEqual(new_max_num_assistants, booking_interval.max_available_assistants)


class ReservationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')
        self.username = 'STUDENT'
        self.password = '123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)
        self.student_group = Group.objects.create(name='students')
        self.user.groups.add(self.student_group)

    def test_make_reservation_deny_not_student(self):
        self.student_group.user_set.remove(self.user)
        response = self.client.post(reverse(
            'course_detail', kwargs={'slug': self.course.slug}
        ), {'booking_interval_nk': self.course.booking_intervals.first().nk, 'reservation_index': 0}
        )
        self.assertEqual(403, response.status_code)

    def test_make_reservation_deny_not_available(self):
        response = self.client.post(reverse(
            'course_detail', kwargs={'slug': self.course.slug}
        ), {'reservation_pk': self.course.booking_intervals.first().reservation_intervals.first().pk}
        )
        messages = list(response.context['messages'])
        self.assertEqual(40, messages[0].level)  # level:40 => error

    def test_make_reservation_success(self):
        # setup assistant and booking interval
        assistant_user = User.objects.create_user(username='ASSISTANT', password='123')
        assistant_group = Group.objects.create(name='assistants')
        assistant_group.user_set.add(assistant_user)
        self.course.booking_intervals.first().min_num_assistants = 1
        self.course.booking_intervals.first().assistants.add(assistant_user)
        self.reservation = self.course.booking_intervals.first().reservation_intervals.first()
        rc_count = self.reservation.connections.count()

        response = self.client.post(
            reverse('course_detail', kwargs={'slug': self.course.slug}),
            {'reservation_pk': self.reservation.pk}
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(rc_count + 1, self.reservation.connections.count())

    def test_student_reservation_list(self):
        assistant_user = User.objects.create_user(username='ASSISTANT', password='123')
        assistant_group = Group.objects.create(name='assistants')
        assistant_group.user_set.add(assistant_user)
        self.course.booking_intervals.first().min_num_assistants = 1
        self.course.booking_intervals.first().assistants.add(assistant_user)
        self.reservation = self.course.booking_intervals.first().reservation_intervals.first()
        ReservationConnection.objects.create(
            reservation_interval=self.reservation,
            student=self.user,
            assistant=assistant_user
        )

        # user is student
        response = self.client.get(reverse_lazy('student_reservation_list'))
        self.assertEqual(200, response.status_code)
        self.assertQuerysetEqual(
            response.context['object_list'],
            ReservationConnection.objects.filter(student=self.user), transform=lambda x: x
        )

        # user is no longer a student
        self.student_group.user_set.remove(self.user)
        response = self.client.get(reverse_lazy('student_reservation_list'))
        self.assertEqual(403, response.status_code)

    def test_assistant_reservation_list(self):
        assistant_user = User.objects.create_user(username='ASSISTANT', password='123')
        assistant_group = Group.objects.create(name='assistants')
        assistant_group.user_set.add(assistant_user)
        self.course.booking_intervals.first().min_num_assistants = 1
        self.course.booking_intervals.first().assistants.add(assistant_user)
        self.reservation = self.course.booking_intervals.first().reservation_intervals.first()
        self.client.logout()
        self.client.login(username='ASSISTANT', password='123')
        ReservationConnection.objects.create(
            reservation_interval=self.reservation,
            student=self.user,
            assistant=assistant_user
        )
        # user is assistant
        response = self.client.get(reverse_lazy('assistant_reservation_list'))
        self.assertEqual(200, response.status_code)

        # user is no longer a assistant
        assistant_group.user_set.remove(assistant_user)
        response = self.client.get(reverse_lazy('assistant_reservation_list'))
        self.assertEqual(403, response.status_code)

    def test_ReservationList_post(self):
        assistant_user = User.objects.create_user(username='ASSISTANT', password='123')
        assistant_group = Group.objects.create(name='assistants')
        assistant_group.user_set.add(assistant_user)
        self.course.booking_intervals.first().min_num_assistants = 1
        self.course.booking_intervals.first().assistants.add(assistant_user)
        self.reservation = self.course.booking_intervals.first().reservation_intervals.first()
        self.connection = ReservationConnection.objects.create(reservation_interval=self.reservation,
                                                               student=self.user,
                                                               assistant=assistant_user
                                                               )
        response = self.client.post(reverse_lazy(
            'student_reservation_list'
        ), {'reservation_connection_pk': self.connection.pk}
        )
        self.assertEqual(302, response.status_code)
        self.assertFalse(ReservationConnection.objects.filter(pk=self.connection.pk).exists())

    def test_ReservationList_post_deny(self):
        """
        Student should not be able to delete other students reservations
        """
        assistant_user = User.objects.create_user(username='ASSISTANT', password='123')
        assistant_group = Group.objects.create(name='assistants')
        assistant_group.user_set.add(assistant_user)
        student_user = User.objects.create_user(username='STUDENT1', password='123')
        self.student_group.user_set.add(student_user)
        self.course.booking_intervals.first().min_num_assistants = 1
        self.course.booking_intervals.first().assistants.add(assistant_user)
        self.reservation = self.course.booking_intervals.first().reservation_intervals.first()
        self.connection = ReservationConnection.objects.create(reservation_interval=self.reservation,
                                                               student=student_user,
                                                               assistant=assistant_user
                                                               )
        response = self.client.post(reverse_lazy(
            'student_reservation_list'
        ), {'reservation_connection_pk': self.connection.pk}
        )
        self.assertEqual(403, response.status_code)
        self.assertTrue(ReservationConnection.objects.filter(pk=self.connection.pk).exists())


class CourseModelTest(TestCase):
    def test_create_course(self):
        course = Course.objects.create(title="algdat", course_code="tdt4125")
        self.assertEqual(course.title, "algdat")
        try:
            Course.objects.create(title='algdat', course_code='tdt4125')
        except IntegrityError:
            pass
        else:
            self.fail("duplicate course code values should result in an error")

    def test_course_save(self):
        """Courses are assigned BookingInterval-objects when first saved"""
        course = Course.objects.create(title="algdat", course_code="tdt4125")
        self.assertEqual(Course.objects.filter(title="algdat").count(), 1)
        self.assertEqual(course.booking_intervals.filter(course=course).count(), 25)
        # assert that BookingInterval-objects are assigned only once
        course.save()
        self.assertEqual(course.booking_intervals.filter(course=course).count(), 25)
        # assert that slugs are generated on save()
        self.assertEqual(course.course_code, course.slug)


class MakeAssistantsAvailableTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')
        self.username = 'TEST_USER'
        self.password = 'TEST_PASS'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.booking_interval = self.course.booking_intervals.first()
        self.booking_interval.course.assistants.add(self.user)
        self.client.login(username=self.username, password=self.password)

    def test_unauthorized_registration_for_interval(self):
        """An user that is not registered as an assistant in the course should not be able to make
        himself available as an assistant."""

        self.client.logout()
        response = self.client.get(reverse('bi_registration_switch'),
                                   {'nk': self.booking_interval.nk})
        self.assertEqual(403, response.status_code, msg="unauthorized users should not be able to access this view")

    def test_authorized_registration_for_interval(self):
        """Assistant registers successfully for an interval"""

        response = self.client.get(reverse('bi_registration_switch'),
                                   {'nk': self.booking_interval.nk})
        self.assertEqual(200, response.status_code, msg="authorized users should be able to access this view")

    def test_assistant_registering_for_interval_in_wrong_course(self):
        """
        An assistant that is not an assistant in a specific course should not be able to register for an interval
        """
        # Create course that the assistant is not registered for
        self.course = Course.objects.create(title='matematikk 1', course_code='tdt3423')
        self.booking_interval = self.course.booking_intervals.first()

        response = self.client.get(reverse('bi_registration_switch'),
                                   {'nk': self.booking_interval.nk})
        self.assertEqual(403, response.status_code,
                         msg="Only assistants registered for the course should be able to register for intervals")

    def test_registration_available_for_interval(self):
        """
        The first assistant registering for an interval
        should result in registration_available=False and available_assistants_count=1
        """
        response = self.client.get(reverse('bi_registration_switch'),
                                   {'nk': self.booking_interval.nk})
        # Convert the content of type bytes to a dictionary.
        content = response.content
        content = json.loads(content.decode('utf-8'))

        self.assertEqual(200, response.status_code)
        self.assertEqual(content['registration_available'], False)
        self.assertEqual(content['available_assistants_count'], 1)

    def test_make_unavailable_for_interval(self):
        """
        An assistant makes himself unavailable for an interval with only one assistant
        should result in registration_available=True and available_assistants_count=0
        """
        # Registering the assistant for the interval
        self.booking_interval.assistants.add(self.user)

        response = self.client.get(reverse('bi_registration_switch'),
                                   {'nk': self.booking_interval.nk})
        # Convert the content of type bytes to a dictionary.
        content = response.content
        content = json.loads(content.decode('utf-8'))

        self.assertEqual(200, response.status_code)
        self.assertEqual(content['registration_available'], True)
        self.assertEqual(content['available_assistants_count'], 0)
