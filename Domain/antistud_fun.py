"""
TODO:
    1) Отделять нормативные документы от научных работ -> нормативные документы не считать устаревшими
    2) Проверка порядка источников
"""

import os.path
import re
from datetime import datetime
from typing import List

from docx import Document

# Настройки
MAX_ERRORS = 3  # Макс. кол-во ошибок для остановки поиска  [3]
MIN_LENGTH = 14  # Миним. длина источника   [14]
MIN_STAGE = 2  # Кол-во заголовков списка [2, но иногда может быть 1]


class NoSourcesException(Exception):
    pass


class NoAuthorException(Exception):
    pass


class _Author:
    last_name: str = None
    first_name: str = None
    middle_name: str = None

    _split_regex = re.compile(
        r'(?:(?P<f>[А-Я])(?:.\s?)(?:(?P<m>[А-Я])(?:.\s?))?(?P<l>[А-Я][а-я]+))'
        r'|(?:(?P<l2>[А-Я][а-я]+)(?:,?\s)(?P<f2>[А-Я])(?:.\s?)(?:(?P<m2>[А-Я])(?:.\s?))?)'
    )

    def __init__(self, text: str):
        res = self._split_regex.findall(text)
        if len(res) == 0:
            raise NoAuthorException()
        res = res[0]
        self.last_name = res[3] if res[0] == '' else res[2]
        self.first_name = res[4] if res[0] == '' else res[0]
        self.middle_name = res[1] if res[1] != '' else res[5] if res[5] != '' else None
        pass

    def find_in_text(self, text):
        for case in self.cases():
            if case in text:
                return True
        return False

    def cases(self):
        if self.middle_name is None:
            res = [t.format(self.first_name, self.last_name)
                   for t in ['{0}.{1}', '{0}. {1}', '{1} {0}.', '{1}, {0}.']]
        else:
            res = [t.format(self.first_name, self.middle_name, self.last_name)
                   for t in ['{0}.{1}.{2}', '{0}. {1}. {2}', '{0}.{1}. {2}',
                             '{2} {0}.{1}.', '{2} {0}. {1}.', '{2}, {0}.{1}', '{2}, {0}. {1}.']]
        return res


class SourceData:
    _author_regex = re.compile(
        r'(?:[A-Я][а-я^\-]+[,\.]?(?:[\s]?[А-Я]\.){1,2})|(?:(?:[А-Я]\.[\s]?){1,2}\s[A-Я][а-я^\-]+)'
    )
    _index_regex: re.compile

    text: str
    index: int
    authors: set = None
    year: int
    has_links: bool = False
    is_modern: bool = False
    links: List[str]

    def __init__(self, text, index, document, max_paragraph, min_year, check_authors=True, search_links=True):
        self.text = text
        self.index = index

        self._index_regex = re.compile(
            '(?:\[(?:[0-9]+,\s?)*' + str(self.index) + '(?:,\s?[0-9]+)*(?:,\s[СCcс]\.\s[0-9]+)?\])'
        )
        authors_names = self._author_regex.findall(text)
        if authors_names is not None and len(authors_names):
            self.authors = set()
            for author in authors_names:
                try:
                    self.authors.add(_Author(author))
                except NoAuthorException:
                    pass
        else:
            self.authors = None

        self.year = get_year(text)

        self._check(document, max_paragraph, check_authors, search_links)

        if self.year is not None:
            self.is_modern = min_year <= self.year
        else:
            self.is_modern = None

    def to_str(self):
        return f'{self.index}. {self.text}'

    def _check(self, document, max_paragraph=None, check_authors=True, search_links=True):
        if max_paragraph is not None:
            paragraphs = document.paragraphs[:max_paragraph]
        else:
            paragraphs = document.paragraphs

        links = []

        for index, paragraph in enumerate(paragraphs):
            if len(self._index_regex.findall(paragraph.text)):
                links.append(paragraph.text)
                if not search_links:
                    break
            if check_authors \
                    and self.authors is not None \
                    and len(self.authors) \
                    and all(author.find_in_text(paragraph.text) for author in self.authors):
                links.append(paragraph.text)
                if not search_links:
                    break

        if len(links):
            self.has_links = True
            self.links = links
        else:
            self.links = []


