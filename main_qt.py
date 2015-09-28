'''
cd Scripts\dicom2mhd\
python setup.py build
'''

from anonymizeImage import anonymizeImage
from anonymizeImage import readImage
from anonymizeImage import saveImage
from convertTagFiles import readTagFiles
from convertTagFiles import writeFcsv
from convertDicom2Mhd import readDicom
from convertDicom2Mhd import writeMhdRaw
import os
import sys

from PyQt4 import  QtGui, uic
import logging

def generateOutFolder(root, folderPathIn, folderPathOut):
    relDir = os.path.relpath(root, folderPathIn)
    tempFolderPathOut = os.path.join(folderPathOut,relDir)
    if not os.path.exists(tempFolderPathOut):
        os.makedirs(tempFolderPathOut)

    return tempFolderPathOut

def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)

form_class = uic.loadUiType("convertData.ui")[0]                 # Load the UI

class ConvertData(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        logging.getLogger('Convert data')
        #logging.basicConfig(filename='convertData.log',level=logging.DEBUG)
        self.logger = logging.getLogger('Convert data')
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('convertData.log')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s  - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)  
        self.logger.info("Program started")        
        
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle('Convert data')
        self.setFixedSize(self.width(), self.height())

        self.pushButton.clicked.connect(self.select_input)  
        self.pushButton_2.clicked.connect(self.select_output)  
        self.pushButton_3.clicked.connect(self.select_convert)  
        self.pushButton_4.clicked.connect(self.select_cancel) 
        
        self.label.setText("")
        self.label_2.setText("")
        self.label_5.setText("")
        
        self.folderPathOut = ''
        self.folderPathIn = ''
        self.cancel = False
        
        
 
    def select_input(self):
        self.logger.info("input")
        self.folderPathIn = QtGui.QFileDialog.getExistingDirectory(None, 'Select input folder:', self.folderPathIn)
        if len(self.folderPathIn) < 33:
            self.label_2.setText(self.folderPathIn)
        else:
            self.label_2.setText("..."+self.folderPathIn[-30:])
        self.logger.info(self.folderPathIn)
        
    def select_output(self):
        self.logger.info("output")
        self.folderPathOut = QtGui.QFileDialog.getExistingDirectory(None, 'Select a folder to store data:',self.folderPathIn, QtGui.QFileDialog.ShowDirsOnly)
        if len(self.folderPathOut) < 33:
            self.label_5.setText(self.folderPathOut)
        else:
            self.label_5.setText("..."+self.folderPathOut[-30:])
        self.logger.info(self.folderPathOut)     
        
    def select_convert(self):
        self.logger.info("convert")
        if len(self.folderPathIn)>0 and len(self.folderPathOut)>0:
            self.cancel = False
            self.pushButton_3.setEnabled(False)
            try:
                self.convertFolder(str(self.folderPathIn), str(self.folderPathOut))
            except Exception, e:
                logging.exception(e) 
                self.label.setText("Failed: " +  e.message)
                self.logger.exception(e)

            self.pushButton_3.setEnabled(True)
        
    def select_cancel(self):
        self.logger.info("cancel")
        self.cancel=True
        
    def convertFolder(self, folderPathIn, folderPathOut):
        for root, dirs, files in os.walk(folderPathIn):
            tagData=[]
            for file_i in files:
                filePath = os.path.join(root, file_i)
                if self.cancel:
                    self.cancel = False
                    self.label.setText("Canceled")
                    self.logger.info("Canceled")
                    return
                self.label.setText("Processing file: " +  os.path.basename(filePath))
                app.processEvents()

                tag = readTagFiles(filePath)
                if tag:
                    self.logger.info("Tag file: " +  os.path.basename(filePath))
                    tagData.append(tag)
                    continue

                dicomData = readDicom(filePath)
                if dicomData:
                    self.logger.info("Dicom file: " +  os.path.basename(filePath))
                    
                    tempFolderPathOut = generateOutFolder(rreplace(root,"Dicom","Data",1), folderPathIn, folderPathOut)
                    writeMhdRaw(tempFolderPathOut, dicomData)
                    continue

                imData = readImage(filePath)
                if imData:
                    self.logger.info("Image file: " +  os.path.basename(filePath))
                    tempFolderPathOut = generateOutFolder(root, folderPathIn, folderPathOut)
                    filePathOut = os.path.join(tempFolderPathOut, os.path.basename(filePath))

                    imDataOut = anonymizeImage(imData, pixelsX=range(230, 1530), pixelsY=range(7, 43), color=(190, 192, 194))
                    saveImage(filePathOut, imDataOut)
                    continue
            if tagData:
                tempFolderPathOut = generateOutFolder(root, folderPathIn, folderPathOut)
                filePathOut = os.path.join(tempFolderPathOut, 'Tags.fcsv')
                writeFcsv(filePathOut, tagData)

        self.label.setText("Finished")
        self.logger.info("Finished")
        
        
app = QtGui.QApplication(sys.argv)
myWindow = ConvertData(None)
myWindow.show()
app.exec_()