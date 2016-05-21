'''
Created on Aug 28, 2014
this is class to represent structured information from the paper. 
this is the output format from final Linker system, as well as from survey response.
@author: echoi
'''
from enum import Enum

from amr_util import parse_to_data_amr, parse_to_result_amr, parse_to_full_amr

CompositionType = Enum('CompositionType', 'survey baseline system')
LinkType = Enum('LinkType', 'result_traindata result_testdata result_exp result_atom data_atom')


class Composition(object):
    def __init__(self, docid, atoms, data_list, result_list, exp_list, composition_type):
        self.docid = docid
        self.atoms = atoms
        self.links = list()
        self.data_list = data_list
        self.result_list = result_list
        self.exp_list = exp_list
        self.comp_type = composition_type
        self.amr = None
        self.amr = parse_to_full_amr(atoms, data_list, result_list, exp_list)
        self.data_amr = parse_to_data_amr(atoms, data_list.values())
        self.result_amr = parse_to_result_amr(atoms, result_list)

    def __repr__(self):
        return "Composition(docid=%s,atoms={%r},data_list={%r},result_list={%r},exp_list={%r})" % \
               (self.docid, [x for x in sorted(self.atoms)],
                [x for x in sorted(self.data_list)],
                [x for x in sorted(self.result_list)],
                [x for x in sorted(self.exp_list)])

    def __hash__(self):
        return hash(self.__repr__())

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        output_str = 'Composition for %s\n' % self.docid
        if len(self.result_list)==0:
            output_str+="########EMPTY_COMPOSITION#######"
        output_str+="\nData:\n\t"
        for data in self.data_list.values():
            output_str += str(data) + '\n\t'
        output_str += '\nResult:\n\t'
        for result in self.result_list:
            output_str += str(result) + '\n\t'
        output_str += '\nExpr:\n\t'
        for experiment in self.exp_list.values():
            output_str += str(experiment) + '\n\t'
        return output_str

    def data_string(self):
        output_str = 'Composition for %s\n\nData:\n\t' % self.docid
        for data in self.data_list.values():
            output_str += str(data) + '\n\t'
        return output_str

    # only applies to survey-created composition, check the atom can be found in the pre-processed pdf file
    def is_default_loc(self, atom_type):
        not_found_atom=0
        found_atom=0
        for atom in self.atoms:
            if atom.atom_type==atom_type:
                if str(atom.position) == 'default_position' and atom.normalized_value != '':
                    not_found_atom += 1
                else:
                    found_atom += 1
        return found_atom, not_found_atom

class Data(object):
    def __init__(self, d_id, usage, d_type, name, size, lang):
        self.dataid = d_id
        self.usage = usage
        self.data_type = d_type
        # should be atom, or list of atoms. 
        self.lang = lang
        self.name = name
        self.size = size
        self.atoms = [lang, name, size]

    def __repr__(self):
        return stdout_encode("Data(usage=%s,type=%s,lang={%s},name={%s},size={%s})" % \
                             (self.usage,
                              self.data_type,
                              # atoms
                              self.lang,
                              self.name,
                              self.size))

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if isinstance(other, Data):
            if self.usage == other.usage \
                    and self.data_type == other.data_type \
                    and self.lang == other.lang \
                    and self.name == other.name \
                    and self.size == other.size:
                return True
        return False

    def __str__(self):
        return 'id:%s,\tname:%s,\tusage:%s,\ttype:%s,\tlang:%s,\tsize:%s' % \
               (self.dataid,
                self.name.value,
                self.usage,
                self.data_type,
                self.lang.value,
                self.size.value if self.size is not None else None)


class Result(object):
    def __init__(self, exp, train_data, test_data, sys_name, metric, value):
        # should be atom
        self.value = value
        self.metric = metric
        self.sys_name = sys_name
        # should be a data
        self.test_data = test_data
        # should be a list of data
        self.train_data = train_data
        # should be experiment
        self.exp = exp

    def __repr__(self):
        return stdout_encode("Result(value={%r},metric={%r},sys_name={%r},test_data={%r},training_data={%r},exp={%r})" % \
                             (self.value,
                              self.metric,
                              self.sys_name,
                              self.test_data,
                              sorted(self.train_data) if self.train_data is not None else None,
                              self.exp))

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if isinstance(other, Result):
            return (self.value == other.value) and \
                   (self.metric == other.metric) and \
                   (self.sys_name == other.sys_name) and \
                   sorted(self.train_data) == sorted(other.train_data) and \
                   (self.test_data == other.test_data) and \
                   (self.exp == other.exp)
        else:
            return False

    def __str__(self):
        return 'Result Value:%s,\tMetric:%s,\tSystem Name:%s,\tTest Data:%s,\tTrain Data:%s' % \
               (self.value.value,
                self.metric.value,
                self.sys_name.value,
                self.test_data.dataid if self.test_data is not None else None,
                [x.dataid if x is not None else None for x in
                 sorted(self.train_data)] if self.train_data is not None else None)


class Experiment(object):
    def __init__(self, eid, goal, method):
        self.id = eid
        # should be atom
        self.goal = goal
        self.method = method

    def __repr__(self):
        return stdout_encode("Experiment(id={%d},goal={%s},method={%s})" % \
                             (self.id, self.goal.normalized_value,
                              self.method.normalized_value))

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if isinstance(other, Experiment):
            return (self.goal == other.goal) and \
                   (self.method == other.method)
        else:
            return False

    def __str__(self):
        return 'id:%d, goal:%s, method:%s' % \
               (self.id, self.goal.normalized_value, self.method.normalized_value)


def stdout_encode(u):
    return u.encode('ascii', 'ignore')
