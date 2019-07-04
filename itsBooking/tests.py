from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse_lazy, reverse

from assignments.models import Exercise
from booking.models import Course, ReservationConnection
from communications.models import Announcement


class TestBaseViews(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='username', password='123')
        self.user.save()
        self.client = Client()
        self.client.login(username='username', password='123')

    def test_populate(self):
        # populate should redirect to home when DEBUG=True and deny permission otherwise
        settings.DEBUG = True
        response = self.client.get(reverse_lazy('populate'))
        self.assertEqual(302, response.status_code)
        settings.DEBUG = False
        response = self.client.get(reverse_lazy('populate'))
        self.assertEqual(403, response.status_code)

    def test_home(self):
        response = self.client.get(reverse_lazy('home'))
        self.assertEqual(200, response.status_code)

    def test_login_fail(self):
        self.client.logout()
        # wrong username
        response = self.client.post(reverse_lazy('login'), {'username': 'WRONG', 'password': '123'})
        self.assertNotEqual(302, response.status_code)
        # wrong password
        response = self.client.post(reverse_lazy('login'), {'username': 'username', 'password': 'WRONG'})
        self.assertNotEqual(302, response.status_code)

    def test_login_success(self):
        self.client.logout()
        response = self.client.post(reverse_lazy('login'), {'username': 'username', 'password': '123'})
        self.assertEqual(302, response.status_code)

    def test_logout_fail(self):
        # handle logout request from anonymousUser
        self.client.logout()
        response = self.client.post(reverse_lazy('logout'))
        self.assertNotEqual(500, response.status_code)

    def test_logout_success(self):
        # test both get and post
        response = self.client.post(reverse_lazy('logout'))
        self.assertEqual(302, response.status_code)
        response = self.client.get(reverse_lazy('logout'))
        self.assertEqual(302, response.status_code)


