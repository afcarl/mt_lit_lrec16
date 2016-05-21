'''
Created on Aug 6, 2014
@author: echoi
'''
import re
import numpy as np
import csv
from utils import *
import pickle
from collections import defaultdict

def parse_csv_to_surveyresponse(line):
    annot_elems = line
    data_list = []
    result_values = []
    goals = {}
    methods = {}
    comment=''
    diff_metric=''
    for ind in range(0, len(annot_elems)):
        if (ind == 0):
            timestamp = annot_elems[ind]
        if (ind == 1):
            first_name = annot_elems[ind]
        if (ind == 2):
            last_name = annot_elems[ind]
        if (ind == 3):
            paper_title = annot_elems[ind]
        if (ind == 4):
            pid = annot_elems[ind]
        if (ind == 5):
            for expr_goal in annot_elems[ind].split('\n'):
                for e_id in re.findall(re.compile("ID:(.*?),"), expr_goal):
                    e_id=int(e_id)
                    for k in re.findall(re.compile("paper\?: (.*?),"), expr_goal):
                        goals[e_id] = k
                    for k in re.findall(re.compile("answer: (.*?),"), expr_goal):
                        if (not (k.strip() == '')):
                            goals[e_id] = k
                    for k in re.findall(re.compile("experiments\?: (.*?),"), expr_goal):
                        methods[e_id] = k
                    for k in re.findall(re.compile("#2: (.*?),"), expr_goal):
                        if (not (k.strip() == '')):
                            methods[e_id] = k
        if (ind == 6):
            data_annot = [x.strip() for x in annot_elems[ind].split("IDe.g.,1 2:")]
            for i in range(0, len(data_annot)):
                data_line = data_annot[i].replace("\n", " ")
                data = []
                for k in re.findall(re.compile("(.*?)Usage"), data_line):
                    data.insert(0, k[:-2].strip())
                for k in re.findall(re.compile("Usagetrain test: (.*?)Type"), data_line):
                    data.insert(1, k[:-2].strip())
                for k in re.findall(re.compile("Typebitext bitext: (.*?)Name"), data_line):
                    data.insert(2, k[:-2].strip())
                for k in re.findall(re.compile("NameEuroparl NIST09: (.*?)Size"), data_line):
                    data.insert(3, k[:-2].replace("sentences", "").strip())
                for k in re.findall(re.compile("Size11k sentences 3k sentences:(.*?)Source"), data_line):
                    data.insert(4, k[:-2].strip())
                for k in re.findall(re.compile("Source LanguageCzech Czech:(.*?)Target"), data_line):
                    data.insert(5, k[:-2].strip())
                for k in re.findall(re.compile("Target LanguageEnglish English:(.*?)URL"), data_line):
                    data.insert(6, k[:-2].strip())
                for k in re.findall(re.compile("where.nist.is:(.*?),"), data_line):
                    data.insert(7, k[:-2].strip())
                for k in re.findall(re.compile("URLhttp:(.*?),"), data_line):
                    data.insert(7, k[:-2].strip())
                if (len(data) < 8 and len(data) > 0):
                    print 'survey response data parse missing element'
                elif (len(data) == 8):
                    data_list.append(data)
        if (ind == 7):
            result_annot = [x.strip().replace("\n", " ") for x in annot_elems[ind].split("Experiment ")]
            for result_line in result_annot:
                result_val = []
                
                for k in re.findall(re.compile("^ID1 1: (.*?)Train"), result_line):
                    result_val.insert(0, k.replace(",", "").strip())
                for k in re.findall(re.compile("^IDe.g.,1 1: (.*?)Train"), result_line):
                    result_val.insert(0, k.replace(",", "").strip())
                for k in re.findall(re.compile("^Type IDe.g.,1 1: (.*?)Train"), result_line):
                    result_val.insert(0, k.replace(",", "").strip())
                for k in re.findall(re.compile("\]: (.*?)Test"), result_line):
                    result_val.insert(1, k[:-2].strip().replace('[','').replace(']','').replace('.',','))
                for k in re.findall(re.compile("Test Dataset ID2 2: (.*?)System Name"), result_line):
                    result_val.insert(2, k.replace(",", "").strip())
                for k in re.findall(re.compile("System NameBaseline My-Own-System: (.*?)Metric"), result_line):
                    result_val.insert(3, k.replace(",", "").strip())
                for k in re.findall(re.compile("System NameBaseline PBMT: (.*?)Metric"), result_line):
                    result_val.insert(3, k.replace(",", "").strip())
                for k in re.findall(re.compile("MetricBLEU BLEU: (.*?)V"), result_line):
                    result_val.insert(4, k.replace(",", "").strip())
                for k in re.findall(re.compile("Value32.11 33.45: (.*?)$"), result_line):
                    result_val.insert(5, k.replace(",", "").strip())
                   # self.result_numbers.append(k.replace(",", "").strip())
                if (len(result_val) < 6 and len(result_val) > 0):
                    print 'survey response result value parse missing element '
                if (len(result_val) > 3):
                    result_values.append(result_val)
        if (ind == 8):
            diff_metric=annot_elems[8]
        if (ind == 9):
            comment = annot_elems[9]
    return SurveyResponse(pid, first_name, last_name, paper_title, goals, methods, data_list, result_values,diff_metric,comment)
    
