from lxml import etree as ET
from tabulate import tabulate
import numpy as np
from utils import *
from enum import Enum

TableType = Enum('TableType', 'result example data')
empty_cell = "*&EMPTY&*"
merge_delimiter = "#@#@"


def parse_xml_file(filename):
    try:
        with open(filename) as f:
            parser = ET.XMLParser(encoding="utf-8")
            root = ET.fromstring(f.read().encode('utf-8'), parser=parser)
            return root
    except:
        print 'Error parsing XML from file %s' % filename
        raise


def parse_document_content(document_xml):
    root = document_xml
    # Metadata
    filename = root.xpath('filename')[0].text if len(root.xpath('filename')) >= 1 else None
    title = root.xpath('title')[0].text if len(root.xpath('title')) >= 1 else None
    authors = [author.text for author in root.xpath('authors//author') if author.text is not None]

    metadata = Metadata(filename, title, authors)

    # Sections
    sections = list()
    for xml_section in root.xpath('content//sections//section'):
        section_index = int(xml_section.xpath('index')[0].text) if len(xml_section.xpath('index')) >= 1 and \
                                                                   xml_section.xpath('index')[0] is not None else None
        section_title = xml_section.xpath('title')[0].text if len(xml_section.xpath('index')) >= 1 and \
                                                              xml_section.xpath('index')[0] is not None else None

        section_paragraphs = list()
        for xml_paragraph in xml_section.xpath('paragraphs//paragraph'):
            paragraph_sentences = list()
            for xml_sentence in xml_paragraph.xpath('sentence'):
                sentence_text = xml_sentence.xpath('text')[0].text if len(xml_sentence.xpath('text')) >= 1 and \
                                                                      xml_sentence.xpath('text')[
                                                                          0] is not None else None
                doc_id = int(xml_sentence.xpath('doc_id')[0].text) if len(xml_sentence.xpath('doc_id')) >= 1 and \
                                                                      xml_sentence.xpath('doc_id')[
                                                                          0] is not None else None
                sec_id = int(xml_sentence.xpath('sec_id')[0].text) if len(xml_sentence.xpath('sec_id')) >= 1 and \
                                                                      xml_sentence.xpath('sec_id')[
                                                                          0] is not None else None
                paragraph_sentences.append(Sentence(sentence_text, doc_id, sec_id))

            section_paragraphs.append(Paragraph(paragraph_sentences))

        section_subsections = list()
        for xml_subsection in xml_section.xpath('subsections//subsection'):
            subsection_index = int(xml_subsection.xpath('index')[0].text) if len(xml_subsection.xpath('index')) >= 1 and \
                                                                             xml_subsection.xpath('index')[
                                                                                 0] is not None else None
            subsection_title = xml_subsection.xpath('title')[0].text if len(xml_subsection.xpath('index')) >= 1 and \
                                                                        xml_subsection.xpath('index')[
                                                                            0] is not None else None

            subsection_paragraphs = list()
            for xml_paragraph in xml_subsection.xpath('paragraphs//paragraph'):
                paragraph_sentences = list()
                for xml_sentence in xml_paragraph.xpath('sentence'):
                    sentence_text = xml_sentence.xpath('text')[0].text if len(xml_sentence.xpath('text')) >= 1 and \
                                                                          xml_sentence.xpath('text')[
                                                                              0] is not None else None
                    doc_id = int(xml_sentence.xpath('doc_id')[0].text) if len(xml_sentence.xpath('doc_id')) >= 1 and \
                                                                          xml_sentence.xpath('doc_id')[
                                                                              0] is not None else None
                    sec_id = int(xml_sentence.xpath('sec_id')[0].text) if len(xml_sentence.xpath('sec_id')) >= 1 and \
                                                                          xml_sentence.xpath('sec_id')[
                                                                              0] is not None else None
                    paragraph_sentences.append(Sentence(sentence_text, doc_id, sec_id))

                subsection_paragraphs.append(Paragraph(paragraph_sentences))

            section_subsections.append(Subsection(subsection_index, subsection_title, subsection_paragraphs))

        sections.append(Section(section_index, section_title, section_paragraphs, section_subsections))

    # Tables
    tables = {}
    for xml_table in root.xpath('content//tables/table'):
        table_id = int(xml_table.xpath('id')[0].text) if len(xml_table.xpath('id')) >= 1 and xml_table.xpath('id')[
                                                                                                 0] is not None else None
        source = xml_table.xpath('source')[0].text if len(xml_table.xpath('source')) >= 1 and xml_table.xpath('source')[
                                                                                                  0] is not None else None
        caption = xml_table.xpath('caption')[0].text if len(xml_table.xpath('caption')) >= 1 and \
                                                        xml_table.xpath('caption')[0] is not None else None
        reference_text = xml_table.xpath('reference_text')[0].text if len(xml_table.xpath('reference_text')) >= 1 and \
                                                                      xml_table.xpath('reference_text')[
                                                                          0] is not None else None
        page_num = int(xml_table.xpath('page_num')[0].text) if len(xml_table.xpath('page_num')) >= 1 and \
                                                               xml_table.xpath('page_num')[0] is not None else None

        head = [cell.text if cell is not None else None for cell in xml_table.xpath('head//rows//row//cell')]

        body = list()
        for xml_row in xml_table.xpath('body//rows//row'):
            row_cells = [cell.text if cell is not None else None for cell in xml_row.xpath('cell')]
            body.append(row_cells)

        tables[table_id] = Table(table_id, head, body, caption, page_num, reference_text, source)

    return Document(metadata, sections, tables)


