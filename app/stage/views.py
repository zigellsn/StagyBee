#  Copyright 2019-2022 Simon Zigelli
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

from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView

from StagyBee.views import SchemeMixin
from picker.models import Credential


class StageView(SchemeMixin, DetailView):
    model = Credential

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if 'HTTP_REFERER' in request.META and "picker" not in request.META['HTTP_REFERER']:
            return redirect('picker')

    @method_decorator(xframe_options_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_template_names(self):
        if self.get_object().touch:
            return "stage/stage.html"
        else:
            return "stage/stage_extractor.html"


class StageFormView(SchemeMixin, DetailView):
    model = Credential
    template_name = "stage/stage_form.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

    @method_decorator(xframe_options_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
