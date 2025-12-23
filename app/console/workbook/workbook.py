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

import asyncio
import dataclasses
import logging
import re
from datetime import datetime
from html.parser import HTMLParser

import aiohttp
from aiohttp import ClientConnectorError
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta, MO

from StagyBee.settings import WB_LANGUAGE_SWITCHER


@dataclasses.dataclass
class Regex:
    find_talks: str
    time_number: str
    time_text: str
    replace_talk: str
    replace_directions: str


@dataclasses.dataclass
class Response:
    code: int
    content: str


@dataclasses.dataclass
class Basic:
    kind: int = 0
    text: str = ""
    is_talk: bool = False


@dataclasses.dataclass
class Times:
    kind: int
    time: int
    talk: str
    directions: str


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


class BasicHTMLParser2024(HTMLParser):

    def __init__(self, *, convert_charrefs=True):
        super().__init__()
        self.text = ""
        self.kind = 0
        self.is_talk = False

    def handle_starttag(self, tag, attrs):
        if not self.is_talk and (tag.lower() == "h1" or tag.lower() == "h2" or tag.lower() == "h3"):
            self.is_talk = True
        if self.kind != 0:
            return
        for attr in attrs:
            if attr[0] == "class":
                if "dc-icon--gem" in attr[1]:
                    self.kind = 1
                    return
                elif "dc-icon--wheat" in attr[1]:
                    self.kind = 2
                    return
                elif "dc-icon--sheep" in attr[1]:
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
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
        self.SEC_CH_UA = '"Brave";v="141","Not?A_Brand";v="8","Chromium";v="141"'
        self.ACCEPT_LANGUAGE = "en-EN,en"

    async def get_workbooks(self, urls: dict[datetime, str], language: str = "en") -> dict[datetime, list[Times]]:
        if not self.language_exists(language):
            return {}

        async with aiohttp.ClientSession() as session:
            weeks = await asyncio.gather(
                *[self.__extract__(session, url, my_date, language) for my_date, url in urls.items()],
                return_exceptions=True)
            if (len(weeks) == 1 and isinstance(weeks[0], ClientConnectorError)) or weeks[0][0] is None:
                weeks_dict = {}
            else:
                weeks_dict = {i[0]: i[1] for i in weeks if i}
        await session.close()
        return weeks_dict

    def create_urls(self, start_date: datetime, end_date: datetime = None) -> dict[datetime, str]:
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

    @staticmethod
    def language_exists(language: str) -> bool:
        return language in WB_LANGUAGE_SWITCHER

    async def __extract__(self, session: aiohttp.ClientSession, url: str, week: datetime, language: str) -> tuple[
        datetime | None, list[Times]]:
        response = await self.__get_workbook__(session, url)
        if response.code == 200:
            if language == "en":
                if week.year < 2024:
                    times = await self.__parse__(response.content, "en")
                else:
                    times = await self.__parse_2024__(response.content, "en")
                return week, times
            else:
                language_url = await self.__get_language_url__(response.content, language)
                response = await self.__get_workbook__(session, language_url)
                if response.code == 200:
                    if week.year < 2024:
                        times = await self.__parse__(response.content, language)
                    else:
                        times = await self.__parse_2024__(response.content, language)
                    return week, times
                else:
                    return None, []
        else:
            return None, []

    @staticmethod
    def __get_month_name__(month: int) -> str:
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
    def __get_month_name_2021__(month: int) -> str:
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
    async def __get_language_regex(language: str, version: int = 2024) -> Regex:
        lang = WB_LANGUAGE_SWITCHER.get(language, "Invalid language")
        res = [d for d in lang if d["version"] >= version]
        return Regex(res[0]["regex"][0], res[0]["regex"][1], res[0]["regex"][2], res[0]["regex"][3], res[0]["regex"][4])

    @staticmethod
    async def __get_language_url__(content: str, language: str) -> str:
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

    async def __get_workbook__(self, session: aiohttp.ClientSession, url: str) -> Response:
        self.logger.info(url)
        self.logger.info("Fetching workbook...")
        headers = {"User-Agent": self.USER_AGENT,
                   "Accept-Language": self.ACCEPT_LANGUAGE,
                   "Sec-CH-UA": self.SEC_CH_UA}
        async with session.get(url, headers=headers) as resp:
            response_code = resp.status
            if response_code == 200:
                self.logger.info("Download completed. Parsing...")
                content = await resp.text()
            else:
                content = ""
            resp.release()
            return Response(code=response_code, content=content)

    async def __parse__(self, content: str, language: str) -> list[Times]:
        regex = await self.__get_language_regex(language)
        times: list[Times] = []
        lines = await self.__get_relevant_lines__(content)
        actual_part = 0
        for line in lines:
            basic = await self.__get_text_from_html__(line)
            if basic.is_talk:
                if basic.kind != 0 and basic.kind > actual_part:
                    actual_part = basic.kind
                    continue
                (talk_name, directions) = await self.__clean_html__(basic.text, regex.time_text)
                if talk_name is not None and talk_name != "":
                    basic.text = talk_name
                clean = re.sub(regex.replace_talk, "", basic.text)
                directions, ti = self.__get_time_and_directions__(directions, clean, regex)
                times_entry = Times(actual_part, int(ti[0]), clean, directions)
                if times_entry not in times:
                    times.append(times_entry)
        self.logger.info("Parsing completed.")
        return times

    async def __parse_2024__(self, content: str, language: str) -> list[Times]:
        regex = await self.__get_language_regex(language, 2024)
        times: list[Times] = []
        lines = await self.__get_relevant_lines__(content)
        actual_kind = 0
        next_basic = Basic()
        i = 0
        while i < len(lines):
            if next_basic.kind != 0 and next_basic.kind > actual_kind:
                actual_kind = next_basic.kind
            line = lines[i]
            basic = await self.__get_text_from_html_2024__(line)
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_basic = await self.__get_text_from_html_2024__(next_line)
            else:
                next_line = None

            if basic.kind != 0 and basic.kind > actual_kind:
                actual_kind = basic.kind

            if basic.is_talk:
                actual_clean = basic.text
                directions = ""
                talk_name = actual_clean
                if talk_name is not None and talk_name != "":
                    basic.text = talk_name
                actual_clean = re.sub(regex.replace_talk, "", basic.text)
                if next_line is not None and not next_basic.is_talk:
                    _, next_ti = self.__get_time_and_directions__(actual_clean, actual_clean, regex)
                    directions, ti = self.__get_time_and_directions__(next_basic.text, next_basic.text, regex)
                    if int(ti[0]) > int(next_ti[0]):
                        time = int(ti[0])
                    else:
                        time = int(next_ti[0])
                    times_entry = Times(actual_kind, time, actual_clean, directions)
                    if times_entry not in times:
                        times.append(times_entry)
                else:
                    _, ti = self.__get_time_and_directions__(actual_clean, actual_clean, regex)
                    times_entry = Times(actual_kind, int(ti[0]), actual_clean, directions)
                    if times_entry not in times:
                        times.append(times_entry)
            if next_basic.is_talk:
                i += 1
            else:
                i += 2
        self.logger.info("Parsing completed.")
        return times

    @staticmethod
    def __get_time_and_directions__(directions: str, clean: str, regex: Regex) -> tuple[str, list[int]]:
        times_tmp = re.search(regex.find_talks, clean)
        if times_tmp is None:
            ti = [0]
        else:
            ti = re.findall(regex.time_number, times_tmp.group(0))
        directions = re.sub(regex.replace_directions, "", directions)
        return directions, ti

    def __get_url__(self, last_monday: datetime, next_sunday: datetime) -> str:
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

    def __get_2020_url__(self, last_monday: datetime, next_sunday: datetime, year: int) -> str:
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
    async def __get_text_from_html__(raw_html: str) -> Basic:
        basic_parser = BasicHTMLParser()
        basic_parser.feed(raw_html)
        return Basic(kind=basic_parser.kind, text=basic_parser.text, is_talk=basic_parser.is_talk)

    @staticmethod
    async def __get_text_from_html_2024__(raw_html: str) -> Basic:
        basic_parser = BasicHTMLParser2024()
        basic_parser.feed(raw_html)
        return Basic(kind=basic_parser.kind, text=basic_parser.text, is_talk=basic_parser.is_talk)

    @staticmethod
    async def __clean_html__(content: str, regex: str) -> tuple[str, str]:
        for match in re.finditer(regex, content):
            return content[:match.end()].strip(), content[match.end():len(content)].strip()
        return content, ""

    @staticmethod
    async def __get_relevant_lines__(content: str) -> list[str]:
        def has_class_but_no_id(tag):
            return tag.has_attr("data-pid") or (
                    tag.has_attr("class") and ("dc-icon--gem" in tag["class"]
                                               or "dc-icon--wheat" in tag["class"]
                                               or "dc-icon--sheep" in tag["class"]
                                               or any("treasures" in s for s in tag["class"])
                                               or any("ministry" in s for s in tag["class"])
                                               or any("christianLiving" in s for s in tag["class"])))

        soup = BeautifulSoup(content, features="html.parser")
        soup_lines = soup.find_all("figure")
        for figure in soup_lines:
            figure.decompose()
        soup_lines = soup.find_all(has_class_but_no_id)

        lines = []
        for line in soup_lines:
            lines.append(str(line).replace("\r", "").replace("\n", ""))

        return lines
