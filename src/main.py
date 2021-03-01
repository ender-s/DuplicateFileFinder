from Ui_MainWindow import Ui_MainWindow
from Tools import Tools
from Crawler import Crawler
from Counter import Counter
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QTreeWidgetItem
import sys, os

class MW(QtWidgets.QMainWindow):
    closeSignal = QtCore.pyqtSignal()
    def __init__(self):
        super().__init__()
    
    def closeEvent(self, event):
        self.closeSignal.emit()

class FileSaver(QtCore.QThread):
    processDone = QtCore.pyqtSignal(str)

    def __init__(self, main, path):
        super().__init__()
        self.tools = Tools()
        self.main = main
        self.path = path
    
    def run(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self._duplicate_information_str())
        self.processDone.emit(f"Information was successfully saved on {self.path}")
    
    def _duplicate_information_str(self):
        result = ""
        for md5, info in self.main.duplicateInformation:
            result += f"MD5: {md5} | size: {self.tools.humanReadableSize(info[1])}\n"
            for n, path in enumerate(info[0]):
                result += f"\t{n+1}: {path}\n"
        
        result += "\nStatistics:\n" + self.main._get_statistics()
        return result
    
    

class Main(object):
    def __init__(self):
        app = QtWidgets.QApplication(sys.argv)

        self.isPathSelected = False
        self.selectedPath = ""
        self.duplicateInformation = []
        self.tools = Tools()

        self.MainWindow = MW()
        self.MainWindow.closeSignal.connect(self._quit)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)
        self.ui.treeWidget.itemDoubleClicked.connect(self._item_handler)
        self._connect_signals()
        self.MainWindow.show()
        sys.exit(app.exec_())

    def _item_handler(self, item, column):
        if column == 2 and item.parent():
            self._show_information("Information", item.text(2))

    

    def _connect_signals(self):
        self.ui.pushButton.clicked.connect(self._browse)
        self.ui.pushButton_2.clicked.connect(self._start)
        self.ui.pushButton_3.clicked.connect(self._stop)
        self.ui.pushButton_4.clicked.connect(self._save_info)
        self.ui.actionClose.triggered.connect(self._quit)

    def _browse(self):
        path = str(QFileDialog.getExistingDirectory(self.MainWindow, "Select Directory"))
        if path:
            path = os.path.abspath(path)
            self.isPathSelected = True
            self.selectedPath = path
            self.ui.lineEdit.setText(path)
    
    def _start(self):
        self.duplicateInformation = []
        self.ui.treeWidget.clear()
        


        if not self.isPathSelected:
            self._show_error_message("Path is not selected!")
        elif not self.selectedPath:
            self._show_error_message("The selected path string is empty!")
        else:
            self.counter = Counter(self)
            self.counter.processDone.connect(self._count_process_done)
            self.counter.updateStatusBar.connect(self._update_status_bar)
            self._start_process_set_button_states()
            self.counter.start()
            
    def _start_process_set_button_states(self):
        self.ui.pushButton.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)
        self.ui.pushButton_3.setEnabled(True)
    
    def _end_process_set_button_states(self):
        self.ui.pushButton.setEnabled(True)
        self.ui.pushButton_2.setEnabled(True)
        self.ui.pushButton_3.setEnabled(False)

    def _update_status_bar(self, text):
        self.ui.statusbar.showMessage(text)

    def _process_done(self):
        if not self.crawler.canceled:
            self._update_progress_bar_value(100)
            self._update_status_bar(self.ui.statusbar.currentMessage() + "   Done!")

            text = "Process is done! Results:\n" + self._get_statistics()
            self._show_information("Done!", text)

        self._end_process_set_button_states()
    
    def _get_statistics(self):
        text = ""
        text += "Number of all duplicate files: " + str(self.crawler.totalCopyCount) + "\n"
        text += "Number of unnecessary duplicates: " + str(self.crawler.totalCopyCount - self.crawler.uniqueCopyCount) + "\n"
        text += "Number of different files that have duplicates: " + str(self.crawler.uniqueCopyCount) + "\n"
        text += "Size of all duplicate files: " + self.tools.humanReadableSize(self.crawler.totalCopySize) + "\n"
        text += "Size of unnecessary duplicates: " + self.tools.humanReadableSize(self.crawler.totalCopySize - self.crawler.uniqueCopySize) + "\n"
        text += "Size of data that is stored in duplicate files: " + self.tools.humanReadableSize(self.crawler.uniqueCopySize) + "\n"
        return text

    def _count_process_done(self, files, folders, others, total):
        if not self.counter.canceled:
            self.crawler = Crawler(self, files, folders, others, total)
            self.crawler.processDone.connect(self._process_done)
            self.crawler.updateStatusBar.connect(self._update_status_bar)
            self.crawler.setProgressBarValue.connect(self._update_progress_bar_value)
            self.crawler.updateDuplicateInformation.connect(self._update_duplicate_information)
            self.crawler.createDuplicateInformation.connect(self._create_duplicate_information)
            self.crawler.start()
        else:
            self._end_process_set_button_states()

    def _update_progress_bar_value(self, val):
        self.ui.progressBar.setValue(val)
    
    def _find_index_binary_search(self, size):
        ll = 0
        ul = len(self.duplicateInformation)

        while ll != ul:
            middle = int((ll + ul)/2)
            sizeAtMiddle = self.duplicateInformation[middle][1][1]
            if size == sizeAtMiddle:
                return middle
            elif size > sizeAtMiddle:
                ul = middle - 1
            else:
                ll = middle + 1
        
        if self.duplicateInformation[ll][1][1] != size:
            return -1
        else:
            return ll

    
    def _find_index_with_the_correct_md5(self, index, size, md5):
        startIndex = index - 1
        while startIndex >= 0 and self.duplicateInformation[startIndex][1][1] == size:
            if self.duplicateInformation[startIndex][0] == md5:
                return startIndex
            startIndex -= 1
        startIndex += 1

        endIndex = index
        while endIndex < len(self.duplicateInformation) and self.duplicateInformation[endIndex][1][1] == size:
            if self.duplicateInformation[endIndex][0] == md5:
                return endIndex
            endIndex += 1
        endIndex -= 1

        return None

    def _update_duplicate_information(self, md5, path, size):
        ind = self._find_index_binary_search(size)
        assert (ind != -1)
        if md5 == self.duplicateInformation[ind][0]:
            index = ind
        else:
            index = self._find_index_with_the_correct_md5(ind, size, md5)
            assert (index != None)

        
        assert (index != -1)

        info = self.duplicateInformation[index][1]

        fl = info[0].copy()
        fl.append(path)
        self.duplicateInformation[index] = [md5, [fl, size]]

        self.ui.treeWidget.topLevelItem(index).addChild(QTreeWidgetItem(["", "", path]))

    def _create_duplicate_information(self, md5, info):

        index = self._find_correct_index(info, self.duplicateInformation)
        assert (index != None)
        self.duplicateInformation.insert(index, [md5, info])

        twItem = QtWidgets.QTreeWidgetItem([md5, self.tools.humanReadableSize(info[1]), ""])
        for i in info[0]:
            twItem.addChild(QTreeWidgetItem(["", "", i]))
        self.ui.treeWidget.insertTopLevelItem(index, twItem)


    def _find_correct_index(self, info, l):
        if len(l) == 0: return 0
        if self._compare(info, l[0][1]) >= 0: return 0
        if self._compare(info, l[-1][1]) <= 0: return len(l)

        ll = 0
        ul = len(l)
        while ll < ul:
            middle = int((ll+ul)/2)
            comp = self._compare(info, l[middle][1])
            if comp == 0:
                return middle
            elif comp < 0:
                ll = middle + 1
            else:
                ul = middle - 1
                if self._compare(info, l[middle - 1][1]) <= 0:
                    return middle
        
        if self._compare(info, l[ll - 1][1]) <= 0 and self._compare(info, l[ll][1]) >= 0:
            return ll
        elif self._compare(info, l[ul - 1][1]) <= 0 and self._compare(info, l[ul][1]) >= 0:
            return ul
        else:
            return None

    def _compare(self, info1, info2):
        if info1[1] > info2[1]:
            return 1
        elif info1[1] < info2[1]:
            return -1
        else:
            return 0

    def _show_information(self, title, msg):
        infDialog = QMessageBox(self.MainWindow)
        infDialog.setIcon(QMessageBox.Information)
        infDialog.setText(msg)
        infDialog.setWindowTitle(title)
        infDialog.exec_()

    def _show_error_message(self, msg):
        errDialog = QMessageBox(self.MainWindow)
        errDialog.setIcon(QMessageBox.Critical)
        errDialog.setText(msg)
        errDialog.setWindowTitle("Error!")
        errDialog.exec_()

    def _stop(self):
        try:
            self.counter.lock = False
        except: pass

        try:
            self.crawler.lock = False
        except: pass
        
        self._show_information("Process Was Canceled", "Process was canceled by the user.")
        


    def _save_info(self):
        path, _ = QFileDialog.getSaveFileName(None, "Save Information File", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            self._show_information("Canceled", "Save path was not selected!")
        else:
            self.fs = FileSaver(self, path)
            self.fs.processDone.connect(self._file_saved)
            self._show_information("About Saving Information File", "Saving process will start when you click on OK.\nThis may take some time depending on the size of the obtained information.")
            self.fs.start()
    
    def _file_saved(self, msg):
        self._show_information("File Saved!", msg)

    def _quit(self):
        self.MainWindow.close()

if __name__ == "__main__":
    main = Main()