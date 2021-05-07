from django.contrib import admin
from . import models


@admin.register(models.MovieDirectory)
class MovieDirectoryAdmin(admin.ModelAdmin):
    pass


def force_convert(modeladmin, request, queryset):
    queryset.update(error=False, force_convert=True)


force_convert.short_description = "Force to be converted"


@admin.register(models.MovieFile)
class MoviesAdmin(admin.ModelAdmin):
    list_display = ('path', 'probed', 'probed_width', 'probed_height', 'probed_video_codec', 'probed_bitrate',
                    'force_convert', 'converted', '_original_size', '_output_size', 'error')
    list_filter = ('probed', 'converted', 'probed_width', 'probed_height', 'probed_video_codec', 'error')
    search_fields = ('path',)
    actions = [force_convert]

    def _original_size(self, obj):
        return obj.original_size_human

    _original_size.admin_order_field = 'original_size'

    def _output_size(self, obj):
        return obj.output_size_human

    _output_size.admin_order_field = 'output_size'


class MovieToConvert(models.MovieFile):
    class Meta:
        proxy = True
        verbose_name_plural = 'Movies to convert'


@admin.register(MovieToConvert)
class MoviesToConvert(MoviesAdmin):
    def get_queryset(self, request):
        qs = models.all_to_convert(qs=super().get_queryset(request))
        return qs
