import re, string
import nltk
from nltk.tokenize import word_tokenize
from Atom import TextPosition, TablePosition, AtomType
import enchant
from smatch import *
import math
import numpy

dict = enchant.Dict('en_US')
result_table_name = set(['performance', 'performances', 'results', 'result'])
example_table_name = set(['example', 'examples'])
data_table_name = set(['corpus', 'statistics'])

non_data_section_name = set(
    ['introduction', 'motivation', 'acknowledgments', 'summary', 'related', 'rule', 'rules', 'feature', 'features',
     'discussion', 'methods', 'method', 'conclusion', 'model', 'models', 'approach', 'algorithm', 'algorithms'])
possible_data_section_name = set(['experiment', 'experiments', 'statistics'])
data_section_name = set(['data', 'experimental setup', 'setting', 'settings'])

metric_set = set(
    [u'f1', u'precision', u'recall', u'accuracy', u'time(sec)', u'perplexity', u'wer', u'aer', u'atec', u'bewt',
     u'bewt_e', u'bleu', u'bleu4', u'bleu-4', u'cbleu', u'char bleu', u'bleu1', u'bleu-1', u'badger', u'bkars',
     u'charbleu', u'dcu-lfg', u'hmeant', u'hter', u'hyter', u'iqmt', u'meant', u'meteor', u'mt-mncd', u'mt-ncd',
     u'nist', u'sepia', u'sempos', u'tec', u'ter', u'pair-wise ter', u'terp', u'tesla', u'tine', u'spearman\u2019s rho',
     u'cohen\u2019s kappa'])


def is_data_position(position, document):
    if isinstance(position, TextPosition):
        if position.subsection_id is not None and position.subsection_id != -1:
            subsection_title_words = set(
                replace_punctuation(document.subsections[position.subsection_id].title.lower()).split())
            if subsection_title_words.intersection(data_section_name):
                return 1.0
            elif subsection_title_words.intersection(possible_data_section_name):
                return 0.9
            elif subsection_title_words.intersection(non_data_section_name):
                return 0.1
        for section in document.sections:
            if section.index == position.section_id:
                section_title_words = set(replace_punctuation(section.title.lower()).split())
                if section_title_words.intersection(data_section_name):
                    return 1.0
                elif section_title_words.intersection(possible_data_section_name):
                    return 0.9
                elif section_title_words.intersection(non_data_section_name):
                    return 0.1
    elif isinstance(position, TablePosition):
        if is_data_table(document.tables[position.table_id]):
            return 0.95
        elif is_result_table(document.tables[position.table_id]):
            return 0.2
        elif is_example_table(document.tables[position.table_id]):
            return 0.2
    return 0.5


def is_related_work(position, document):
    if isinstance(position, TextPosition):
        if position.subsection_id is not None and position.subsection_id != -1:
            subsection_title = document.subsections[position.subsection_id].title.lower()
            if 'related' in subsection_title:
                return True
        for section in document.sections:
            if section.index == position.section_id:
                section_title = section.title.lower()
                if 'related' in section_title:
                    return True
    return False


def is_result_table(table):
    if set(replace_punctuation(table.caption.lower()).split()).intersection(result_table_name):
        return True
    if set(replace_punctuation(table.caption.lower()).split()).intersection(metric_set):
        return True
    for row in table.cells:
        if metric_set.intersection(set(row)):
            return True
    return False


def is_example_table(table):
    if set(replace_punctuation(table.caption.lower()).split()).intersection(example_table_name):
        return True
    return False


def is_data_table(table):
    if set(replace_punctuation(table.caption.lower()).split()).intersection(data_table_name):
        return True
    return False


def replace_punctuation(text):
    text = text.encode('ascii', 'ignore')
    replace_punctuation = string.maketrans(string.punctuation, ' ' * len(string.punctuation))
    text = text.lower().translate(replace_punctuation)
    return text


def lower_tokenize_nltk(sentence):
    return word_tokenize(sentence.lower())


def valid_word(input_string):
    return dict.check(input_string)


def tokenize_digit(sentence):
    return [x for x in re.split('(\d+)|\s', sentence) if (x is not None and x is not '')]


def find_overlap(string, llist, ignorecase=True):
    if string is None:
        return list()
    if ignorecase:
        l = set([x.lower() for x in llist if x is not None]).intersection(string.lower().split())
    else:
        l = set(llist).intersection(string.split())
    return list(l)


def find_substring(string, llist, ignorecase=True):
    if ignorecase:
        substring = set([x for x in llist if x is not None and x.lower() in string.lower()])
    else:
        substring = set([x for x in llist if x is not None and x in string])
    return substring


def find_substring_lang_pair(string, lang_pair, ignorecase=True):
    langs = lang_pair.split('_')
    lang1 = langs[0]
    lang2 = langs[1]
    if ignorecase:
        if lang1.lower() in string.lower() and lang2.lower() in string.lower():
            return set([lang_pair])
            # substring = set([x for x in llist if x is not None and x.lower() in string.lower()])
    else:
        if lang1 in string and lang2 in string:
            return set([lang_pair])
            # substring = set([x for x in llist if x is not None and x in string])
    return set([])


