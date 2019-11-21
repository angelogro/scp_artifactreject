# -*- coding: utf-8 -*-
"""
Created on Tue Oct 29 17:05:21 2019

@author: agross
"""
from PyQt5 import QtGui,uic
from PyQt5.QtWidgets import  QGridLayout,QLabel, QAction, QTextEdit, QFontDialog, QColorDialog, QFileDialog, QTableWidget,QFrame
from PyQt5.QtWidgets import QApplication,QLineEdit,QDialog,QScrollArea,QWidget,QStackedWidget, QMainWindow, QPlainTextEdit,QVBoxLayout
import os
from PyQt5.QtGui import QIcon,QPixmap
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
from PyQt5.Qt import QFileInfo,QDrag,QMimeData,QXmlSimpleReader,QDomDocument, QXmlStreamWriter,QFile,QIODevice,QTextStream,QTime
from PyQt5.QtCore import Qt,QRect
from PyQt5.QtGui import QPainter, QColor, QFont, QPdfWriter,QFontMetrics
from xml_read import XML_Read
from PyQt5 import QtCore
from xml_read import Singleton

#@Singleton
class SettingArtefactOrder(QDialog):
    def __init__(self,xml_config_read,xml_file=None):
        super().__init__()
        self.XML_Read = xml_config_read
        uic.loadUi(os.path.join(self.XML_Read.getValue(['Paths','Designer_File_Folder']),'artifactOrder.ui'),self)
        self.btnLoad.clicked.connect(self.loadArtifactOrder)
        self.btnSave.clicked.connect(self.saveArtifactOrder)
        print(xml_file)
        self.loadArtefactTypes(xml_file)
        self.show()
        
    def loadArtefactTypes(self,xml_file=None):
        if xml_file and os.path.isfile(xml_file):
            self.loadArtifactOrder(None,xml_file=xml_file)
            return
        lstArtefactTypes = self.XML_Read.getChildren(['ArtefactCategories'])
        for _type,_used in lstArtefactTypes:
            self.verticalLayout.addWidget(DragQLabel(self.XML_Read.getValue(['ArtefactCategories',_type,'Text']),xml_text=_type,parent=self.verticalLayout))
        
        
    def loadArtifactOrder(self,event,xml_file=None):
        if not xml_file:
            fileName = QFileDialog.getOpenFileName(self,
                "Open Bookmark File", os.path.join(QtCore.QDir.currentPath(),self.XML_Read.getValue(['Paths','ArtifactOrderSettingsDefault'])),
                "XBEL Files (*.xbel *.xml)")
        else:
            fileName = xml_file

        if type(fileName)==str:
            xmlReader = XML_Read(fileName)
            if not xml_file:
                self.currentXMLfilepath = fileName
        else:
            xmlReader = XML_Read(fileName[0])
            if not xml_file:
                self.currentXMLfilepath = fileName[0]

        orders = list(zip(*xmlReader.getChildren(['Order'])))[0]
        self.emptyLayout(self.verticalLayout)
        for _type in orders:
            self.verticalLayout.addWidget((DragQLabel(self.XML_Read.getValue(['ArtefactCategories',_type,'Text']),xml_text=_type,parent=self.verticalLayout)))
        
        pause_minute = xmlReader.getValue(['PauseInBetweenTrials','Minute'])
        pause_second = xmlReader.getValue(['PauseInBetweenTrials','Second'])
        self.timeEditInBetweenTrials.setTime(QTime(0,int(pause_minute),int(pause_second),0))
        self.sbAmountTrials.setValue(int(xmlReader.getValue(['AmountOfTrials'])))
        
    def saveArtifactOrder(self,event,fileName=None):
        diag = QFileDialog(self,"Open Bookmark File", QtCore.QDir.currentPath())
        if fileName is None:
            filename,filetype = QFileDialog.getSaveFileName(self,"Open Bookmark File",os.path.join(QtCore.QDir.currentPath(),self.XML_Read.getValue(['Paths','ArtifactOrderSettingsDefault'])),
                "XML Files (*.xml)")
        else:
            filename = fileName
        fh = QFile(filename)
        if not fh.open(QIODevice.WriteOnly):
            print('IOERROR')
        self.currentXMLfilepath = filename
        stream = QXmlStreamWriter(fh)
        
        stream.setAutoFormatting(True)
        stream.writeStartDocument()
        stream.writeStartElement("Data")
        stream.writeStartElement("Order")
        for i in range(self.verticalLayout.count()):
            print(self.verticalLayout.itemAt(i).widget().text())
            stream.writeTextElement(self.verticalLayout.itemAt(i).widget().xml_text, "")
        #stream.writeAttribute("href", "http://qt-project.org/")
        stream.writeEndElement()
        stream.writeStartElement('PauseInBetweenTrials')
        stream.writeTextElement('Minute',str(self.timeEditInBetweenTrials.time().minute()))
        stream.writeTextElement('Second',str(self.timeEditInBetweenTrials.time().second()))
        stream.writeEndElement()
        stream.writeTextElement('AmountOfTrials',str(self.sbAmountTrials.value()))
        stream.writeEndElement()
        stream.writeEndDocument()
        
    def emptyLayout(self,layout):
        for i in reversed(range(layout.count())):
            item = layout.takeAt(i)
            item.widget().deleteLater()
            
    def accept(self):
        if not hasattr(self,'currentXMLfilepath'):
            self.saveArtifactOrder(None,fileName='temp_ordersettings.xml')
        self.close()
        
        