class AssistantViewTest(TestCase):
    def setUp(self):
        """
        Runs before every test
        """
        self.client = Client()
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')
        self.username = 'ASSISTANT'
        self.password = '123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)
        self.assistants_group = Group.objects.create(name='assistants')
        self.user.groups.add(self.assistants_group)

        self.cc = User.objects.create_user(username='CC', password='123')
        self.cc_group = Group.objects.create(name='course_coordinators')
        self.cc.groups.add(self.cc_group)
        self.course.course_coordinator = self.cc
        self.course.save()

    def test_context_data_announcement(self):
        """
        Announcements of the course should be in context['announcements']
        """
        self.course.course_coordinator = self.cc
        self.course.save()
        # Create announcement
        announcement = Announcement.objects.create(
            title='test',
            content='test',
            author=self.cc,
            course=self.course)
        self.response = self.client.get(reverse('course_landing_page', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, self.response.status_code)
        self.assertIn(announcement, self.response.context['announcements'])

    def test_context_booking_intervals(self):
        """
        Booking intervals that have the relevant user as an assistant should be in context['booking_intervals']
        """
        booking_interval = self.course.booking_intervals.first()
        booking_interval.assistants.add(self.user)
        booking_interval.save()
        self.response = self.client.get(reverse('course_landing_page', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, self.response.status_code)
        self.assertIn(booking_interval, self.response.context['booking_intervals'])

    def test_context_booking_intervals_empty(self):
        """
        Booking intervals that have the relevant user as an assistant should be in context['booking_intervals']
        """
        booking_interval = self.course.booking_intervals.first()
        self.response = self.client.get(reverse('course_landing_page', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, self.response.status_code)
        self.assertNotIn(booking_interval, self.response.context['booking_intervals'])

    def test_context_exercise_list(self):
        """
        Exercises associated with the course should be in context['exercise_list']
        """
        student = User.objects.create(username='student', password='123')
        image1 = SimpleUploadedFile("img.png", b"file_content", content_type="image/png")
        self.exercise = Exercise.objects.create(file=image1, student=student, course=self.course)
        self.response = self.client.get(reverse('course_landing_page', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, self.response.status_code)
        self.assertIn(self.exercise, self.response.context['exercise_list'])

    def test_context_exercise_list_empty(self):
        """
        Exercises associated with the course should be in context['exercise_list']
        """
        student = User.objects.create(username='student', password='123')
        course2 = Course.objects.create(title='mathermatics', course_code='tdt4110')
        image1 = SimpleUploadedFile("img.png", b"file_content", content_type="image/png")
        self.exercise = Exercise.objects.create(file=image1, student=student, course=course2)
        self.response = self.client.get(reverse('course_landing_page', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, self.response.status_code)
        self.assertNotIn(self.exercise, self.response.context['exercise_list'])


class StudentViewTest(TestCase):
    def setUp(self):
        """
        Runs before every test
        """
        self.client = Client()
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')
        self.username = 'STUDENT'
        self.password = '123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)
        self.students_group = Group.objects.create(name='students')
        self.user.groups.add(self.students_group)
        self.cc = User.objects.create_user(username='CC', password='123')
        self.cc_group = Group.objects.create(name='course_coordinators')
        self.cc.groups.add(self.cc_group)
        self.course.course_coordinator = self.cc
        self.course.save()

    def test_context_data_reservations_empty(self):
        """
        context['reservations'] should be empty when the student has no reservations.
        """
        self.response = self.client.get(reverse('course_landing_page', kwargs={'slug': self.course.slug}))

        self.assertEqual(200, self.response.status_code)
        self.assertQuerysetEqual(self.response.context['reservations'], [])

    def test_context_data_reservations(self):
        """
        context['reservations'] should be empty when the student has no reservations.
        """
        assistant_user = User.objects.create_user(username='ASSISTANT', password='123')
        assistant_group = Group.objects.create(name='assistants')
        assistant_group.user_set.add(assistant_user)
        booking_interval = self.course.booking_intervals.filter(day=4).first()
        booking_interval.min_num_assistants = 1
        booking_interval.assistants.add(assistant_user)
        self.reservation = booking_interval.reservation_intervals.first()
        self.connection = ReservationConnection.objects.create(reservation_interval=self.reservation,
                                                               student=self.user,
                                                               assistant=assistant_user
                                                               )
        self.response = self.client.get(reverse('course_landing_page', kwargs={'slug': self.course.slug}))

        self.assertEqual(200, self.response.status_code)
        self.assertIn(self.connection, self.response.context['reservations'])

    def test_context_exercise_list(self):
        """
        Exercises uploaded by the student would be in context['exercise_list']
        """
        # student = User.objects.create(username='student', password='123')
        image1 = SimpleUploadedFile("img.png", b"file_content", content_type="image/png")
        self.exercise = Exercise.objects.create(file=image1, student=self.user, course=self.course)
        self.response = self.client.get(reverse('course_landing_page', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, self.response.status_code)
        self.assertIn(self.exercise, self.response.context['exercise_list'])

    def test_context_exercise_list_empty(self):
        """
        Exercises uploaded by the student would be in context['exercise_list']
        """
        student2 = User.objects.create(username='student', password='123')
        course2 = Course.objects.create(title='mathematics', course_code='tdt4110')
        image1 = SimpleUploadedFile("img.png", b"file_content", content_type="image/png")
        self.exercise = Exercise.objects.create(file=image1, student=student2, course=course2)
        self.response = self.client.get(reverse('course_landing_page', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, self.response.status_code)
        self.assertNotIn(self.exercise, self.response.context['exercise_list'])


class CourseCoordinatorViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')
        self.username = 'STUDENT'
        self.password = '123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)
        self.cc_group = Group.objects.create(name='course_coordinators')
        self.user.groups.add(self.cc_group)
        self.response = self.client.get(reverse('course_landing_page', kwargs={'slug': self.course.slug}))

    def test_context_data(self):
        self.assertIsNotNone(self.response.context)
