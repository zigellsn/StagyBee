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

import asyncio
import logging
import re

import aiohttp
from dateutil.relativedelta import relativedelta, MO

from StagyBee.settings.common import WB_LANGUAGE_SWITCHER


class WorkbookExtractor:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.PREFIX = "https://www.jw.org/en/library/jw-meeting-workbook"
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/79.0.3945.130 Safari/537.36"

    async def get_workbooks(self, urls, language="en"):
        async with aiohttp.ClientSession() as session:
            weeks = await asyncio.gather(
                *[self.__extract__(session, url, my_date, language) for my_date, url in urls.items()],
                return_exceptions=True)
            weeks_dict = {i[0]: i[1] for i in weeks if i}
        await session.close()
        return weeks_dict

    def create_urls(self, start_date, end_date=None):
        last_monday = start_date + relativedelta(weekday=MO(-1))
        urls = {}
        if end_date is None:
            end_date = start_date + relativedelta(months=2)
        while last_monday <= end_date:
            next_sunday = last_monday + relativedelta(days=6)
            if last_monday.year >= 2020:
                url = self.__get_2020_url__(last_monday, next_sunday, last_monday.year)
            else:
                url = self.__get_url__(last_monday, next_sunday)

            urls[last_monday] = url
            last_monday = last_monday + relativedelta(days=7)
        return urls

    async def __extract__(self, session, url, week, language):
        response_code, content = await self.__get_workbook__(session, url)
        if response_code == 200:
            if language == "en":
                times = await self.__parse__(content, "en")
                return week.strftime("YYYY-MM-DD"), times
            else:
                language_url = await self.__get_language_url__(content, language)
                response_code, content = await self.__get_workbook__(session, language_url)
                if response_code == 200:
                    times = await self.__parse__(content, language)
                    return week.strftime("%Y-%m-%d"), times

    @staticmethod
    def __get_month_name__(month):
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

    @staticmethod
    def __get_month_name_2021__(month):
        switcher = {
            1: "January-February",
            2: "January-February",
            3: "March-April",
            4: "March-April",
            5: "May-June",
            6: "May-June",
            7: "July-August",
            8: "July-August",
            9: "September-October",
            10: "September-October",
            11: "November-December",
            12: "November-December"
        }
        return switcher.get(month, "Invalid month")

    @staticmethod
    async def __get_language_regex__(language):
        return WB_LANGUAGE_SWITCHER.get(language, "Invalid language")

    @staticmethod
    async def __get_language_url__(content, language):
        lines = content.split("\n")
        for line in lines:
            if line.find(f"hreflang=\"{language}\"") != -1:
                reg = re.compile(r"href=\".*?\"")
                text = re.findall(reg, line)
                if text:
                    length = len(text[0]) - 1
                    return text[0][6:length]
        return ""

    async def __get_workbook__(self, session, url):
        self.logger.info(url)
        self.logger.info("Fetching workbook...")
        headers = {
            "User-Agent": self.USER_AGENT}
        async with session.get(url, headers=headers) as resp:
            response_code = resp.status
            if response_code == 200:
                self.logger.info("Download completed. Parsing...")
                content = await resp.text()
            else:
                content = ""
            await resp.release()
            return response_code, content

    async def __parse__(self, content, language):
        regex = await self.__get_language_regex__(language)
        times = []
        lines = content.split("\n")
        for line in lines:
            clean = await self.__clean_html__(line, regex[2])
            if clean is None or clean == "":
                continue
            clean = re.sub(regex[3], "", clean)
            times_tmp = re.search(regex[0], clean)
            if not times_tmp:
                continue
            ti = re.findall(regex[1], times_tmp.group(0))
            if not ti:
                continue
            times.append([int(ti[0]), clean])
        self.logger.info("Parsing completed.")
        return times

    def __get_url__(self, last_monday, next_sunday):
        prefix = "meeting-schedule"

        month = self.__get_month_name__(last_monday.month)
        if last_monday.month == next_sunday.month:
            url = f"{self.PREFIX}/{month.lower()}-{last_monday.year}-mwb/" \
                  f"{prefix}-{month.lower()}{last_monday.day}-{next_sunday.day}/"
        else:
            next_month = self.__get_month_name__(next_sunday.month)
            url = f"{self.PREFIX}/{month.lower()}-{last_monday.year}-mwb/" \
                  f"{prefix}-{month.lower()}{last_monday.day}-{next_month.lower()}{next_sunday.day}/"
        return url

    def __get_2020_url__(self, last_monday, next_sunday, year):
        prefix = "Life-and-Ministry-Meeting-Schedule-for"
        month = self.__get_month_name__(last_monday.month)
        if year <= 2020:
            month_root = self.__get_month_name__(last_monday.month)
        else:
            month_root = self.__get_month_name_2021__(last_monday.month)
        if last_monday.month == next_sunday.month:
            url = f"{self.PREFIX}/{month_root.lower()}-{last_monday.year}-mwb/" \
                  f"{prefix}-{month}-{last_monday.day}-{next_sunday.day}-{last_monday.year}/"
        else:
            next_month = self.__get_month_name__(next_sunday.month)
            if last_monday.year == next_sunday.year:
                url = f"{self.PREFIX}/{month_root.lower()}-{last_monday.year}-mwb/" \
                      f"{prefix}-{month}-{last_monday.day}-{next_month}-{next_sunday.day}-{last_monday.year}/"
            else:
                url = f"{self.PREFIX}/{month_root.lower()}-{last_monday.year}-mwb/" \
                      f"{prefix}-{month}-{last_monday.day}-{last_monday.year}-{next_month}-{next_sunday.day}-" \
                      f"{next_sunday.year}/"
        return url

    @staticmethod
    async def __clean_html__(raw_html, regex):
        clean_reg = re.compile(r"<.*?>")
        clean_text = re.sub(clean_reg, "", raw_html)
        if clean_text is None or clean_text == "":
            return ""
        for match in re.finditer(regex, clean_text):
            return clean_text[:match.end()].strip()
