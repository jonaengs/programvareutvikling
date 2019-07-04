import os

from django.contrib.auth.models import User, Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from assignments.models import Exercise
from booking.models import Course


class ExerciseTest(TestCase):
    def setUp(self):
        self.course = Course.objects.create(title='algdat', course_code='tdt4125')
        self.username = 'STUDENT'
        self.password = '123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.client.login(username=self.username, password=self.password)
        self.students_group = Group.objects.create(name='students')

    def test_file_upload(self):
        self.user.groups.add(self.students_group)
        prev_count = Exercise.objects.count()
        with open('manage.py') as f:
            response = self.client.post(
                reverse('upload_exercise', kwargs={'slug': self.course.slug}),
                {'file': f}
            )
            self.assertEqual(302, response.status_code)
            self.assertEqual(prev_count + 1, Exercise.objects.count())

    def test_post_upload_no_file_fail(self):
        prev_count = Exercise.objects.count()
        response = self.client.post(
            reverse('upload_exercise', kwargs={'slug': self.course.slug})
        )
        self.assertEqual(Exercise.objects.count(), prev_count)
        # self.assertFormError(response, 'form', 'file', 'Feltet er påkrevet.')

    def test_get_upload_page(self):
        self.user.groups.add(self.students_group)
        response = self.client.get(reverse('upload_exercise', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, response.status_code)

    def test_get_uploads_list_test_func(self):
        """
        asssistants and ccs should be able to access the page, no one else
        """

        self.user.groups.add(Group.objects.create(name='assistants'))
        self.user.groups.add(self.students_group)
        self.user.groups.add(Group.objects.create(name='course_coordinators'))

        response = self.client.get(reverse('exercise_uploads_list', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, response.status_code)

        self.user.groups.remove(Group.objects.get(name='assistants'))
        response = self.client.get(reverse('exercise_uploads_list', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, response.status_code)

        self.user.groups.remove(Group.objects.get(name='course_coordinators'))
        response = self.client.get(reverse('exercise_uploads_list', kwargs={'slug': self.course.slug}))
        self.assertEqual(403, response.status_code)

        self.user.groups.remove(Group.objects.get(name='students'))
        response = self.client.get(reverse('exercise_uploads_list', kwargs={'slug': self.course.slug}))
        self.assertEqual(403, response.status_code)

    def test_post_review(self):
        self.user.groups.add(self.students_group)
        self.test_file_upload()
        self.exercise = Exercise.objects.first()
        post = lambda: self.client.post(reverse('exercise_uploads_list', kwargs={'slug': self.course.slug}),
                                        {'approved': True, 'exercise_pk': self.exercise.pk, 'feedback_text': 'abc'})
        response = post()
        self.assertEqual(403, response.status_code, msg="unauthorized users should be denied review access")

        # assistants should be allowed to post reviews
        self.user.groups.add(Group.objects.create(name='assistants'))
        response = post()
        self.exercise.refresh_from_db()
        self.assertEqual(self.exercise.feedback_by, self.user)  # user should get registered as reviewer
        self.assertEqual(302, response.status_code)

        # assistants should be allowed to edit their own reviews
        response = post()
        self.assertEqual(302, response.status_code)

        self.user2 = User.objects.create_user(username='USER2', password=123)
        self.client.logout()
        self.client.login(username="USER2", password=123)
        self.user2.groups.add(Group.objects.get(name='assistants'))
        response = post()
        self.assertEqual(403, response.status_code,
                         msg="assistants should not be able to override each other's reviews")

        # course coordinators should be able to overrule all reviews
        self.user2.groups.add(Group.objects.create(name='course_coordinators'))
        response = post()
        self.assertEqual(302, response.status_code)

    def test_exercise_delete(self):
        # make sure file associated with exercise is deleted when exercise is deleted
        image = SimpleUploadedFile("img.png", b"file_content", content_type="image/png")
        self.exercise = Exercise.objects.create(file=image, student=self.user, course=self.course)
        path = self.exercise.file.path
        self.assertTrue(os.path.isfile(path))
        self.exercise.delete()
        self.assertFalse(os.path.isfile(path))

    def test_student_get_uploads_list_test_func(self):
        """
        only students should be able to access this page
        """

        self.user.groups.add(Group.objects.create(name='assistants'))
        self.user.groups.add(self.students_group)
        self.user.groups.add(Group.objects.create(name='course_coordinators'))

        response = self.client.get(reverse('student_exercise_uploads_list', kwargs={'slug': self.course.slug}))
        self.assertEqual(200, response.status_code)

        self.user.groups.remove(Group.objects.get(name='students'))
        response = self.client.get(reverse('student_exercise_uploads_list', kwargs={'slug': self.course.slug}))
        self.assertEqual(403, response.status_code)

    def test_student_exercise_list(self):
        # make sure that students can only see their own exercises
        self.user.groups.add(self.students_group)
        image1 = SimpleUploadedFile("img.png", b"file_content", content_type="image/png")
        self.exercise = Exercise.objects.create(file=image1, student=self.user, course=self.course)

        response = self.client.get(reverse('student_exercise_uploads_list', kwargs={'slug': self.course.slug}))
        exercise_list = list(response.context['exercise_list'])
        self.assertEqual(1, len(exercise_list))

        self.user2 = User.objects.create_user(username='USER2', password=123)
        self.client.logout()
        self.client.login(username=self.user2.username, password=123)
        self.user2.groups.add(Group.objects.get(name='students'))

        response2 = self.client.get(reverse('student_exercise_uploads_list', kwargs={'slug': self.course.slug}))
        exercise_list = list(response2.context['exercise_list'])
        self.assertEqual(0, len(exercise_list))
