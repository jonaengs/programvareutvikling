import random
from io import BytesIO

import requests

from faker import Faker

from django.contrib.auth.models import Group, User
from django.core import management

from booking.models import Course, ReservationConnection
from communications.models import Avatar


def set_user_avatar(user):
    try:
        response = requests.get('http://gooddoggo.dog')
        image = BytesIO(response.content)
        a = Avatar.objects.create(user=user)
        a.image.save('dog.png', image, True)
        print(
            f'{user} avatar set'
        )
    except:
        print("Something went wrong while requesting and processing the dummy avatar. Please "
              "check your internet connection and the image source or disable this step of the setup process")


def setup_course(course, cc):
    course.course_coordinator = cc
    course.save()
    for bi in course.booking_intervals.all():
        r = random.randint(0, 5)
        bi.max_available_assistants = r
        for i in range(random.randint(0, r)):
            bi.assistants.add(random.choice(assistants))
            if random.randint(0, 2) == 2:
                break
        bi.save()
    # Register students for registration_intervals
    for bi in course.booking_intervals.all():
        registered_assistants = bi.assistants.all()
        if not registered_assistants:
            continue

        for ri in bi.reservation_intervals.all():
            possible_students = list.copy(students)
            for i in range(bi.assistants.all().count()):
                r = random.randint(1, 4)
                # 25 % chance of registering a student.
                if r != 1:
                    continue
                student = random.choice(possible_students)
                possible_students.remove(student)
                ReservationConnection.objects.create(reservation_interval=ri, student=student)


def generate_users(group, group_list, number):
    username = str(group)[:-1]
    for i in range(len(group_list), len(group_list) + number):
        if i == 0:
            u = User.objects.create_user(username=username, password='123')
        else:
            u = User.objects.create_user(username=username + str(i), password='123')
        first_name, *last_name = fake.name().split(' ')
        u.first_name, u.last_name = first_name, ' '.join(last_name)
        u.email = fake.email()
        u.groups.add(group)
        group_list.append(u)
        u.save()

        set_user_avatar(u)


# flush db
management.call_command('flush', verbosity=0, interactive=False)
print("!----DB flushed----!")

#################
# setup base data
#################

# setup faker in norwegian
fake = Faker('no_NO')

# create groups
g_students = Group.objects.create(name='students')
g_assistants = Group.objects.create(name='assistants')
g_ccs = Group.objects.create(name='course_coordinators')

# create admin user
u_admin = User.objects.create_user(username='admin', password='123', is_staff=True, is_superuser=True)

# lists of users
students = []
assistants = []
ccs = []

print("Generating users...")
generate_users(g_students, students, 6)
generate_users(g_assistants, assistants, 4)
generate_users(g_ccs, ccs, 2)

# create courses
c_algdat = Course.objects.create(title='Algoritmer og datastrukturer', course_code='TDT4120')
c_mat1 = Course.objects.create(title='Matematikk 1', course_code='TMA4100')
c_med = Course.objects.create(title='Innføring i medisin for ikke-medisinere', course_code='MFEL1010')

# add students to course
for student in students:
    c_algdat.students.add(student)

# add assistants to courses
for assistant in assistants:
    c_algdat.assistants.add(assistant)

# extra
c_mat1.students.add(students[0])
c_med.students.add(students[0])
c_mat1.students.add(assistants[0])

print("Setting up courses...")
setup_course(c_algdat, ccs[0])

print("Saving new data...")
for v in list(locals().values()):
    try:
        v.save()
    except (AttributeError, TypeError):
        pass
print("DB successfully reset!")