class DragQLabel(QLabel):
    def __init__(self, *args,xml_text,parent=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.xml_text = xml_text
        self.setStyleSheet("background-color: rgb(212, 241, 239);")
        self.setAutoFillBackground(True)
        self.setFrameShape(QFrame.Box)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        
    
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
        if event.button() == Qt.RightButton:
            self.parent.removeWidget(self)
            self.deleteLater()
            

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        
        mimedata = QMimeData()
        mimedata.setParent(self)
        mimedata.setText(self.text())
        drag.setMimeData(mimedata)
        pixmap = QPixmap(self.size())
        painter = QPainter(pixmap)
        painter.drawPixmap(self.rect(), self.grab())
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        drag.exec_(Qt.CopyAction | Qt.MoveAction)
    
    def dragEnterEvent(self, event):
        print(event)
        print(event.mimeData().text())
        print(self.text())
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        print(event)
        pos = event.pos()
        text = event.mimeData().text()
        oldtext = self.text()

        self.setText(text)
        event.mimeData().parent().setText(oldtext)
        event.acceptProposedAction()
        
class SettingTrial(QDialog):
    def __init__(self,xml_config_read,xml_file=None):
        super().__init__()
        self.XML_Read = xml_config_read
        uic.loadUi(os.path.join(self.XML_Read.getValue(['Paths','Designer_File_Folder']),'trialSetting.ui'),self)
        self.rbERP.clicked.connect(lambda x: self.activateFormLayout(self.rbERP))
        self.rbArtifacts.clicked.connect(lambda x: self.activateFormLayout(self.rbArtifacts))
        self.btnSave.clicked.connect(self.saveSettings)
        self.btnLoad.clicked.connect(self.loadSettings)
        if xml_file and os.path.isfile(xml_file):
            self.loadSettings(None,xml_file)
        self.show()
        
    def activateFormLayout(self,object_):
        if object_ is self.rbERP:
            for i in range(self.formLayoutERP.count()):
                item = self.formLayoutERP.itemAt(i)
                item.widget().setEnabled(True)
        elif object_ is self.rbArtifacts:
            for i in range(self.formLayoutERP.count()):
                item = self.formLayoutERP.itemAt(i)
                item.widget().setEnabled(False)
                
    def loadSettings(self,event,xml_file=None):
        print(self.XML_Read.getValue(['Paths','TrialSettingsDefault']))
        if xml_file:
            fileName = xml_file
            xmlReader = XML_Read(fileName)
        else:
            fileName = QFileDialog.getOpenFileName(self,
                "Open Bookmark File", os.path.join(QtCore.QDir.currentPath(),self.XML_Read.getValue(['Paths','TrialSettingsDefault'])),
                "XBEL Files (*.xbel *.xml)")
            if type(fileName)==str:
                xmlReader = XML_Read(fileName)
                self.currentXMLfilepath = fileName
            else:
                xmlReader = XML_Read(fileName[0])
                self.currentXMLfilepath = fileName[0]

        self.sbTrialDuration.setValue(int(xmlReader.getValue(['TrialSettings','GeneralSettings','sbTrialDuration'])))
        self.sbStimulusDuration.setValue(float(xmlReader.getValue(['TrialSettings','GeneralSettings','sbStimulusDuration'])))
        self.sbPause.setValue(float(xmlReader.getValue(['TrialSettings','GeneralSettings','sbPause'])))
        self.cbRandomizeStimuli.setCheckState(int(xmlReader.getValue(['TrialSettings','GeneralSettings','cbRandomizeStimuli'])))
        index = self.cbProbability.findText(xmlReader.getValue(['TrialSettings','ERP','cbProbability']))
        if  index != -1 :
            self.cbProbability.setCurrentIndex(index)

        if xmlReader.getAttrib(['TrialSettings','Artifacts'],'Checked') == 'True':
            pass
        if xmlReader.getAttrib(['TrialSettings','ERP'],'Checked') == 'True':
            self.rbERP.setChecked(True)
            self.activateFormLayout(self.rbERP)
        
    def saveSettings(self,event,filename=None):
        if not filename:
            filename,filetype = QFileDialog.getSaveFileName(self,"Open Bookmark File", os.path.join(QtCore.QDir.currentPath(),self.XML_Read.getValue(['Paths','TrialSettingsDefault'])),
                "XML Files (*.xml)")
        fh = QFile(filename)
        if not fh.open(QIODevice.WriteOnly):
            print('IOERROR')
        self.currentXMLfilepath = filename
        stream = QXmlStreamWriter(fh)
        
        stream.setAutoFormatting(True)
        stream.writeStartDocument()
        stream.writeStartElement("Data")
        stream.writeStartElement("TrialSettings")
        stream.writeStartElement('GeneralSettings')
        
        stream.writeTextElement(self.sbTrialDuration.objectName(),str(self.sbTrialDuration.value()))
        stream.writeTextElement(self.sbStimulusDuration.objectName(),str(self.sbStimulusDuration.value()))
        stream.writeTextElement(self.sbPause.objectName(),str(self.sbPause.value()))
        stream.writeTextElement(self.cbRandomizeStimuli.objectName(),str(self.cbRandomizeStimuli.checkState()))
        stream.writeEndElement()
        stream.writeStartElement('Artifacts')
        stream.writeAttribute('Checked',str(self.rbArtifacts.isChecked()))
        stream.writeEndElement()
        stream.writeStartElement('ERP')
        stream.writeAttribute('Checked',str(self.rbERP.isChecked()))
        stream.writeTextElement(self.cbProbability.objectName(),str(self.cbProbability.currentText()))
        stream.writeEndElement()
        stream.writeEndElement()
        stream.writeEndElement()
        stream.writeEndDocument()
    
    def accept(self):
        if not hasattr(self,'currentXMLfilepath'):
            self.saveSettings(None,filename='temp_trialsettings.xml')
        self.close()