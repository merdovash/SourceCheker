import re
import os.path
from datetime import datetime

from docx import Document

# Настройки
MAX_ERRORS = 3  # Макс. кол-во ошибок для остановки поиска  [3]
MIN_LENGTH = 14  # Миним. длина источника   [14]
MIN_STAGE = 2  # Кол-во заголовков списка [2, но иногда может быть 1]


class NoSourcesException(Exception):
    pass


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
    text = paragraph.text.lower()
    if len(re.findall('[0-9]+(\s)*[CСcс]\.', text)) > 0:
        # 52 c.
        return True

    if len(re.findall('[CСcс]\.(\s)*[0-9]+', text)):
        # c. 52
        return True

    if len(re.findall('с\.(\s){0,2}[0-9]{1,4}(\s){0,2}-(\s){0,2}[0-9]{1,4}', text)):
        # c. 52 – 57
        return True

    if '//' in paragraph.text:
        return True

    if get_year(paragraph.text):
        return True

    return False


def find_links(source_index, document, max_paragraph=None):
    if max_paragraph is not None:
        paragraphs = document.paragraphs[:max_paragraph]
    else:
        paragraphs = document.paragraphs

    regexp = re.compile('\[([0-9],\s{0,2}){0,4}[' + str(source_index) + '](,\s{0,2}[0-9]){0,4}\]')

    links = []

    for index, paragraph in enumerate(paragraphs):
        if regexp.findall(paragraph.text):
            links.append(paragraph.text)

    return links


def find_missing_src(file_path, callback=lambda x, y: None, min_year=1000):
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
    :return: Tuple[List[str], List[int], List[int]]
        возвращает список всех источников
        и список индексов источников на которые есть ссылки
        и список индексов устаревших источников
    """

    if not os.path.isfile(file_path):
        return None, None
    else:

        document = Document(file_path)
        sources = []
        old = []
        links = []
        lacks = []

        paragraphs = document.paragraphs
        sources_header_index = find_sources(document)
        if sources_header_index is None:
            raise NoSourcesException()
        sources_paragraphs = paragraphs[sources_header_index:]

        for index, paragraph in enumerate(sources_paragraphs, sources_header_index):
            callback('Поиск источников', round(index * 10 / len(sources_paragraphs)))
            if is_source(paragraph):
                sources.append(paragraph)
                year = get_year(paragraph.text)
                if year is not None and year < min_year:
                    old.append(len(sources) - 1)

    for index, source in enumerate(sources):
        callback('Поиск ссылок', round(index * 90 / len(sources)))
        source_links = find_links(index + 1, document, sources_header_index)
        if len(source_links) == 0:
            lacks.append(index)
        links.append(source_links)

    callback("Завершение", 100)
    return [x.text for x in sources], lacks, old


def run():
    while True:

        print("\n")
        input_file_path = input("Path? ")

        list_of_sources, missing_sources = find_missing_src(input_file_path)
        print(list_of_sources)
        print(missing_sources)

        input_user_action = input("\nOpen another file? (y/n): ")

        if input_user_action.lower() == "n":
            break


if __name__ == "__main__":
    run()