def from_readable_to_surveyset(pretty_string_file):
    survey_response = defaultdict(list)
    f = open(pretty_string_file,'r') 
    for line in  f :
        line=line.replace("\n","")
        if line=='<SURVEYSTART>':
            goals={}
            methods={}
            data_list=[]
            result_values=[]
            paper_title=''
            first_name=''
            last_name=''
            pid=''
            in_result=False
            in_data=False
            diff_metric=''
            comment=''
        elif line=='<SURVEYEND>':
            in_result=False
            if pid!='':
                sv = SurveyResponse(pid, first_name, last_name, paper_title, goals, methods, data_list, result_values,diff_metric,comment)
                survey_response[pid].append(sv)
        elif line.startswith("id:"):
            pid = line.replace('id:','').strip()
        elif line.startswith('first_name:'):
            first_name=line.replace('first_name:','').strip()
        elif line.startswith('last_name:'):
            last_name=line.replace('last_name:','').strip()
        elif line.startswith('title:'):
            paper_title=line.replace('title:','').strip()
        elif line.startswith('goal'):
            pe = re.compile('(\w+)\s:\s(.+)')
            goal_number = re.findall(pe,line)[0][0]
            goal = re.findall(pe,line)[0][1]
            goals[int(goal_number)]=goal
        elif line.startswith('tech'):
            pe = re.compile('(\w+)\s:\s(.+)')
            tech_number = re.findall(pe,line)[0][0]
            tech = re.findall(pe,line)[0][1]
            methods[int(tech_number)]=tech
        elif line.startswith('diff_metric:'):
            diff_metric=line.replace("diff_metric:",'')
        elif line.startswith('extra:'):
            comment=line.replace('extra:','')
        elif line == '------data------':
            in_data = True
        elif line == '=====result=====':
            in_data=False
            in_result=True
        elif in_data:
            data_list.append(line.split('\t'))
        elif in_result:
            result_values.append(line.split('\t'))
    return survey_response
# a class containing survey responses.
class SurveyResponseSet():
    def __init__(self, csv_file):
        self.survey_response = {}
        with open(csv_file, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                row = [x.decode('utf-8') for x in row]
                sr = parse_csv_to_surveyresponse(row)
                if sr.pid in self.survey_response:
                    self.survey_response[sr.pid].append(sr)
                else:
                    self.survey_response[sr.pid] = []
                    self.survey_response[sr.pid].append(sr)
        # remove duplicates.
        for s_id in self.survey_response:
            responses = self.survey_response[s_id]
            non_duplicate_list = []
            annotator_name = []
            for response in responses:
                if response.first_name in annotator_name:
                    pass
                else:
                    annotator_name.append(response.first_name)
                    non_duplicate_list.append(response)
            self.survey_response[s_id] = non_duplicate_list
    def export(self, output_file_name):
        f = open(output_file_name,'wb')
        for response_id in self.survey_response:
            responses = self.survey_response[response_id]
            for response in responses:
                f.write(response.pretty_print().encode('ascii','ignore'))
        f.close()

class SurveyResponse():
    def __init__(self, pid, first_name, last_name, paper_title, goals, methods, data_list, result_values,diff_metric,comment):
        self.pid = pid
        self.first_name=first_name
        self.last_name=last_name
        self.paper_title = paper_title
        self.goals = goals
        self.methods = methods
        self.data_list = data_list
        self.result_values = result_values
        self.diff_metric=diff_metric
        self.comment=comment
        
    def pretty_print(self):
        print_str = "<SURVEYSTART>\n"
        print_str += "id:  %s\n" % self.pid
        print_str += 'title: %s\n'%self.paper_title
        print_str += "link: http://www.aclweb.org/anthology/%s\n"% self.pid
        print_str += "first_name: %s\n" % ( self.first_name)
        print_str += "last_name: %s\n"%self.last_name
        for goal_id in self.goals:
            print_str += "goal #%s : %s\n" % (goal_id, self.goals[goal_id])
        for method_id in self.methods:
            print_str += "tech #%s : %s\n" % (method_id, self.methods[method_id])
        print_str += "------data------\n"
        for data in self.data_list:
            for data_elem in data:
                print_str += data_elem + "\t"
            print_str += "\n"
        print_str += "=====result=====\n"
        for result in self.result_values:
            for result_elem in result:
                print_str += result_elem + "\t"
            print_str += "\n"
        print_str += "diff_metric:"+self.diff_metric+"\n"
        print_str += "extra:"+ self.comment+"\n"
        print_str += "<SURVEYEND>\n"
        
        return print_str
if __name__=="__main__":
    parsed_data = from_readable_to_surveyset('../annotation/eval_set.txt')  
