import requests 
from requests.exceptions import HTTPError 
import time 
import ast
import sys
import getopt
import yaml
import numpy
import pandas as pd
import hl7
import os
import datetime
from shutil import copyfile
from shutil import move
import csv
import traceback
from filelock import FileLock
from pathlib import Path
import os.path
import re
import math
print("Run start time: ", str(datetime.datetime.now()) + "\n")

script_path = os.path.dirname(os.path.abspath( __file__ ))
parent_path = os.path.abspath(os.path.join(script_path, '..'))

dbdict = {}

RLU_NOMINAL_SCORE = 350
USER_NAME=os.environ['USER']
INPUT_POOL_FILE = ""
INPUT_POOL_RESULTS_FILE = ""
MIRTH_ORDERS_DIR = ""
MIRTH_RESULTS_DIR = ""
MIRTH_ARCHIVE_DIR = ""          

def check_folders_exist():
    if not os.path.isfile(INPUT_POOL_FILE):
        sys.exit("ERROR: Does not have access to following file: " + INPUT_POOL_FILE + "\n") 

    if not os.path.isfile(INPUT_POOL_RESULTS_FILE):
        sys.exit("ERROR: Does not have access to following file: " + INPUT_POOL_RESULTS_FILE + "\n") 

    if not os.path.isdir(MIRTH_ORDERS_DIR):
        sys.exit("ERROR: Does not have access to following folder: " + MIRTH_ORDERS_DIR + "\n") 

    if not os.path.isdir(MIRTH_RESULTS_DIR):
        sys.exit("ERROR: Does not have access to following folder: " + MIRTH_RESULTS_DIR + "\n") 

    if not os.path.isdir(MIRTH_ARCHIVE_DIR):
        sys.exit("ERROR: Does not have access to following folder: " + MIRTH_ARCHIVE_DIR + "\n")

def format_for_unity(x):
    if(x<10):
        return "0"+str(x)
    else:
        return str(x)

def get_current_formatted_date():
    currentDT = datetime.datetime.now()
    if currentDT:
        data = format_for_unity(currentDT.year) +format_for_unity(currentDT.month) +format_for_unity(currentDT.month)+format_for_unity(currentDT.hour)+format_for_unity(currentDT.minute)+format_for_unity(currentDT.second)
        
        return data
    return str(currentDT)

def get_ticks(dt):
    return (dt - datetime.datetime(1, 1, 1)).total_seconds() * 10000000

class hl7update:
    
    def __init__(self, h):
        self.h = h

    def update_msh_segment(self):
        if self.h and self.h['MSH']:
            for msh_segment in self.h['MSH']:
                if msh_segment:
                    msh_segment[7] = get_current_formatted_date()
                    msh_segment[8] = ''
                    msh_segment[9][0][0] = 'ORU'
                    msh_segment[9][0][1] = 'R01'
                    msh_segment[10] = get_ticks(datetime.datetime.now())

    def update_orc_segment(self):
        if self.h and self.h['ORC']:
            for orc_segment in self.h['ORC']:
                orc_segment[1] = 'RE'

    def update_obr_segment(self):
        if self.h and self.h['OBR']:
            for obr_segment in self.h['OBR']:
                obr_segment[22] = get_current_formatted_date()
                obr_segment[25] = 'P'
                obr_segment[27] = '^^^^^R^^'

    def update_obx_segment(self):
        if self.h and self.h['OBX']:
            for obx_segment in self.h['OBX']:
                obx_segment[2] = 'ST'
                obx_segment[11] = 'P'
                obx_segment[14] = get_current_formatted_date()
                if(len(obx_segment)==19):
                    obx_segment.append(obx_segment[14])
                elif(len(obx_segment)>=19):
                    obx_segment[19] = obx_segment[14]
   
    def update_obx_seg_containing_gene(self, result, runid):
        updates = 0
        temp_obx = self.h[:]
        l = len(self.h)
        for i in range(l):
            del temp_obx[l-i-1]
        new_obx_index = 1
        for obxSegment in self.h['OBX']:
            if obxSegment[3][0][1][0] == "SARS-COV-2, NAA":
                obxSegment[5][0] = result
                obxSegment[1] = new_obx_index
                machineId = ""
                if runid.startswith('003109'):
                    machineId = "UFHPL Panther1"
                elif runid.startswith('003253'):
                    machineId = "UFHPL Panther2"
                if len(machineId) > 0:
                    obxSegment[18][0] = machineId
                new_obx_index +=1 
                temp_obx.append(obxSegment) 
            
        h_t = self.h[:]
        l = len(self.h)
        for i in range(l):
            del h_t[l-i-1]
        for i in range(len(self.h)):
            if(self.h[i][0][0]!="OBX"):
                h_t.append(self.h[i])
        h_t.extend(temp_obx)
        return h_t

    def get_first_obx_index(self):
        idx = 0
        for seg in self.h:
            if seg[0][0] == 'OBX':
                return idx
            idx += 1
        return -1
    # Assuming insertion is just above first OBX segment
    def update_comments(self, comments):
        comments_arr = comments.split("\n")
        obx_idx = self.get_first_obx_index()
        if (obx_idx == -1):
            print("OBX segment not found, so appending it")
            obx_idx = len(self.h) - 1 
        i=1
        for comment in comments_arr:
            self.h.append('NTE|{}|L|{}'.format(i,comment))
            obx_idx += 1
            i += 1

