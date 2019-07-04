from django.contrib import admin
from .models import Course, BookingInterval


class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("course_code",)}


class BookingIntervalAdmin(admin.ModelAdmin):
    readonly_fields = ('nk', 'day', 'start', 'end', 'course', )


class ReservationAdmin(admin.ModelAdmin):
    readonly_fields = ('booking_interval', )


admin.site.register(Course, CourseAdmin)
admin.site.register(BookingInterval, BookingIntervalAdmin)
# admin.site.register(Reservation, ReservationAdmin)
