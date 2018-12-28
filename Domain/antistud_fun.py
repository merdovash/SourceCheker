from docx import Document
import re
import os.path


# Настройки
LAST_DATE = 1980    # Миним. дата источника     [1980, стариков мы не любим]
MAX_ERRORS = 3      # Макс. кол-во ошибок для остановки поиска  [3]
MIN_LENGTH = 14     # Миним. длина источника   [14]
MIN_STAGE = 2       # Кол-во заголовков списка [2, но иногда может быть 1]


def findMissingSrc(path, callback):

    if not os.path.isfile(path):
        return None, None
    else:

        document = Document(path)
        results = []
        wrong = []
        stage = 0
        count = 0
        errors = 1

        paragraphs = document.paragraphs

        for index, para in enumerate(paragraphs):
            callback('Чтение файла', round(index*10/len(paragraphs)))
            # Нахождение заголовков
            if stage < MIN_STAGE:
                if "список" in para.text.lower():
                    if ("литератур" in para.text.lower()) or ("источник" in para.text.lower()):
                        stage += 1

            # Нахождение источников
            elif stage == MIN_STAGE:
                numbers = [int(s) for s in re.findall(r'\b\d+\b', para.text)]
                itsFine = False
                # Проверка на наличие даты
                for n in numbers:
                    if n > LAST_DATE:
                        results.append(para.text)
                        itsFine = True
                        break
                # Проверка формата
                if itsFine == False:
                    if "// " in para.text:
                        results.append(para.text)
                    elif para.style.name == "List Paragraph" and len(para.text)>MIN_LENGTH:
                        results.append(para.text)
                    else:
                        errors += 1
                        wrong.append(para.text)
                        if errors > MAX_ERRORS:
                            break

    # Проверка на наличие ссылок
    count = 0
    lacks = []

    for index, res in enumerate(results):
        count += 1
        itsFine = False
        for p_index, p in enumerate(document.paragraphs):
            callback('Проверка ссылок',
                     10 + round((index * len(paragraphs)+p_index)*90 / (len(results) * len(paragraphs))))
            link1 = "["+str(count)+"]"
            link2 = "["+str(count)+","
            if link1 in p.text or link2 in p.text:
                itsFine = True
                break
        if itsFine == False:
            lacks.append(count)

    callback("Завершение", 100)
    return results, lacks


if __name__ == "__main__":

    while True:
        
        print("\n")
        path = input("Path? ")
        
        results, missing = findMissingSrc(path)
        # print (results)
        print (missing)

        ch = input("\nOpen another file? (y/n): ")

        if ch.lower() == "n":
            break
    