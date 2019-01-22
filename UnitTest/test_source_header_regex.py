from unittest import TestCase
from Domain.antistud_fun import check_paragraph_to_source_header


class TestHeaderSource(TestCase):
    def test(self):
        self.assertTrue(check_paragraph_to_source_header("источники"))

    def test_with_uppercase(self):
        self.assertTrue(check_paragraph_to_source_header("Источники"))

    def test_with_dot(self):
        self.assertTrue(check_paragraph_to_source_header("источники."))

    def test_with_text_before(self):
        self.assertFalse(check_paragraph_to_source_header("Денежные источники"))

    def test_with_text_after(self):
        self.assertFalse(check_paragraph_to_source_header("источники доходов"))


class TestHeaderLiterature(TestCase):
    def test(self):
        self.assertTrue(check_paragraph_to_source_header("литература"))

    def test_with_uppercase(self):
        self.assertTrue(check_paragraph_to_source_header("Литература"))

    def test_with_dot(self):
        self.assertTrue(check_paragraph_to_source_header("Литература."))

    def test_with_text_before(self):
        self.assertFalse(check_paragraph_to_source_header("источники литературных"))

    def test_with_text_after(self):
        self.assertFalse(check_paragraph_to_source_header("летературное достояние"))

    def tet_with_in_the_middle(self):
        self.assertFalse(check_paragraph_to_source_header("что-то там литература другое слово"))