#  Copyright 2019-2024 Simon Zigelli
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
from django.utils.translation import get_language

from notification.models import Notification

register = template.Library()


@register.inclusion_tag("notification/notification_list.html")
def notifications():
    notification_list = Notification.objects.by_state(show_in_locale=[get_language()])
    return {"object_list": notification_list}


@register.inclusion_tag("notification/notification.html")
def notification(notification_object, index=0):
    return {"object": notification_object, "index": index}


@register.inclusion_tag("notification/notification_maintain_list.html")
def notifications_maintain():
    notification_list = Notification.objects.all()
    return {"object_list": notification_list}
