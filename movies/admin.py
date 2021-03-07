from django.contrib import admin
from . import models


@admin.register(models.MovieDirectory)
class MovieDirectoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.MovieFile)
class MoviesAdmin(admin.ModelAdmin):
    list_display = ('path', 'probed', 'probed_width', 'probed_height', 'probed_video_codec', 'converted',)

