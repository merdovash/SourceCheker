import re
from datetime import datetime


def get_year_from_source_text(text):
    """
    Допущения:
        - год это большее число из всех чисел текста в интервале 1000-2999
        - год меньше текущего года

    :param text: текст
    :return: год
    """

    year = re.findall('[1-2][0-9]{3}', text)
    year = map(lambda x: int(x), year)
    year = list(filter(lambda x: x <= datetime.now().year, year))

    have_any_years = len(year) > 0
    if have_any_years:
        return max(year)
    return None


def get_missing_sources(sources, missing_indexes):
    missing_links = []
    for index, item in enumerate(sources):
        if index in missing_indexes:
            missing_links.append('{}. {}'.format(index + 1, item))

    return missing_links
