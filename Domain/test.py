import docx2txt

if __name__ == '__main__':


    text = docx2txt.process("../r1.docx")
    print(list(filter(None, text.split('\n'))))