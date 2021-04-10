#  Copyright 2019-2021 Simon Zigelli
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DeleteView

from .forms import NotificationForm
from .models import Notification


class NotificationCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Notification
    form_class = NotificationForm
    success_url = reverse_lazy("settings")

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.create_date = timezone.now()
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_superuser


class NotificationUpdate(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Notification
    form_class = NotificationForm
    success_url = reverse_lazy("settings")

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.create_date = timezone.now()
        return super().form_valid(form)

    def test_func(self):
        return self.request.user.is_superuser


class NotificationDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Notification
    success_url = reverse_lazy("settings")

    def test_func(self):
        return self.request.user.is_superuser
