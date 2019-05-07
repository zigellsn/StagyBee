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


def main():
    options = Options()
    # options.add_argument("--headless")
    try:
        auto_login = False  # TODO: Read from DB
        browser = webdriver.Chrome(options=options)

        if auto_login:
            auto_login_key = ''  # TODO: Read from DB
            browser.get(AUTO_LOGIN_URL % auto_login_key)
        else:
            credentials = [(CONGREGATION, ''),  # TODO: Read from DB
                           (USERNAME, ''),  # TODO: Read from DB
                           (PASSWORD, '')]  # TODO: Read from DB
            browser.get(URL)
            for value_pair in credentials:
                elem = browser.find_element_by_name(value_pair[0])
                elem.send_keys(value_pair[1])
            elem = browser.find_element_by_id(LOGIN)
            elem.click()

        WebDriverWait(browser, 3).until(ec.visibility_of_element_located((By.ID, ID_NAMES)))
        previous_names = []
        while True:
            elements = browser.find_elements_by_class_name(CLASS_NAME)
            names = []
            for element in elements:
                names.append((element.text,
                              True if element.value_of_css_property(PROPERTY) == VALUE
                              else False))
            if names != previous_names:
                for name in names:
                    print(name)  # TODO: Web Service -> Callback
                previous_names = names
            time.sleep(1)
        # browser.close()
    except BaseException as e:
        print(e)


if __name__ == '__main__':
    main()
