from PyQt5 import QtCore
import os, hashlib
from collections import OrderedDict

class Crawler(QtCore.QThread): 
    processDone = QtCore.pyqtSignal()
    updateStatusBar = QtCore.pyqtSignal(str)
    setProgressBarValue = QtCore.pyqtSignal(int)
    updateDuplicateInformation = QtCore.pyqtSignal(str, str, int)
    createDuplicateInformation = QtCore.pyqtSignal(str, list)

    def __init__(self, main, files, folders, others, total):
        super().__init__()
        self.md5Dictionary = OrderedDict()
        self.main = main
        self.canceled = False
        self.files = files
        self.folders = folders
        self.others = others
        self.total = total
        self.uniqueCopyCount = 0
        self.uniqueCopySize = 0
        self.totalCopySize = 0
        self.totalCopyCount = 0

        self.fi = 0 #files
        self.fo = 0 #folders
        self.oth = 0 #others
        self.tot = 0 #total

        self.path = self.main.selectedPath
        self.lock = True
    
    def run(self):
        self._crawl_path(self.path)
        self.processDone.emit()
    
    def _crawl_path(self, path):
        #print (path)
        if not self.lock: 
            self.canceled = True
            return None
        try:
            for f in os.scandir(path):
                if not self.lock: 
                    self.canceled = True
                    break            
                try:
                    p = f.path
                    self.tot += 1
                    if f.is_dir() and not f.is_symlink():
                        self.fo += 1
                        self._crawl_path(p)
                    elif f.is_file():
                        self.fi += 1
                        self._analyze_file(f.path)
                    else:
                        self.oth += 1
                    
                except: pass
        except: pass
        
        self._update_progress()
    
    def _update_progress(self):
        percent = int((self.tot / self.total) * 100)
        self.setProgressBarValue.emit(percent)
        self.updateStatusBar.emit(f"Analyzing... {self.fi}/{self.files} files, {self.fo}/{self.folders} folders, {self.oth}/{self.others} others, Total: {self.tot}/{self.total}")
    
    def _analyze_file(self, path):
        md5, size = self._get_md5(path)
        if md5 in self.md5Dictionary.keys():
            if len(self.md5Dictionary[md5]) == 1:
                self.uniqueCopyCount += 1
                self.uniqueCopySize += size
                
                self.totalCopyCount += 2
                self.totalCopySize += 2 * size
                self.createDuplicateInformation.emit(md5, [[self.md5Dictionary[md5][0], path], size])
            else:
                self.totalCopyCount += 1
                self.totalCopySize += size
                self.updateDuplicateInformation.emit(md5, path, size)
            self.md5Dictionary[md5].append(path)
        else:
            self.md5Dictionary[md5] = [path]
            


    def _get_md5(self, path):
        md5 = hashlib.md5()
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            while True:
                r = f.read(8192)
                if r:
                    md5.update(r)
                else:
                    break
        return (md5.hexdigest(), size)

