# Copyright 2019 Simon Zigelli
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
import time
import json
import importlib
import asyncio

picker = importlib.import_module('jwconf_stage.picker.models')

AUTO_LOGIN_URL = 'https://jwconf.org/?key=%s'
URL = 'https://jwconf.org/login.php?source=index.php&'
CONGREGATION = 'congregation'
USERNAME = 'username'
PASSWORD = 'password'
LOGIN = 'login'
ID_NAMES = 'names'
CLASS_NAME = 'name'
PROPERTY = 'background-color'
VALUE = 'rgba(23, 121, 186, 1)'
NAME = 'name'
NAMES = 'names'
REQUEST_TO_SPEAK = 'request_to_speak'


async def main(credential: picker.Credential):
    options = Options()
    # options.add_argument("--headless")
    try:
        browser = webdriver.Chrome(options=options)

        if not credential.autologin:
            browser.get(AUTO_LOGIN_URL % credential.autologin)
        else:
            credentials = [(CONGREGATION, credential.congregation),
                           (USERNAME, credential.username),
                           (PASSWORD, credential.password)]
            browser.get(URL)
            for value_pair in credentials:
                elem = browser.find_element_by_name(value_pair[0])
                elem.send_keys(value_pair[1])
            elem = browser.find_element_by_id(LOGIN)
            elem.click()

        WebDriverWait(browser, 3).until(ec.visibility_of_element_located((By.ID, ID_NAMES)))
        previous_names = {NAMES: []}
        while True:
            elements = browser.find_elements_by_class_name(CLASS_NAME)
            names = {NAMES: []}
            if len(elements) == 0:
                names = {NAMES: [{NAME: "",
                                  REQUEST_TO_SPEAK: False
                                  }]}
            else:
                for element in elements:
                    names[NAMES].append({
                        NAME: element.text,
                        REQUEST_TO_SPEAK: True if element.value_of_css_property(PROPERTY) == VALUE
                        else False
                    })
            if names != previous_names:
                json_data = json.dumps(names)
                print(json_data)
                previous_names = names
            time.sleep(1)
        # browser.close()
    except BaseException as e:
        print(e)


if __name__ == '__main__':
    my_credential = picker.Credential.objects.create_credential(congregation="",
                                                                username="", password="")
    loop = asyncio.get_event_loop()
    tasks = [main(my_credential)]
    loop.run_until_complete(
        asyncio.wait(tasks)
    )
    loop.close()

