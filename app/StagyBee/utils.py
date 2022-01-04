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

import ssl

import aiohttp
from asgiref.sync import async_to_sync
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
