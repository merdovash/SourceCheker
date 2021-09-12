import re
import zipfile
from xml.etree import ElementTree as ET

from docx2txt.docx2txt import qn, xml2text


def xml2text_endnote(xml):
    """
    A string representing the textual content of this run, with content
    child elements like ``<w:tab/>`` translated to their Python
    equivalent.
    Adapted from: https://github.com/python-openxml/python-docx/
    """
    text = u''
    root = ET.fromstring(xml)

    for child in root.iter():
        if child.tag == qn('w:t'):
            t_text = child.text
            text += t_text if t_text is not None else ''
        elif child.tag == qn('w:endnote') and int(child.attrib.get(qn('w:id'), 0)) > 0:
            text += f"\n{child.attrib[qn('w:id')]}. "
    return text


def process(docx):
    text = u''

    # unzip the docx in memory
    with zipfile.ZipFile(docx) as zipf:
        filelist = zipf.namelist()

        # get header text
        # there can be 3 header files in the zip
        header_xmls = 'word/header[0-9]*.xml'
        for fname in filelist:
            if re.match(header_xmls, fname):
                text += xml2text(zipf.read(fname))

        # get main text
        doc_xml = 'word/document.xml'
        text += xml2text(zipf.read(doc_xml))

        # get footnotes
        if 'word/endnotes.xml' in filelist:
            text += xml2text_endnote(zipf.read('word/endnotes.xml'))

        # get footer text
        # there can be 3 footer files in the zip
        footer_xmls = 'word/footer[0-9]*.xml'
        for fname in filelist:
            if re.match(footer_xmls, fname):
                text += xml2text(zipf.read(fname))

    return text.strip()
