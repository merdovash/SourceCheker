import re
import os.path
from datetime import datetime

from docx import Document

# Настройки
MAX_ERRORS = 3  # Макс. кол-во ошибок для остановки поиска  [3]
MIN_LENGTH = 14  # Миним. длина источника   [14]
MIN_STAGE = 2  # Кол-во заголовков списка [2, но иногда может быть 1]


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


def find_missing_src(file_path, callback=lambda x, y: None, min_year=None):
    """
    TODO возвращает объект с полями:
        - sources: List - список источников
            - text: str - текст источника
            - year: int - год источника
            - has_link: bool - есть ли ссылка на этот источник
            - paragraphs: List[str] - список параграфов, имеющих ссылки на этот источник
        - author: List[str, str, str] - автор работы
        - year: int - год написания работы

    TODO извлекать даты  с помощью '[1-2][0-9]{3}' => 1000-2999

    :param min_year: int минимальный год
    :param file_path: str путь к файлу
    :param callback: Callable[str, int[0:100]] принимает строку о текущей задаче и число с текущим процентом выполнения
    :return: Tuple[List[str], List[int]] возвращает список всех источников и список индексов источников на которые
    есть ссылки
    """

    if not os.path.isfile(file_path):
        return None, None
    else:

        document = Document(file_path)
        sources = []
        wrong = []
        stage = 0
        errors = 1

        paragraphs = document.paragraphs

        for index, paragraph in enumerate(paragraphs):
            callback('Чтение файла', round(index * 10 / len(paragraphs)))
            # Нахождение заголовков
            if stage < MIN_STAGE:
                if "список" in paragraph.text.lower():
                    if ("литератур" in paragraph.text.lower()) or ("источник" in paragraph.text.lower()):
                        stage += 1

            # Нахождение источников
            elif stage == MIN_STAGE:
                numbers = [int(s) for s in re.findall(r'\b\d+\b', paragraph.text)]
                is_fine = False
                # Проверка на наличие даты
                for number in numbers:
                    if number > min_year:
                        sources.append(paragraph.text)
                        is_fine = True
                        break
                # Проверка формата
                if not is_fine:
                    if "// " in paragraph.text:
                        sources.append(paragraph.text)
                    elif paragraph.style.name == "List Paragraph" and len(paragraph.text) > MIN_LENGTH:
                        sources.append(paragraph.text)
                    else:
                        errors += 1
                        wrong.append(paragraph.text)
                        if errors > MAX_ERRORS:
                            break

    # Проверка на наличие ссылок
    count = 0
    lacks = []

    for index, source in enumerate(sources):
        count += 1
        is_fine = False
        for paragraph_index, paragraph in enumerate(document.paragraphs):
            callback('Проверка ссылок',
                     10 + round((index * len(paragraphs) + paragraph_index) * 90 / (len(sources) * len(paragraphs))))
            link1 = "[" + str(count) + "]"
            link2 = "[" + str(count) + ","
            if link1 in paragraph.text or link2 in paragraph.text:
                is_fine = True
                break
        if not is_fine:
            lacks.append(count)

    callback("Завершение", 100)
    return sources, lacks


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