class Document(object):
    def __init__(self, metadata, sections, tables):
        self.metadata = metadata
        self.sections = sections
        self.tables = tables
        self.sentences = []
        self.subsections={}
        for section in self.sections:
            for paragraph in section.paragraphs:
                self.sentences.extend(paragraph.sentences)
            for subsection in section.subsections:
                self.subsections[subsection.index]=subsection
                for subsection_paragraph in subsection.paragraphs:
                    self.sentences.extend(subsection_paragraph.sentences)

    # returns entire cell values in paper
    def get_result_cells(self):
        cells = []
        for table in self.tables:
            cells.extend([item for sublist in table.cells for item in sublist])
            star_cell = table.get_starred_cells()
            if (star_cell != []):
                cells.extend(star_cell)
            merged_cell = table.get_merged_cells()
            if (merged_cell != []):
                cells.extend(merged_cell)
        return filter(None, cells)

    def print_out(self):
        for section in self.sections:
            print section.title
            for paragraph in section.paragraphs:
                for sentence in paragraph.sentences:
                    print sentence.text
            for subsection in section.subsections:
                print subsection.title
                for paragraph in subsection.paragraphs:
                    for sentence in paragraph.sentences:
                        print sentence.text

        for table in self.tables:
            print '(%s, %d, %d) %s' % (table.source, table.page_num, table.id, table.caption)
            print table.reference_text
            print '\t'.join([cell if cell is not None else '' for cell in table.head])
            for row in table.body:
                print '\t'.join([cell if cell is not None else '' for cell in row])


class Metadata(object):
    def __init__(self, doc_id, title, authors):
        self.id = doc_id
        self.title = title
        self.authors = authors


class Author(object):
    def __init__(self, name, affiliation=None, email=None):
        self.name = name
        self.affiliation = affiliation
        self.email = email


class Section(object):
    def __init__(self, index, title, paragraphs, subsections):
        self.index = index
        self.title = title
        self.paragraphs = paragraphs
        self.subsections = subsections
        

class Subsection(Section):
    def __init__(self, index, title, paragraphs):
        self.index = index
        self.title = title
        self.paragraphs = paragraphs
        
class Paragraph(object):
    def __init__(self, sentences):
        self.sentences = sentences


class Sentence(object):
    def __init__(self, text, document_id, section_id):
        self.text = text
        self.document_id = document_id
        self.section_id = section_id

def get_table_type(table):
    table_type=[]
    if is_result_table(table):
        table_type.append(TableType.result)
    if is_example_table(table):
        table_type.append(TableType.example)
    if is_data_table(table):
        table_type.append(TableType.data)
    return table_type

class Table(object):
    def __init__(self, tid, head, body, caption, page_num, reference_text, source):
        self.id = tid
        self.head = head
        self.body = body
        self.caption = caption
        self.page_num = page_num
        self.reference_text = reference_text
        self.source = source
        self.cells = [head]
        self.cells.extend(body)
        self.numpy_cells = np.array(self.cells)
        self.type = get_table_type(self)
    # get starred cell
    
    def get_starred_cells(self):
        starred_cells = []
        for row in (self.numpy_cells):
            for cell in row:
                if (cell is not None and (cell.endswith("*") or cell.endswith("?"))):
                    starred_cells.append(cell.replace("*", "").replace("?", "").strip())
        return starred_cells

    # get merged cells
    def get_merged_cells(self):
        merged_cells = []
        for row in (self.numpy_cells):
            for cell in row:
                if (cell is not None and merge_delimiter in cell):
                    merged_cells.extend(cell.split(merge_delimiter))
        return merged_cells
    
    
    def pretty_print(self):
        out_txt = ''
        if (len(self.body) == 0):
            "empty table:"
        else:
           # print_str = "%s##%s" % (self.id, self.caption.encode('ascii', 'ignore'))
            #out_txt += print_str
            tabulated = "\n" + tabulate(self.cells, headers="firstrow")
          #  tabulated=''
            out_txt += tabulated
            if ("ERRINTER" in tabulated):
                out_txt += "\n TABULATE ERROR, SHOWING RAW FORM\nthead:\n"
                for header in self.head:
                    out_txt += ' '.join(header)
                out_txt += "\ntbody:\n"
                for col in self.body:
                    out_txt += ' '.join(col)
        return out_txt.replace('\n','\n\t')
    #.encode('ascii', 'ignore')
    