def get_year(source):
    """
    Возвращает год выхода источника
    :param source: str
    :return: int or None
    """

    years = [int(year) for year in re.findall('[1-2][0-9]{3}', source)]
    current_year = datetime.now().year
    years = [x for x in years if x <= current_year]
    if len(years) == 0:
        return None
    if len(years) == 1:
        return years[0]
    return max(years)


def check_paragraph_to_source_header(text):
    """
    Проверяет евляется ли переданный текст заголовком списка источников.
    :param text: str
    :return: bool
    """
    return bool(len(
            re.findall(r'^(?:(?:(?:[сС]писок|[иИ]спользованн)[а-я]*\s)?(?:использ[а-я]*\s)?(?:[Лл]итератур|[иИ]сточник)[а-я]*(?:[.:])?)$',
                       text, re.I)))


def find_sources(document, text: str = None):
    """
    Возвращает индекс параграфа в документе, с которого начниатеся список литературы
    список литературы
    :param text: optional Строка заголовка, указнная пользователем
    :param document: WordDocument
    :return: int
    """
    last_mention = None
    if text is None:
        for index, paragraph in enumerate(document.paragraphs):
            if check_paragraph_to_source_header(paragraph.text):
                last_mention = index
    else:
        for index, paragraph in enumerate(document.paragraphs):
            if text == paragraph.text:
                return index

    return last_mention


def is_source(paragraph):
    """
    Проверяет является ли параграф источником
    :param paragraph: Paragraph
    :return: bool
    """
    return len(re.findall(r'(?:[0-9]+\s?[CСcс]\.)|(?://)|(?:[1-2][0-9]{3})|(?:федеральн|положение)',
                          paragraph.text,
                          flags=re.I)) > 0


def find_missing_src(file_path, callback=lambda x, y: None, **kwargs):
    """
    :param file_path: str путь к файлу
    :param callback: Callable[str, int[0:100]] принимает строку о текущей задаче и число с текущим процентом выполнения
    :param kwargs:
        :key declare_text: Callable[[], str]
            Указатель на функцию, которая возращает текст заголовка спсика литературы

        :key min_year: int
            Все источники, которые были созданы ниже указанного года, будут помечены как устревшие

        :key check_author: bool
            если True, то включает проверку ссылок по авторам источников

        :key search_links: bool
            если True, то включает сбор абзацев, в которых есть ссылки на каждую из ссылок

    :return: List[SourceData]
        возвращает список всех источников
        и список индексов источников на которые есть ссылки
        и список индексов устаревших источников
    """

    if not os.path.isfile(file_path):
        return None, None
    else:

        document = Document(file_path)
        sources = []

        paragraphs = document.paragraphs
        sources_header_index = find_sources(document)
        if sources_header_index is None:
            source_header_text = kwargs.get('declare_text')()
            if source_header_text[1]:
                sources_header_index = find_sources(document, source_header_text[0])
                if sources_header_index is None:
                    raise NoSourcesException()
            else:
                raise NoSourcesException()
        sources_paragraphs = paragraphs[sources_header_index + 1:]

        source_index = 1
        for index, paragraph in enumerate(sources_paragraphs):
            callback('Поиск источников', round(index * 100 / len(sources_paragraphs)))
            if paragraph.text == '':
                continue
            if is_source(paragraph):
                sources.append(
                    SourceData(
                        paragraph.text,
                        source_index,
                        document,
                        sources_header_index,
                        min_year=kwargs.get('min_year', 1900),
                        check_authors=kwargs.get('check_authors', True),
                        search_links=kwargs.get('search_links', True)
                    )
                )
                source_index += 1

    callback("Завершение", 100)
    return sources
