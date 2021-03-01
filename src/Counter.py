from PyQt5 import QtCore
import os

class Counter(QtCore.QThread):
    processDone = QtCore.pyqtSignal(int, int, int, int)
    updateStatusBar = QtCore.pyqtSignal(str)

    def __init__(self, main):
        super().__init__()

        self.files = 0
        self.folders = 0
        self.others = 0
        self.total = 0
        self.lock = True
        self.canceled = False

        self.main = main
        self.path = self.main.selectedPath
    
    def run(self):
        self._counter(self.path)
        self.processDone.emit(self.files, self.folders, self.others, self.total)
    
    def _counter(self, path):
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
                    if f.is_dir() and not f.is_symlink():
                        self.folders += 1
                        self._counter(p)
                    elif f.is_file():
                        self.files += 1
                    else:
                        self.others += 1

                    self.total += 1
                except: 
                    pass
        except:
            pass
        
        self._update_status_bar()

    def _update_status_bar(self):
        self.updateStatusBar.emit(f"Counting... {self.files} files, {self.folders} folders, {self.others} others, Total: {self.total}")


