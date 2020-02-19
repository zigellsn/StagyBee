#  Copyright 2019-2020 Simon Zigelli
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

import aiohttp
from dateutil.relativedelta import relativedelta, MO

PREFIX = "https://www.jw.org/en/library/jw-meeting-workbook"


async def extract(start_date, end_date=None, language="en"):
    last_monday = start_date + relativedelta(weekday=MO(-1))

    async with aiohttp.ClientSession() as session:
        weeks = {}
        response_code = 200
        while response_code == 200:
            next_sunday = last_monday + relativedelta(days=6)
            if last_monday.year >= 2020:
                url = await __get_2020_url(last_monday, next_sunday)
            else:
                url = await __get_url(last_monday, next_sunday)
            response_code, content = await __get_workbook(session, url)
            if language == "en":
                times = await __parse(content, "en")
            else:
                language_url = await __get_language_url(content, language)
                response_code, content = await __get_workbook(session, language_url)
                times = await __parse(content, language)
            print(times)

            weeks[last_monday] = times
            last_monday = last_monday + relativedelta(days=7)
            if end_date is not None and last_monday > end_date:
                response_code = 404
    await session.close()
    return weeks


async def __get_month_name(month):
    switcher = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December"
    }
    return switcher.get(month, "Invalid month")


async def __get_language_regex(language):
    switcher = {
        "en": [r"\([0-9]+(\u0020|\u00A0)min.*?\)", r"[0-9]+", ")"],
        "de": [r"\(.*?[0-9]+(\u0020|\u00A0)Min.\)", r"[0-9]+", ")"],
        "fr": [r"\([0-9]+(\u0020|\u00A0)min.*?\)", r"[0-9]+", ")"],
        # "fa": [r"\(.*?‏[۱-۹]+ دقیقه\)", r"[۱-۹]+", "("], #TODO: Wrong regex.
        "it": [r"\([0-9]+(\u0020|\u00A0)min.*?\)", r"[0-9]+", ")"],
        "el": [r"\([0-9]+(\u0020|\u00A0)(λεπτά|λεπτό).*?\)", r"[0-9]+", ")"],
    }
    return switcher.get(language, "Invalid language")


async def __get_language_url(content, language):
    lines = content.split("\n")
    for line in lines:
        if line.find(f"hreflang=\"{language}\"") != -1:
            reg = re.compile(r"href=\".*?\"")
            text = re.findall(reg, line)
            if text:
                length = len(text[0]) - 1
                return text[0][6:length]
    return ""


async def __get_workbook(session, url):
    print(url)
    print("Fetching workbook...")
    async with session.get(url) as resp:
        response_code = resp.status
        if resp.status == 200:
            print("Download completed. Parsing...")
            content = await resp.text()
        return response_code, content


async def __parse(content, language):
    regex = await __get_language_regex(language)
    times = []
    lines = content.split("\n")
    for line in lines:
        clean = await __clean_html(line, regex[2])
        times_tmp = re.findall(regex[0], clean)
        if not times_tmp:
            continue
        ti = re.findall(regex[1], clean)
        if not ti:
            continue
        times.append([int(ti[0]), clean])
    return times


async def __get_url(last_monday, next_sunday):
    month = await __get_month_name(last_monday.month)
    if last_monday.month == next_sunday.month:
        url = f"{PREFIX}/{month.lower()}-{last_monday.year}-mwb/meeting-" \
              f"schedule-{month.lower()}{last_monday.day}-{next_sunday.day}/"
    else:
        next_month = await __get_month_name(next_sunday.month)
        url = f"{PREFIX}/{month.lower()}-{last_monday.year}-mwb/meeting-" \
              f"schedule-{month.lower()}{last_monday.day}-{next_month.lower()}{next_sunday.day}/"
    return url


async def __get_2020_url(last_monday, next_sunday):
    month = await __get_month_name(last_monday.month)
    if last_monday.month == next_sunday.month:
        url = f"{PREFIX}/{month.lower()}-{last_monday.year}-mwb/Our-Christian-Life-and-Ministry-" \
              f"Schedule-for-{month}-{last_monday.day}-{next_sunday.day}-{last_monday.year}/"
    else:
        next_month = await __get_month_name(next_sunday.month)
        if last_monday.year == next_sunday.year:
            url = f"{PREFIX}/{month.lower()}-{last_monday.year}-mwb/Our-Christian-Life-and-Ministry-" \
                  f"Schedule-for-{month}-{last_monday.day}-{next_month}-{next_sunday.day}-{last_monday.year}/"
        else:
            url = f"{PREFIX}/{month.lower()}-{last_monday.year}-mwb/Our-Christian-Life-and-Ministry-Schedule-" \
                  f"for-{month}-{last_monday.day}-{last_monday.year}-{next_month}-{next_sunday.day}-{next_sunday.year}/"
    return url


async def __clean_html(raw_html, regex):
    clean_reg = re.compile(r"<.*?>")
    clean_text = re.sub(clean_reg, "", raw_html)
    return clean_text[:clean_text.find(regex) + 1].strip()
