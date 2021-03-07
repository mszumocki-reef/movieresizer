from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class LoginRequired(LoginRequiredMixin):
    login_url = '/admin/login/'
    redirect_field_name = 'redirect_to'


class Dashboard(LoginRequired, TemplateView):
    template_name = 'movies/dashboard.html'
