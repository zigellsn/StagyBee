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

from django.test import TestCase

from stage.consumers import generate_channel_group_name


class ExtractorUtilitiesTests(TestCase):
    def test_generate_channel_group_name(self):
        self.assertEqual("congregation.console.testAZaz", generate_channel_group_name("console", "testAZaz"))
        self.assertEqual("congregation.console.T.e_s-t", generate_channel_group_name("console", "T.e_s-t"))
        self.assertEqual("congregation.console.t_est_", generate_channel_group_name("console", "t%est%"))
