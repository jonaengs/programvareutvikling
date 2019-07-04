from django.urls import path
from communications.views import *

urlpatterns = [
    path('<str:slug>/announcements/', AnnouncementListView.as_view(), name='announcements'),
    path('announcement/delete/<int:pk>/', DeleteAnnouncementView.as_view(), name='delete_announcement'),
    path('comment/<int:pk>/', CreateCommentView.as_view(), name='create_comment'),
    path('<str:slug>/announcement/<int:pk>/', AnnouncementDetailView.as_view(), name='announcement_detail'),
]
