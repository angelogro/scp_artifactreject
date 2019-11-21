import random
from math import ceil
from itertools import cycle
from xml_read import XML_Read
from PyQt5.QtWidgets import  QGridLayout,QLabel, QAction, QTextEdit, QFontDialog, QColorDialog, QFileDialog, QTableWidget,QLCDNumber
from PyQt5.QtCore import Qt
import os
from PyQt5 import QtCore
import csv
PAUSETEXT = 'pause'
PAUSEBETWEENTRIALSTEXT = 'pause_between_trials'
PAUSEID = 100
STARTID = 200

seq = {0.2:[[1,0,0,0,1,0,0,0,0,0],
          [1,0,0,0,0,1,0,0,0,0],
          [1,0,0,0,0,0,0,0,1,0],
          [0,1,0,1,0,0,0,0,0,0],
          [0,1,0,0,1,0,0,0,0,0],
          [0,1,0,0,0,1,0,0,0,0],
          [0,0,1,0,1,0,0,0,0,0],
          [0,0,0,1,0,0,0,0,1,0],
          [0,0,1,0,0,0,0,0,1,0],
          [0,0,0,1,0,0,1,0,0,0],
          [0,0,0,0,1,0,1,0,0,0],
          [0,0,0,0,0,0,1,0,1,0]],
       0.3:[[1,0,1,0,0,1,0,0,0,0],
          [1,0,0,1,0,1,0,0,0,0],
          [1,0,0,0,0,1,0,0,1,0],
          [0,1,0,1,0,0,0,1,0,0],
          [0,1,0,0,1,0,0,1,0,0],
          [0,1,0,0,0,1,0,0,1,0],
          [0,0,1,0,1,0,0,1,0,0],
          [0,0,0,1,0,1,0,0,1,0],
          [0,0,1,0,1,0,0,0,1,0],
          [0,0,0,1,0,0,1,0,1,0]],
       0.4:[[1,0,1,0,0,1,0,0,1,0],
          [1,0,0,1,0,1,0,0,1,0],
          [1,0,1,0,0,1,0,1,0,0],
          [0,1,0,1,0,1,0,1,0,0],
          [0,1,0,0,1,0,1,0,1,0],
          [1,0,0,1,0,1,0,1,0,0],
          [0,0,1,0,1,0,1,0,1,0],
          [1,0,1,0,1,0,0,0,1,0],
          [1,0,1,0,1,0,1,0,0,0]]}

def getSequence(prob):
    if prob not in seq.keys():
        print(n,'is not a possible probability.')
        return None

    return seq[prob][random.randint(0,len(seq[prob])-1)]

def getCompleteSequence(prob,desiredLength):
    returnedSequence = []
    while len(returnedSequence) < desiredLength:
        returnedSequence.extend(getSequence(prob))
    return returnedSequence[:desiredLength]