# method to write the results to excel
def writeDataToExcel(sampleToResult, sampleToPool):
    writeToList = []
    for key, value in sampleToResult.items():    
        tempdict = {}
        tempdict['CONTAINER_ID'] = key
        tempdict['POOL_ID'] = sampleToPool[key]      
        tempdict['VALID_FLAG'] = sampleToResult[key][1]
        tempdict['RESULT'] = sampleToResult[key][2]
        tempdict['RLU_SCORE'] = sampleToResult[key][3]
        tempdict['RLU_FLAG'] = sampleToResult[key][4]         
        if key in dbdict.keys():
            tempdict['MRN'] = dbdict[key][0]
            tempdict['PLMO_NUMBER'] = dbdict[key][1]
            tempdict['PATIENT_NAME'] = dbdict[key][2]
            tempdict['PATIENT_SEX'] = dbdict[key][3]
            tempdict['PATIENT_AGE'] = dbdict[key][4]
       
        writeToList.append(tempdict)

    xldf = pd.DataFrame(writeToList)
    columnsTitles = ['VALID_FLAG','POOL_ID','RLU_FLAG','RLU_SCORE','RESULT','CONTAINER_ID','MRN','PLMO_NUMBER','PATIENT_NAME','PATIENT_SEX','PATIENT_AGE']
    xldf = xldf.reindex(columns=columnsTitles)
    xldf.sort_values(['RESULT','POOL_ID'], ascending=[False,True], inplace=True)
    RESULT_LOG = "RESULTS_OUTPUT.xlsx"
    
    try:
        with pd.ExcelWriter(RESULT_LOG) as writer:
            xldf.to_excel(writer, index=False, sheet_name='Sheet 1')
        print("done writeToExcel method and writing done to -->", RESULT_LOG )
    except:
        print("unable to save status excel, please close it")