# substring


def find_pattern(string, pattern, group_list):
    pattern_found = list()

    for mo in pattern.finditer(string):
        pattern_found.append(tuple([mo.group(x) for x in group_list]))

    return pattern_found


def find_patterns(string, patterns, group_list):
    pattern_found = list()

    for pattern in patterns:
        pattern_found.extend(find_pattern(string, pattern, group_list))

    return pattern_found


numerics_pattern_in_text = re.compile("\s+([+-]?[0-9]([0-9]*,?)+\.?[0-9]*%?)\s+")
numerics_pattern_standalone = re.compile("([+-]?[0-9]([0-9]*,?)+\.?[0-9]*%?)")


def find_numerics_in_text(string):
    return find_pattern(string, numerics_pattern_in_text, [0])


def find_numerics_standalone(string):
    return find_pattern(string, numerics_pattern_standalone, [0])


def traverse_text(document, ignorecase, match_function, *args):
    match_list = list()
    for section in document.sections:
        if section.title is None:
            continue
        text = section.title if not ignorecase else section.title.lower()
        matches = [(string, TextPosition(document, section.index, None, -1)) for string in match_function(text, *args)]
        match_list.extend(matches)
        for paragraph in section.paragraphs:
            for sentence in paragraph.sentences:
                if sentence.text is None:
                    continue
                text = sentence.text if not ignorecase else sentence.text.lower()
                matches = [(string, TextPosition(document, section.index, None, sentence.document_id)) for string in
                           match_function(text, *args)]
                match_list.extend(matches)
        for subsection in section.subsections:
            if subsection.title is None:
                continue
            text = subsection.title if not ignorecase else subsection.title.lower()
            matches = [(string, TextPosition(document, section.index, subsection.index, -1)) for string in
                       match_function(text, *args)]
            match_list.extend(matches)
            for paragraph in subsection.paragraphs:
                for sentence in paragraph.sentences:
                    if sentence.text is None:
                        continue
                    text = sentence.text if not ignorecase else sentence.text.lower()
                    matches = [(string, TextPosition(document, section.index, subsection.index, sentence.document_id))
                               for string in match_function(text, *args)]
                    match_list.extend(matches)
    return match_list


def traverse_tables(document, ignorecase, match_function, *args):
    match_list = list()
    for table_id, table in document.tables.items():
        for index, cell in enumerate(table.head):
            if cell is None:
                continue
            text = cell if not ignorecase else cell.lower()
            matches = [(string, TablePosition(document, table.id, 0, index)) for string in match_function(text, *args)]
            match_list.extend(matches)
        for row_index, row in enumerate(table.body):
            for column_index, cell in enumerate(row):
                if cell is None:
                    continue
                text = cell if not ignorecase else cell.lower()
                matches = [(string, TablePosition(document, table.id, row_index, column_index)) for string in
                           match_function(text, *args)]

                match_list.extend(matches)
        text = table.caption if not ignorecase else table.caption.lower()
        matches = [(string, TablePosition(document, table.id, caption=True)) for string in match_function(text, *args)]
        match_list.extend(matches)
    return match_list


def is_integer(x):
    try:
        int(x)
        return True
    except ValueError:
        return False


def is_numeric(x):
    if numerics_pattern_standalone.match(x):
        return True
    else:
        return False


def cosine_similarity(v1, v2):
    dot = sum([x * y for x, y in zip(v1, v2)])
    v1_norm = math.sqrt(sum([x * x for x in v1]))
    v2_norm = math.sqrt(sum([x * x for x in v2]))

    if v1_norm == 0 or v2_norm == 0:
        return 0.0
    return float(dot) / (v1_norm * v2_norm)


def print_aggStat(agg_stata, printStd=True):
    print "====================aggregate statistics over data================="
    print "data point length %d" % len(agg_stata.values()[0])
    for k in agg_stata:
        v = agg_stata[k]
        if printStd:
            print (
            "%s & %.2f& %.2f " % (k, numpy.mean(map(lambda x: float(x), v)), numpy.std(map(lambda x: float(x), v))))
        else:
            print ("%s & %.2f " % (k, numpy.mean(map(lambda x: float(x), v))))


def print_ratio_aggStat(agg_stat, printStd=True):
    print "====================aggregate statistics over data================="
    print "data point length %d" % len(agg_stat.values()[0])
    for k in agg_stat:
        if k.startswith("no_"):
            pass
        else:
            v = agg_stat[k]
            v_no = agg_stat['no_' + k]
            if printStd:
                print ("%s & %.2f & %.2f " % (k, (numpy.mean(map(lambda x: float(x), v))
                                                  / (
                numpy.mean(map(lambda x: float(x), v) + numpy.mean(map(lambda x: float(x), v_no))))),
                                              sum(v) + sum(v_no)


                ))
