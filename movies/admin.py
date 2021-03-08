from django.contrib import admin
from . import models


@admin.register(models.MovieDirectory)
class MovieDirectoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.MovieFile)
class MoviesAdmin(admin.ModelAdmin):
    list_display = ('path', 'probed', 'probed_width', 'probed_height', 'probed_video_codec', 'converted', '_original_size', '_output_size')
    list_filter = ('probed', 'converted', 'probed_width', 'probed_height', 'probed_video_codec')
    search_fields = ('path',)

    def _original_size(self, obj):
        return obj.original_size_human

    _original_size.admin_order_field = 'original_size'

    def _output_size(self, obj):
        return obj.output_size_human

    _output_size.admin_order_field = 'output_size'