class TimeTable():
    def __init__(self,settingOrderPath,settingTrialPath,xml_config_read):
        self.XML_Read = xml_config_read
        self.XML_artifactOrder = XML_Read(settingOrderPath)
        self.XML_settingTrial = XML_Read(settingTrialPath)
        self.loadSettingInformation()
        filename,filetype = QFileDialog.getSaveFileName(None,"Stimulus file", os.path.join(QtCore.QDir.currentPath(),self.XML_Read.getValue(['Paths','StimulusFilesDefault'])),
                                                        "CSV Files (*.csv)")
        self.writeToCSVFile(filename)

    def loadSettingInformation(self):
        self.lstOrder = []
        trialDuration = self.XML_settingTrial.getValue(['TrialSettings','GeneralSettings','sbTrialDuration'])
        self.stimulusDuration = self.XML_settingTrial.getValue(['TrialSettings','GeneralSettings','sbStimulusDuration'])
        self.pauseDuration = self.XML_settingTrial.getValue(['TrialSettings','GeneralSettings','sbPause'])
        randomizeStimuli = self.XML_settingTrial.getValue(['TrialSettings','GeneralSettings','cbRandomizeStimuli'])
        amountOfTrials = int(self.XML_artifactOrder.getValue(['AmountOfTrials']))
        self.pauseBetweenTrials = 60*int(self.XML_artifactOrder.getValue(['PauseInBetweenTrials','Minute']))+int(self.XML_artifactOrder.getValue(['PauseInBetweenTrials','Second']))
        self.amount_of_stimuli = ceil(int(trialDuration)*60/(float(self.stimulusDuration)+float(self.pauseDuration)))
        self.artifacts = list(list(zip(*self.XML_artifactOrder.getChildren(['Order'])))[0])
        all_stimuli_list = [ele for ele in self.artifacts for _ in range(self.amount_of_stimuli)]

        if int(randomizeStimuli) == Qt.CheckState(Qt.Checked):
            random.shuffle(all_stimuli_list)
        self.all_stimuli_list = all_stimuli_list

        self.ERP = bool(self.XML_settingTrial.getAttrib(['TrialSettings','ERP'],'Checked'))

        if  self.ERP == True:
            self.generateERPStimuliSequence()
        else:
            self.generateArtifactStimuliSequence()
    
    def generateERPStimuliSequence(self):
        prob = float(self.XML_settingTrial.getValue(['TrialSettings','ERP','cbProbability']))
        complSequence = iter(getCompleteSequence(prob,len(self.all_stimuli_list)))

        time = 0      
        for i in range(len(self.artifacts)):
            if (time != 0):
                self.lstOrder.append({'start_time':str(time),'end_time':str(time+self.pauseBetweenTrials),'type':PAUSEBETWEENTRIALSTEXT})
                time+=self.pauseBetweenTrials
                
            for num in range(self.amount_of_stimuli):
                self.lstOrder.append({'start_time':str(time),'end_time':str(time+float(self.pauseDuration)),'type':PAUSETEXT})
                time+=float(self.pauseDuration)

                if complSequence.__next__() == 1:
                    self.lstOrder.append({'start_time':str(time),'end_time':str(time+float(self.stimulusDuration)),
                                                'type':self.artifacts[i]})
                else:
                    while True:
                        nontargetindex = random.randint(0,len(self.artifacts)-1)
                        if nontargetindex!=i:
                            break
                    self.lstOrder.append({'start_time':str(time),'end_time':str(time+float(self.stimulusDuration)),
                                                'type':self.artifacts[nontargetindex]})
                time+=float(self.stimulusDuration)

    def generateArtifactStimuliSequence(self):
        time = 0
        
        for i in range(amountOfTrials):
            if (time != 0) or (int(self.otherSettings['P300']) == Qt.CheckState(Qt.Checked)):
                self.lstOrder.append({'start_time':str(time),'end_time':str(time+pauseBetweenTrials),'type':PAUSEBETWEENTRIALSTEXT})
                time+=pauseBetweenTrials
                
            for num in range(amount_of_stimuli):
                self.lstOrder.append({'start_time':str(time),'end_time':str(time+float(pauseDuration)),'type':PAUSETEXT})
                time+=float(pauseDuration)
                
                if int(self.otherSettings['P300'])==Qt.CheckState(Qt.Checked):
                    if random.random()<prob:
                        self.lstOrder.append({'start_time':str(time),'end_time':str(time+float(stimulusDuration)),
                                                  'type':self.artifacts[i]})
                    else:
                        while True:
                            artifact_name = all_stimuli_list.__next__()
                            if artifact_name != self.artifacts[i]:
                                break
                        self.lstOrder.append({'start_time':str(time),'end_time':str(time+float(stimulusDuration)),
                                                  'type':artifact_name})
                else:
                    artifact_name = all_stimuli_list.__next__()
                    self.lstOrder.append({'start_time':str(time),'end_time':str(time+float(stimulusDuration)),
                                                  'type':artifact_name})
                time+=float(stimulusDuration)

        

        



    def writeToCSVFile(self,filename):

        with open(filename, mode='w',newline='') as csv_file:
            fieldnames = ['start_time', 'end_time', 'type']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.lstOrder:
                writer.writerow(row)