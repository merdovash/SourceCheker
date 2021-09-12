"""
TODO:
    1) Отделять нормативные документы от научных работ -> нормативные документы не считать устаревшими
    2) Проверка порядка источников
"""
import collections
import os.path
import re
from datetime import datetime
from enum import Enum
from typing import List, Iterator, Optional, Callable, Any, Dict, Sequence, Union

from Domain.docx_extract import process

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

    def __str__(self):
        res = [self.last_name]
        if len(self.first_name) == 1:
            res.append(self.first_name + '.')
        else:
            res.append(self.first_name)
        if self.middle_name:
            if len(self.middle_name) == 1:
                res.append(self.middle_name + '.')
            else:
                res.append(self.middle_name)

        return ' '.join(res)


class SourceData:
    _author_regex = re.compile(
        r'(?:[A-Я][а-я^\-]+[,\.]?(?:[\s]?[А-Я]\.){1,2})|(?:(?:[А-Я]\.[\s]?){1,2}\s[A-Я][а-я^\-]+)'
    )
    _index_regex: re.compile

    text: str
    index: int
    authors: set = None
    year: int
    links: List[str]
    is_modern = None

    def __init__(self, text, index, year: Optional[int] = None, link: Optional[str] = None,
                 authors: Optional[List[str]] = None, name: str = None, original: str = None):
        self.text = text
        self.index = index
        self._links = None
        self.original = original
        self.name = name

        self.index_regex = re.compile(
            r'(?:\[(?:[0-9]+,\s?)*' + str(self.index) + r'(?:,\s?[0-9]+)*(?:,\s[СCcс]\.\s[0-9]+)?\])'
        )

        self.authors = set()
        if authors is None:
            authors_names = self._author_regex.findall(text)
            if authors_names is not None and len(authors_names):
                self.authors = set()
                for author in authors_names:
                    try:
                        self.authors.add(_Author(author))
                    except NoAuthorException:
                        pass
        else:
            self.authors = set(map(_Author, authors))

        self.year = year

        self._e_link = link
        if not self.year and self._e_link:
            self.year = datetime.now().year

    def __str__(self):
        return repr(self)

    def __repr__(self):
        if self.name:
            return self.name
        if self.text:
            return self.text
        return self.original

    def find_links(self, document: 'Referat', check_authors=True, search_links=True):
        links = []

        for index, paragraph in enumerate(reversed(document.body())):
            if paragraph == self.original:
                continue
            if len(self.index_regex.findall(paragraph)):
                links.append(paragraph)
                if not search_links:
                    break
            if check_authors \
                    and self.authors is not None \
                    and len(self.authors) \
                    and all(author.find_in_text(paragraph) for author in self.authors):
                links.append(paragraph)
                if not search_links:
                    break
        self._links = links
        return links

    @property
    def has_links(self) -> bool:
        return bool(self.links)

    @property
    def links(self) -> List[str]:
        return self._links

    def set_limit_year(self, year):
        if self.year:
            self.is_modern = self.year >= year


class Referat(collections.Collection):
    def __len__(self) -> int:
        return len(self._raw)

    def __iter__(self) -> Iterator:
        return iter(self._raw)

    def __contains__(self, __x: object) -> bool:
        return __x in self._raw

    def __init__(self, paragraphs: List[str], declare_text: Callable[[], str]):
        self._raw = paragraphs

        self._source_header_index = self._find_source_paragraph_index(check_paragraph_to_source_header)
        if not self._source_header_index:
            user_text = declare_text()
            self._source_header_index = self._find_source_paragraph_index(lambda x: x == user_text)

    def _find_source_paragraph_index(self, is_source_header):
        for i, el in enumerate(reversed(self._raw)):
            if is_source_header(el):
                return len(self._raw) - i

    def body(self) -> List[str]:
        return self._raw[:self._source_header_index]

    def sources(self) -> List[str]:
        return self._raw[self._source_header_index:]


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
        re.findall(
            r'^(?:(?:(?:[сС]писок|[иИ]спользованн)[а-я]*\s)?(?:использ[а-я]*\s)?(?:(?:[Лл]итератур|[иИ]сточник)[а-я]*\s*и?\s*)+(?:[.:])?)$',
            text, re.I)))


LINK = r'(https?://(?:[\w\-]*\.?)+(?:/[\w\d\-]*)+(?:.html)?)'
NUMBER = r'^(?:(?P<index>\d+)\s*[\.\?\)]?\s*)'
AUTHOR = r'(?P<authors>(?:\w+\,?\s+\w+\.?(?:\s*\w+\.?)?)|(?:\w\.(?:\s*\w+\.?)?\,\s*\w+))'

MAP: Dict[Any, Callable[[Sequence[Union[str, bytes]], str], SourceData]] = {
    # 1. https://address.com/path описание
    re.compile(NUMBER + LINK + r'\s(.*\s?)+?'):
        (lambda groups, original: SourceData(
            groups[2],
            int(groups[0]),
            link=groups[1],
            original=original,
        )),

    # 1. Фамилия И.О., работа / ФИО // год ...
    re.compile(NUMBER + AUTHOR + r'(.*)(?:,\s/\s?.*)(?:\s//\s)(\d{4})'):
        (lambda groups, original: SourceData(
            ' '.join([groups[1], groups[2]]),
            index=int(groups[0]),
            year=int(groups[3]),
            authors=[groups[1]],
            original=original,
            name=groups[1]
        )),

    re.compile(NUMBER + r'(\w+\s+\w\.(?:\w\.?)?,?)+\s((?:[\w\":\-.]*\s?)+).*(\d{4})'):
        (lambda groups, original: SourceData(
            ' '.join([groups[1], groups[2]]),
            int(groups[0]),
            int(groups[3]),
            original=original)
         ),

    re.compile(NUMBER + r'([\w\s«»\[\]:\-]*[Ээ]лектронный ресурс[\w\s«»\[\]:\-]*)<?' + LINK):
        (lambda groups, original: SourceData(
            groups[1],
            int(groups[0]),
            link=groups[2],
            original=original
        ))
}


def try_build_source(paragraph: str):
    for reg, builder in MAP.items():
        res = re.match(reg, paragraph)
        if res:
            groups = res.groups()
            try:
                print(reg.pattern)
                return builder(groups, paragraph)
            except ValueError:
                print(reg.pattern, paragraph)


def find_missing_src(file_path, callback=lambda x, y: None, declare_text: Callable[[], str] = None, **kwargs):
    """
    :param declare_text: функция точного поиска заголовка списка исопльзованной литературы
    :param file_path: str путь к файлу
    :param callback: Callable[str, int[0:100]] принимает строку о текущей задаче и число с текущим процентом выполнения
    :param kwargs:
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
        document = Referat(
            list(map(lambda x: x.strip(), filter(None, process(file_path).split('\n')))),
            declare_text=declare_text,
        )

        sources = []
        len_body = len(document.sources())
        if not len_body:
            raise NoSourcesException()

        for index, paragraph in enumerate(document.sources()):
            callback('Поиск источников', round(index * 100 / len_body))
            if not paragraph:
                continue

            source = try_build_source(paragraph)
            if source:
                source.find_links(document)
                sources.append(source)

    callback("Завершение", 100)
    return sources
