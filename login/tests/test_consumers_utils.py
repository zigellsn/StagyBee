from django.test import TestCase

from login.consumers import generate_channel_group_name


class ExtractorUtilitiesTests(TestCase):
    def test_generate_channel_group_name(self):
        self.assertEqual("congregation.testAZaz", generate_channel_group_name("testAZaz"))
        self.assertEqual("congregation.T.e_s-t", generate_channel_group_name("T.e_s-t"))
        self.assertEqual("congregation.t_est_", generate_channel_group_name("t%est%"))