def checkIncomingHl7(sampleDict, sampleResultDict):
    allhl7filenames = []
    for (dirpath, dirnames, filenames) in os.walk(MIRTH_ORDERS_DIR):
        allhl7filenames.extend(filenames)
        break
    for hl7_file_name in allhl7filenames:
        try:
            hl7file = open(MIRTH_ORDERS_DIR + hl7_file_name, mode="r").read()
        except:
            continue
        arr = hl7file.split("\n\n") #split by blank lines
        #Iterate all HL7 messages in file
        for hl7msg in arr: 
            if hl7msg: #check if message not empty
                msg_unix_fmt = hl7msg.replace("\n","\r")
                h = hl7.parse(msg_unix_fmt)
                newHl7 = hl7update(h)
                #Read message id from HL7 message
                try:
                    messageId = str(h['OBR'][0][3]).replace("^", "")
                except:
                    continue
                if (not messageId):
                    continue
                plm = None
                try:
                    plm = h['ORC'][0][2]
                except:
                    print("---------could not find PLMO in hl7 file: ", hl7_file_name)
                    continue
                
                mrn = ""
                try:
                    mrn = h['PID'][0][3][0][0]
                except:
                    print("---------could not find MRN in hl7 file: ", hl7_file_name)
        
                ptName = ""
                try:
                    ptName = h['PID'][0][5][0]
                except:
                    print("---------could not find PATIENT_NAME in hl7 file: ", hl7_file_name) 

                ptSex = ""
                try:
                    ptSex = h['PID'][0][8][0]
                except:
                    print("---------could not find PATIENT_SEX in hl7 file: ", hl7_file_name) 

                ptAge = -1
                try:    
                    ptAge = 2020 - int(h['PID'][0][7][0][:4]) 
                except:
                    print("---------could not find PATIENT_AGE in hl7 file: ", hl7_file_name) 

                ordDept = ""
                try:
                    ordDept = h['OBR'][0][15][0]
                except:
                    print("---------could not find Ordering_DEPT in hl7 file: ", hl7_file_name) 

                if messageId in sampleDict or plm[0] in sampleDict:
                    if sampleDict.get(messageId) is not None:
                        givenSampleResult =  sampleDict.get(messageId)
                    else:
                        givenSampleResult = sampleDict.get(plm[0])                  
                    newHl7.update_msh_segment()
                    newHl7.update_orc_segment()
                    newHl7.update_obr_segment()
                    newHl7.update_obx_segment()
                    h = newHl7.update_obx_seg_containing_gene( givenSampleResult, sampleResultDict[messageId][0] )
                    
                    out_file_path = MIRTH_RESULTS_DIR + '/hl7-pooled-COVID_19-{}-output.txt'.format(messageId)
                    if h:
                        with open(out_file_path, 'w' ,  encoding='utf-8') as f:
                            f.write(str(h))
                        print("Out file available at :",out_file_path)
                        move(MIRTH_ORDERS_DIR + hl7_file_name, MIRTH_ARCHIVE_DIR + 'POOLED_COVID_19_processed_' + get_current_formatted_date() + "-" + hl7_file_name) 
                        if plm:
                            dbdict[messageId] = [str(mrn), plm, str(ptName), str(ptSex), str(ptAge)]

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:],"hs:p:o:r:a:",["help","pm_file=","pr_file=","orders_dir=","results_dir=","orders_archive_dir="])
    except getopt.GetoptError:
        print('Pool_Covid19_Panther.py -s <input pool map file> -p <input pool results file> -o <mirth orders directory> -r <mirth results directory> -a <orders archive directory>')
        sys.exit(2)
        
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print('Pool_Covid19_Panther.py -s <input pool map file> -p <input pool results file> -o <mirth orders directory> -r <mirth results directory> -a <orders archive directory>')
            sys.exit()
        elif opt in ("-s", "--pm_file"):
            INPUT_POOL_FILE = arg
        elif opt in ("-p", "--pr_file"):
            INPUT_POOL_RESULTS_FILE = arg
        elif opt in ("-o", "--orders_dir"):
            MIRTH_ORDERS_DIR = arg
        elif opt in ("-r", "--results_dir"):
            MIRTH_RESULTS_DIR = arg  
        elif opt in ("-a", "--orders_archive_dir"):
            MIRTH_ARCHIVE_DIR = arg

    check_folders_exist()

    sampleToPool = {}
    df = pd.read_excel(INPUT_POOL_FILE)
    for i, row in df.iterrows():
        if not pd.isna(row["Source Sample Barcode"]):
            sampleToPool[str(row["Source Sample Barcode"]).split(".")[0]] = str(row["Pooled Sample Barcode"]).split(".")[0]

    results_df = pd.read_csv(INPUT_POOL_RESULTS_FILE, sep='\t')
    pool_results = {}

    for i, row in results_df.iterrows():
        if row["Specimen Barcode"] in sampleToPool.values():
            if int(row["Interpretation 1"]) < RLU_NOMINAL_SCORE:
                flag = "NORMAL"
            else:
                flag = "HIGH"
            pool_results[row["Specimen Barcode"]] = [row["Run ID"], row["Interpretation 2"], row["Interpretation 3"], row["Interpretation 1"], flag]

    #contains results corresponding to each containerId
    sampleToResult = {}
    for i, row in df.iterrows():
        if not pd.isna(row["Source Sample Barcode"]):
            if str(row["Pooled Sample Barcode"]).split(".")[0] in pool_results.keys():
                sampleToResult[str(row["Source Sample Barcode"]).split(".")[0]] = pool_results[str(row["Pooled Sample Barcode"]).split(".")[0]]
            else:
                sampleToResult[str(row["Source Sample Barcode"]).split(".")[0]] = ["No Results","No Results","No Results","No Results","No Results"]

    containerToResult = {}
    for containerId in sampleToResult:
        if sampleToResult[containerId][1].lower() == "valid" and sampleToResult[containerId][2].lower() == "negative" and int(sampleToResult[containerId][3]) < RLU_NOMINAL_SCORE:
            containerToResult[containerId] = "Not Detected"

    #logic to add the corresponding hl7 file to RESULTS folder
    checkIncomingHl7(containerToResult, sampleToResult)

    #print(f)
    writeDataToExcel(sampleToResult, sampleToPool)