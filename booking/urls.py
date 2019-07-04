from django.urls import path
from booking.views import update_max_num_assistants, bi_registration_switch, ReservationList, \
    CourseDetailDelegator, AssistantReservationList

urlpatterns = [
    path('reservation/<str:slug>/', CourseDetailDelegator.as_view(), name='course_detail'),
    path('max_assistants/', update_max_num_assistants, name='update_max_num_assistants'),
    path('bi_registration_switch/', bi_registration_switch, name='bi_registration_switch'),
    path('reservations/', ReservationList.as_view(), name='student_reservation_list'),
    path('assistant_reservations/', AssistantReservationList.as_view(), name='assistant_reservation_list'),
]
