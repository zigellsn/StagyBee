#  Copyright 2019-2023 Simon Zigelli
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
import re
import ssl

import aiohttp
from asgiref.sync import async_to_sync
from django.core.validators import URLValidator
from django.utils.deconstruct import deconstructible
from django.utils.regex_helper import _lazy_re_compile
from tenacity import retry, retry_if_exception_type, wait_random_exponential, stop_after_delay


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def create_ssl_context(certificate=None):
    context = ssl.create_default_context()
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = False
    certificate.seek(0)
    context.load_verify_locations(cadata=certificate.read().decode("ascii"))
    return context


# From https://github.com/bsouthga/blog/blob/master/public/posts/color-gradients-with-python.md
def hex_to_rgb(hex_value):
    """ "#FFFFFF" -> [255,255,255] """
    # Pass 16 to the integer function for change of base
    return [int(hex_value[i:i + 2], 16) for i in range(1, 6, 2)]


# From https://github.com/bsouthga/blog/blob/master/public/posts/color-gradients-with-python.md
def rgb_to_hex(rgb):
    """ [255,255,255] -> "#FFFFFF" """
    # Components need to be integers for hex to make sense
    rgb = [int(x) for x in rgb]
    hex_rgb = "".join([f"0{v:x}" if v < 16 else f"{v:x}" for v in rgb])
    return f"#{hex_rgb}"


# From https://github.com/bsouthga/blog/blob/master/public/posts/color-gradients-with-python.md
def color_dict(gradient):
    """ Takes in a list of RGB sub-lists and returns dictionary of
      colors in RGB and hex form for use in a graphing function
      defined later on """
    return {"hex": [rgb_to_hex(rgb) for rgb in gradient],
            "r": [rgb[0] for rgb in gradient],
            "g": [rgb[1] for rgb in gradient],
            "b": [rgb[2] for rgb in gradient]}


# From https://github.com/bsouthga/blog/blob/master/public/posts/color-gradients-with-python.md
def linear_gradient(start_hex, finish_hex="#FFFFFF", n=10):
    """ returns a gradient list of (n) colors between
      two hex colors. start_hex and finish_hex
      should be the full six-digit color string,
      inlcuding the number sign ("#FFFFFF") """
    # Starting and ending colors in RGB form
    s = hex_to_rgb(start_hex)
    f = hex_to_rgb(finish_hex)
    # Initilize a list of the output colors with the starting color
    rgb_list = [s]
    # Calcuate a color at each evenly spaced value of t from 1 to n
    for t in range(1, n):
        # Interpolate RGB vector for color at the current value of t
        curr_vector = [
            int(s[j] + (float(t) / (n - 1)) * (f[j] - s[j]))
            for j in range(3)
        ]
        # Add it to our list of output colors
        rgb_list.append(curr_vector)

    return color_dict(rgb_list)


@retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
       stop=stop_after_delay(15))
@async_to_sync
async def get_request(url, certificate=None):
    async with aiohttp.ClientSession() as session:
        ssl_context = create_ssl_context(certificate)
        async with session.get(url, ssl=ssl_context) as response:
            return await response.read(), response.status


@retry(retry=retry_if_exception_type(aiohttp.ClientError), wait=wait_random_exponential(multiplier=1, max=15),
       stop=stop_after_delay(15))
@async_to_sync
async def post_request(url, certificate=None, payload=None):
    async with aiohttp.ClientSession() as session:
        ssl_context = create_ssl_context(certificate)
        async with session.post(url=url, data=payload, ssl=ssl_context) as response:
            return await response.read(), response.status


@deconstructible
class DockerURLValidator(URLValidator):

    def __init__(self, schemes=None, **kwargs):
        self.host_re = '(' + self.hostname_re + self.tld_re + '|localhost|' + self.hostname_re + ')'
        self.regex = _lazy_re_compile(r'^(?:[a-z0-9\.\-\+]*)://'  # scheme is validated separately
                                      r'(?:\S+(?::\S*)?@)?'  # user:pass authentication
                                      r'(?:' + self.ipv4_re + '|' + self.ipv6_re + '|' + self.host_re + ')'
                                      r'(?::\d{2,5})?'  # port
                                      r'(?:[/?#][^\s]*)?'  # resource path
                                      r'\Z',
                                      re.IGNORECASE)
        super().__init__(schemes, **kwargs)
