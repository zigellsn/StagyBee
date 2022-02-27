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

from typing import Any

from django import template
from django.utils.safestring import mark_safe
from qr_code.qrcode.maker import make_qr_code_with_args

register = template.Library()


@register.simple_tag()
def qr_from_text(text: Any, **kwargs) -> str:
    if "dark_color" in kwargs:
        del kwargs["dark_color"]
    return mark_safe(make_qr_code_with_args(text, qr_code_args=kwargs).replace(' stroke="#000"', ""))
