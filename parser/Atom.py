import re
from enum import Enum

AtomType = Enum('Atom',
                'language language_pair data_name data_size data_purpose_train data_purpose_tune data_purpose_test result_value result_metric result_name exp_goal exp_method')
data_atom_type = [AtomType.language, AtomType.language_pair, AtomType.data_name, AtomType.data_size]
result_atom_type = [AtomType.result_value, AtomType.result_metric, AtomType.result_name]
exp_atom_type = [AtomType.exp_goal, AtomType.exp_method]

# ## definitely needs to be modified later. currently normalizing values into some format
# language data_name data_size result_value result_metric result_name

numerics_pattern_in_text = re.compile("\s+([+-]?[0-9]([0-9]*,?)+\.?[0-9]*%?)\s+")
numerics_pattern_standalone = re.compile("([+-]?[0-9]([0-9]*,?)+\.?[0-9]*%?)")

def is_numeric(x):
    if numerics_pattern_standalone.match(x):
        return True
    else:
        return False


def normalize_atom_value(value_string, atom_type):
    if not value_string:
        return value_string

    value_string = value_string.strip().lower()

    if atom_type == AtomType.data_size:
        if 'sentence pairs' in value_string:
            value_string = value_string.replace('sentence pairs', 'sentence')
        elif 'sentence pair' in value_string:
            value_string = value_string.replace('sentence pair', 'sentence')
        elif 'sentences' in value_string:
            value_string = value_string.replace('sentences', 'sentence')
        elif 'sentence' not in value_string and 'sents' in value_string:
            value_string = value_string.replace('sents', 'sentence')
        elif 'sentence' not in value_string and 'sent' in value_string:
            value_string = value_string.replace('sent', 'sentence')

        elif 'words' in value_string:
            value_string = value_string.replace('words', 'word')
        elif 'tokens' in value_string:
            value_string = value_string.replace('tokens', 'word')
        elif 'token' in value_string:
            value_string = value_string.replace('token', 'word')

        tokens = value_string.split()
        for index, token in enumerate(tokens):

            if is_numeric(token):
                tokens[index] = token.replace(',', '')

            if index > 0 and is_numeric(tokens[index - 1]):
                if token == "billion":
                    tokens[index - 1] = tokens[index - 1] + '000000000'
                    tokens[index] = ''

                elif token == "million":
                    tokens[index - 1] = tokens[index - 1] + '000000'
                    tokens[index] = ''

                elif token == "thousand":
                    tokens[index - 1] = tokens[index - 1] + '000'
                    tokens[index] = ''

            if token.endswith("b") and is_numeric(token[:-1]):
                tokens[index] = token[:-1] + '000000000'

            elif token.endswith("m") and is_numeric(token[:-1]):
                tokens[index] = token[:-1] + '000000'

            elif token.endswith("k") and is_numeric(token[:-1]):
                tokens[index] = token[:-1] + '000'

        value_string = ' '.join(x for x in tokens if x != '')
        
    if atom_type == AtomType.data_name:
        value_string = value_string.replace('unknown', '')
        value_string = value_string.replace('corpus', '')
        value_string = value_string.replace('corpora', '')
        value_string = value_string.replace('data', '')
        value_string = value_string.replace('-',' ')
        value_string = value_string.replace('set','')
        value_string = value_string.strip()

    if atom_type == AtomType.language:
        pass

    if atom_type == AtomType.language_pair:
        elems= value_string.strip().split("_")
        value_string = elems[0]+"_"+elems[1] if(elems[0]>elems[1]) else elems[1]+"_"+elems[0]
    if atom_type == AtomType.result_name:
        pass

    if atom_type == AtomType.result_value:

        value_string = value_string.replace(',', '')
        value_string = value_string.replace('%', '')

        if value_string.endswith("billion"):
            value_string = value_string.replace("billion", '000000000')
        elif value_string.endswith("b"):
            value_string = value_string.replace("b", '000000000')
        elif value_string.endswith("m"):
            value_string = value_string.replace("m", '000000')
        elif value_string.endswith("million"):
            value_string = value_string.replace("million", '000000')
        elif value_string.endswith("k"):
            value_string = value_string.replace("k", '000')
        elif value_string.endswith("thousand"):
            value_string = value_string.replace("thousand", '000')

        if '.' in value_string:
            value_string = value_string.rstrip('0')

    return value_string.strip()


