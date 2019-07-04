from django.contrib.auth.models import User, Group
from django.urls import reverse
from booking.models import Course
from communications.models import Announcement
from django.test import TestCase, Client
from django.utils import timezone

from communications.views import AnnouncementDetailView


class AnnouncementModelTests(TestCase):
    def testCreateAnnouncement(self):
        """
        Create announcement and check that timestamp is correct
        """
        before_time = timezone.now()
        announcement = Announcement(title="Test announcement", content="heiehie")
        after_time = timezone.now()
        self.assertIs(announcement.timestamp >= before_time, True, msg="Timestamp is not correct")
        self.assertIs(announcement.timestamp <= after_time, True, msg="Timestamp is not correct")


class AnnouncementViewTest(TestCase):
    def setUp(self):
        """
        Runs before every test
        """
        self.client = Client()
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')
        self.username = 'CC'
        self.password = '123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)
        self.cc_group = Group.objects.create(name='course_coordinators')
        self.user.groups.add(self.cc_group)
        self.assistant_group = Group.objects.create(name='assistants')
        self.student_group = Group.objects.create(name='students')

    def _create_announcement(self):
        return Announcement.objects.create(
            title='test',
            content='test',
            author=self.user,
            course=self.course)

    def test_no_announcement_list(self):
        """
        If no announcement_list exists, an appropriate message is displayed
        """
        response = self.client.get(reverse('announcements', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        # self.assertContains(response, "Ingen kunngjøringer tilgjengelig")
        self.assertQuerysetEqual(response.context['announcement_list'], [],
                                 msg="There should not be announcement_list in context")

    def test_one_announcement(self):
        """
        The announcement_list page should display the announcement
        """
        self._create_announcement()
        response = self.client.get(reverse('announcements', kwargs={'slug': self.course.slug}))
        self.assertQuerysetEqual(
            response.context['announcement_list'].order_by('title'),
            ['<Announcement: test>']
        )

    def test_two_announcement_list(self):
        """
        The announcement_list page may display multiple announcement_list.
        """
        self._create_announcement()
        self._create_announcement()
        response = self.client.get(reverse('announcements', kwargs={'slug': self.course.slug}))
        self.assertQuerysetEqual(
            response.context['announcement_list'].order_by('title'),
            ['<Announcement: test>', '<Announcement: test>']
        )

    def test_announcements_list_page_testfunc(self):
        # logged in as cc
        response = self.client.get(reverse('announcements', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, response.status_code)
        self.assertIsNotNone(response.context['announcement_form'], "AnnouncementForm must be included for ccs")

        # forbidden for users who are not cc or assistant
        Group.objects.get(name="course_coordinators").user_set.remove(self.user)
        response = self.client.get(reverse('announcements', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 403)

        # assistants have access to the page, but not the form
        self.user.groups.add(self.assistant_group)
        response = self.client.get(reverse('announcements', kwargs={'slug': self.course.slug}))
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(KeyError):
            response.context['announcement_form']  # keyError proves the form is not included in the response

    def test_create_announcement_deny_not_course_coordinator(self):
        """
        It should not be possible to create an announcement if you are not a course coordinator
        """
        self.cc_group.user_set.remove(self.user)
        response = self.client.post(reverse(
            'announcements', kwargs={'slug': self.course.slug}
        ), {'title': 'Test Announcement', 'content': 'Test content'}
        )
        self.assertEqual(Announcement.objects.all().__str__(), '<QuerySet []>')
        self.assertEqual(response.status_code, 403)

    def test_create_announcement_success(self):
        """
        It should be possible to create an announcemnt if you are a course coordinator
        """
        response = self.client.post(reverse(
            'announcements', kwargs={'slug': self.course.slug}
        ), {'title': 'Test Announcement', 'content': 'Test content'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Announcement.objects.all().__str__(), '<QuerySet [<Announcement: Test Announcement>]>', )

    def test_get_announcement_detail_view_testfunc(self):
        # allow cc's and assistants. No one else
        self.test_create_announcement_success()
        announcement = Announcement.objects.first()
        response = self.client.get(reverse(
            'announcement_detail', kwargs={'slug': self.course.slug, 'pk': announcement.pk}
        ))
        self.assertEqual(200, response.status_code)

        self.user.groups.remove(self.cc_group)
        self.user.groups.add(self.assistant_group)
        response = self.client.get(reverse(
            'announcement_detail', kwargs={'slug': self.course.slug, 'pk': announcement.pk}
        ))
        self.assertEqual(200, response.status_code)

        self.user.groups.remove(self.assistant_group)
        self.user.groups.add(self.student_group)
        response = self.client.get(reverse(
            'announcement_detail', kwargs={'slug': self.course.slug, 'pk': announcement.pk}
        ))
        self.assertEqual(403, response.status_code)

    def test_create_comment(self):
        # allow cc's and assistants. No one else
        self.test_create_announcement_success()
        announcement = Announcement.objects.first()
        comment_count = announcement.comments.count()
        response = self.client.post(
            reverse('create_comment', kwargs={'pk': announcement.pk}),
            data={'content': 'CONTENT'}
        )
        self.assertEqual(302, response.status_code)
        self.assertEqual(comment_count + 1, announcement.comments.count(), msg="comment should be created on 200")

        self.user.groups.remove(self.cc_group)
        self.user.groups.add(self.assistant_group)
        response = self.client.post(
            reverse('create_comment', kwargs={'pk': announcement.pk}),
            data={'content': 'CONTENT'}
        )
        self.assertEqual(302, response.status_code)

        self.user.groups.remove(self.assistant_group)
        self.user.groups.add(self.student_group)
        response = self.client.post(
            reverse('create_comment', kwargs={'pk': announcement.pk}),
            data={'content': 'CONTENT'}
        )
        self.assertEqual(403, response.status_code)

    def test_delete_announcement_success(self):
        """
        The course coordinator of a course should be able to delete announcements
        """
        # Set user to be the course coordinater
        self.course.course_coordinator = self.user
        self.course.save()

        # Create announcement to delete
        announcement = self._create_announcement()

        response = self.client.post(
            reverse('delete_announcement', kwargs={'pk': announcement.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIs(Announcement.objects.filter(pk=announcement.pk).exists(), False)

    def test_delete_announcement_deny_not_course_coordinator(self):
        """
        Users who are not course coordinator of the course should not be able to delete announcements
        """
        # self.course has no course coordinator
        # Create announcement to delete
        announcement = self._create_announcement()
        response = self.client.post(
            reverse('delete_announcement', kwargs={'pk': announcement.pk}))
        self.assertEqual(response.status_code, 403)
        self.assertIs(Announcement.objects.filter(pk=announcement.pk).exists(), True)
