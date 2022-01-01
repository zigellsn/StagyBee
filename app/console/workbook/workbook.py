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

import asyncio
import logging
import re
from html.parser import HTMLParser

import aiohttp
from aiohttp import ClientConnectorError
from dateutil.relativedelta import relativedelta, MO

from StagyBee.settings import WB_LANGUAGE_SWITCHER


class BasicHTMLParser(HTMLParser):

    def __init__(self, *, convert_charrefs=True):
        super().__init__()
        self.text = ""
        self.kind = 0
        self.is_talk = False

    def handle_starttag(self, tag, attrs):
        if not self.is_talk and (tag.lower() == "strong" or tag.lower() == "h1" or tag.lower() == "h2"):
            self.is_talk = True
        if self.kind != 0:
            return
        for attr in attrs:
            if attr[0] == "class":
                if "treasures" in attr[1]:
                    self.kind = 1
                    return
                elif "ministry" in attr[1]:
                    self.kind = 2
                    return
                elif "christianLiving" in attr[1]:
                    self.kind = 3
                    return
                else:
                    self.kind = 0
            else:
                self.kind = 0

    def handle_data(self, data):
        self.text = f"{self.text}{data}"


class WorkbookExtractor:

    def __init__(self, *argss, **kwargs):
        super().__init__(*argss, **kwargs)
        self.logger = logging.getLogger("WorkbookExtractor")
        self.PREFIX = "https://www.jw.org/en/library/jw-meeting-workbook"
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/79.0.3945.130 Safari/537.36"

    async def get_workbooks(self, urls, language="en"):
        async with aiohttp.ClientSession() as session:
            weeks = await asyncio.gather(
                *[self.__extract__(session, url, my_date, language) for my_date, url in urls.items()],
                return_exceptions=True)
            if len(weeks) == 1 and isinstance(weeks[0], ClientConnectorError):
                weeks_dict = {}
            else:
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
        match month:
            case 1:
                return "January"
            case 2:
                return "February"
            case 3:
                return "March"
            case 4:
                return "April"
            case 5:
                return "May"
            case 6:
                return "June"
            case 7:
                return "July"
            case 8:
                return "August"
            case 9:
                return "September"
            case 10:
                return "October"
            case 11:
                return "November"
            case 12:
                return "December"
            case _:
                return "Invalid month"

    @staticmethod
    def __get_month_name_2021__(month):
        match month:
            case 1 | 2:
                return "January-February"
            case 3 | 4:
                return "March-April"
            case 5 | 6:
                return "May-June"
            case 7 | 8:
                return "July-August"
            case 9 | 10:
                return "September-October"
            case 11 | 12:
                return "November-December"
            case _:
                return "Invalid month"

    @staticmethod
    async def __get_language_regex(language):
        return WB_LANGUAGE_SWITCHER.get(language, "Invalid language")

    @staticmethod
    async def __get_language_url__(content, language):
        lines = content.split("\n")
        lines = list(filter(lambda item: f"hreflang=\"{language}\"" in item, lines))
        if not lines:
            return ""
        reg = re.compile(r"href=\".*?\"")
        text = re.findall(reg, lines[0])
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
        regex = await self.__get_language_regex(language)
        times = []
        lines = await self.__get_relevant_lines__(content)
        actual_part = 0
        for line in lines:
            (part, clean, is_talk) = await self.__get_text_from_html__(line)
            if is_talk:
                if part != 0 and part > actual_part:
                    actual_part = part
                    continue
                (talk_name, directions) = await self.__clean_html__(clean, regex[2])
                if talk_name is not None and talk_name != "":
                    clean = talk_name
                clean = re.sub(regex[3], "", clean)
                times_tmp = re.search(regex[0], clean)
                if times_tmp is None:
                    ti = [0]
                else:
                    ti = re.findall(regex[1], times_tmp.group(0))
                directions = re.sub(regex[4], "", directions)
                times.append([actual_part, int(ti[0]), clean, directions])
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
    async def __get_text_from_html__(raw_html):
        basic_parser = BasicHTMLParser()
        basic_parser.feed(raw_html)
        return basic_parser.kind, basic_parser.text, basic_parser.is_talk

    @staticmethod
    async def __clean_html__(content, regex):
        for match in re.finditer(regex, content):
            return content[:match.end()].strip(), content[match.end():len(content)].strip()
        return content, ""

    @staticmethod
    async def __get_relevant_lines__(content):
        lines = content.split("\n")
        return list(filter(lambda item: "data-pid" in item, map(lambda item: item.replace("\r", ""), lines)))
