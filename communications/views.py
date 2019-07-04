from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, ListView, DeleteView, DetailView

from booking.models import Course
from communications.models import Announcement, Comment
from itsBooking.extensions.mixins import UserInGroupMixin
from itsBooking.templatetags.helpers import user_in_group
from .forms import AnnouncementForm


class AnnouncementListView(UserInGroupMixin, ListView):
    model = Announcement
    allowed_groups = ('assistants', 'course_coordinators')

    def get_queryset(self):
        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        return Announcement.objects.filter(course=course).order_by('-id')

    def get_context_data(self):
        context = super().get_context_data()
        if user_in_group(self.request.user, "course_coordinators"):
            context.update({
                'announcement_form': AnnouncementForm(),
            })
        context.update({
            'course': get_object_or_404(Course, slug=self.kwargs['slug'])
        })
        return context

    def post(self, request, *args, **kwargs):
        # handle reviews through a separate view
        return CreateAnnouncementView.as_view()(request, *args, **kwargs)


class AnnouncementDetailView(UserInGroupMixin, DetailView):
    model = Announcement
    allowed_groups = ('assistants', 'course_coordinators')

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update({
            'comment_form': CreateCommentView.as_view()(self.request).context_data['form']
        })
        context.update({
            'show_delete': True
        })
        return context


class CreateAnnouncementView(UserInGroupMixin, CreateView):
    template_name = 'communications/announcement_list.html'
    model = Announcement
    form_class = AnnouncementForm
    allowed_groups = ('course_coordinators',)

    def get_success_url(self):
        return HttpResponseRedirect(
            reverse('announcements', kwargs={'slug': self.kwargs['slug']})
        )

    def form_valid(self, form):
        announcement = form.save(commit=False)
        announcement.author = self.request.user
        announcement.course = get_object_or_404(
            Course,
            slug=self.kwargs['slug']
        )
        announcement.save()
        return self.get_success_url()


class CreateCommentView(UserInGroupMixin, CreateView):
    model = Comment
    fields = ('content',)
    allowed_groups = ('assistants', 'course_coordinators')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['content'].widget.attrs['class'] = 'uk-textarea uk-form-small'
        form.fields['content'].widget.attrs['placeholder'] = 'Skriv inn din kommentar her...'
        return form

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.announcement = get_object_or_404(Announcement, pk=self.kwargs['pk'])
        comment.save()
        return HttpResponseRedirect(comment.get_absolute_url())


class DeleteAnnouncementView(UserPassesTestMixin, DeleteView):
    model = Announcement

    def test_func(self):
        return self.request.user == self.get_object().course.course_coordinator

    def get_success_url(self):
        announcement = get_object_or_404(Announcement, pk=self.kwargs['pk'])
        return reverse('announcements', kwargs={'slug': announcement.course.slug})
