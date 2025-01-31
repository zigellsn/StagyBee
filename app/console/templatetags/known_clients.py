#  Copyright 2019-2025 Simon Zigelli
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

from django import template
from guardian.shortcuts import get_objects_for_user

register = template.Library()


@register.inclusion_tag("console/knownclient_list.html", takes_context=True)
def known_clients_control(context):
    request = context["request"]
    known_client_list = get_objects_for_user(request.user, "console.control_client")
    return {"object_list": known_client_list}
