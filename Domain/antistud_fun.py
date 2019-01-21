import re
import os.path
from collections import namedtuple
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

        # self._index_regex = re.compile('\[([0-9],\s{0,2}){0,4}[' + str(self.index) + '](,\s{0,2}[0-9]){0,4}\]')
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


def find_sources(document):
    """
    Возвращает индекс параграфа в документе, с которого начниатеся список литературы
    :param document: WordDocument
    :return: int
    """
    last_mention = None
    for index, paragraph in enumerate(document.paragraphs):
        paragraph_text = paragraph.text.lower()
        if "список" in paragraph_text:
            if ("литератур" in paragraph_text) or ("источник" in paragraph_text):
                last_mention = index

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
    TODO возвращает объект с полями:
        - sources: List - список источников
            - text: str - текст источника
            - year: int - год источника
            - has_link: bool - есть ли ссылка на этот источник
            - is_modern: bool - проходит ли проверку на современность
            - paragraphs: List[str] - список параграфов, имеющих ссылки на этот источник
        - author: List[str, str, str] - автор работы
        - year: int - год написания работы

    TODO извлекать даты  с помощью '[1-2][0-9]{3}' => 1000-2999

    :param min_year: int минимальный год
    :param file_path: str путь к файлу
    :param callback: Callable[str, int[0:100]] принимает строку о текущей задаче и число с текущим процентом выполнения
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
            raise NoSourcesException()
        sources_paragraphs = paragraphs[sources_header_index+1:]

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
                source_index+=1

    callback("Завершение", 100)
    return sources