class Atom(object):
    def __init__(self, atom_value, atom_type, position):
        self.value = atom_value
        self.atom_type = atom_type
        self.position = position
        self.normalized_value = normalize_atom_value(atom_value, atom_type)

    def __repr__(self):
        return stdout_encode("Atom(normalized_value=%s,type=%s)" % (self.normalized_value, self.atom_type))

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if isinstance(other, Atom):
            return (self.normalized_value == other.normalized_value) and \
                   (self.atom_type == other.atom_type)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return stdout_encode('Value:%s,  Normalized:%s,  Type:%s,  Position:%s' % \
                             (self.value,
                              self.normalized_value,
                              self.atom_type,
                              self.position))


class UniqueAtom(Atom):
    def __init__(self, atom):
        super(UniqueAtom, self).__init__(atom.value, atom.atom_type, atom.position)
        self.related_atoms = set()

    def __repr__(self):
        return stdout_encode("UniqueAtom(normalized_value=%s,type=%s,position=%r)" % (self.normalized_value, self.atom_type, self.position))

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if isinstance(other, UniqueAtom):
            return (self.normalized_value == other.normalized_value) and \
                   (self.atom_type == other.atom_type) and \
                   (self.position == other.position)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return stdout_encode('Value:%s,  Normalized:%s,  Type:%s,  Position:%s' % \
                             (self.value,
                              self.normalized_value,
                              self.atom_type,
                              self.position))


class Position(object):
    def __init__(self, document):
        self.document = document

    def __str__(self):
        return 'default_position'

    def content_at_position(self):
        return 'No Content at Default Position'


class TablePosition(Position):
    def __init__(self, document, table_id, row=None, column=None, caption=False):
        super(TablePosition, self).__init__(document)
        self.table_id = table_id
        self.row = row
        self.column = column
        self.caption = caption

    def __repr__(self):
        return stdout_encode(
            "TablePosition(table_id=%s,row=%s,column=%s,caption=%s)" % (self.table_id, self.row, self.column, self.caption))

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if isinstance(other, TablePosition):
            return (self.table_id == other.table_id) and \
                   (self.row == other.row) and \
                   (self.column == other.column) and \
                   (self.caption == other.caption)
        else:
            return False


    def __str__(self):
        if (self.caption):
            return 'Table ID:%s,caption' % \
                   (self.table_id)
        else:
            return 'Table ID:%s,Row ID:%s,Column ID:%s' % \
                   (self.table_id,
                    self.row,
                    self.column)

    def content_at_position(self):
        content_str = ''
        content_str += '\ttable %s\n' % ( self.document.tables[self.table_id].caption)
        content_str += self.document.tables[self.table_id].pretty_print()
        return stdout_encode(content_str)


class TextPosition(Position):
    def __init__(self, document, section_id, subsection_id, sentence_id):
        super(TextPosition, self).__init__(document)
        self.section_id = section_id
        self.subsection_id = subsection_id
        self.sentence_id = sentence_id

    def __repr__(self):
        return stdout_encode(
            "TablePosition(section_id=%s,subsection_id=%s,sentence_id=%s)" % (
                self.section_id, self.subsection_id, self.sentence_id))

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if isinstance(other, TextPosition):
            return (self.section_id == other.section_id) and \
                   (self.subsection_id == other.subsection_id) and \
                   (self.sentence_id == other.sentence_id)
        else:
            return False

    def __str__(self):
        return 'section_id:%s,subsection_id:%s,sentence_id:%s' % \
               (self.section_id,
                self.subsection_id,
                self.sentence_id)

    def content_at_position(self):
        content_str = ''
        for section in self.document.sections:
            if section.index == self.section_id:
                content_str += '\tSect. %d: %s\n' % (section.index, section.title)
                break
        for sentence in self.document.sentences:
            if self.sentence_id == sentence.document_id:
                content_str += '\tSent. %d: %s' % (sentence.document_id, sentence.text)
        return stdout_encode(content_str)


def stdout_encode(u):
    return u.encode('ascii', 'ignore')
