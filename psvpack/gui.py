#!/usr/bin/env python3
# vim: set ts=4 sw=4 expandtab syntax=python:
"""

psvpack.gui
PS Vita package tool
CLI entry-point

@author   Jacob Hipps <jacob@ycnrg.org>

Copyright (c) 2018 J. Hipps / Neo-Retro Group, Inc.
https://ycnrg.org/

"""
# pylint: disable=E0602,W0201,C0111

import os
import sys
import logging
import time

from PyQt5.QtCore import QThread, QRegExp, QSortFilterProxyModel, Qt, QDate, QDateTime, QTime, qVersion, QT_VERSION_STR, PYQT_VERSION_STR, pyqtSignal
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from PyQt5.Qt import Qt, QPixmap

from psvpack import __version__, __date__
from psvpack.cli import setup_logging
from psvpack import psfree
from psvpack.util import *

logger = logging.getLogger('psvpack')
gconf = get_default_config()


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadGameData()

    def initUI(self):

        # Setup main application window
        self.title = "psvpack"
        self.geo = (100, 100, 800, 600)
        self.setWindowTitle(self.title)
        self.setGeometry(*self.geo)

        # Create menu items
        self.createMenus()

        # Setup proxy model
        self.proxyModel = GameListFilter(self)
        self.proxyModel.setDynamicSortFilter(True)

        # Setup source view (gameList)
        self.gameList = QTreeView()
        self.gameList.setRootIsDecorated(False)
        self.gameList.setAlternatingRowColors(True)
        self.gameList.setSortingEnabled(True)
        self.gameList.sortByColumn(3, Qt.DescendingOrder)

        self.glistModel = self.createGlistModel(self)
        self.gameList.setModel(self.proxyModel)
        self.proxyModel.setSourceModel(self.glistModel)

        self.gameList.setColumnWidth(0, 80)
        self.gameList.setColumnWidth(1, 50)
        self.gameList.setColumnWidth(2, 450)
        self.gameList.setColumnWidth(3, 120)
        self.gameList.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Setup searchBox / filter
        flayout = QVBoxLayout()
        rlayout = QHBoxLayout()

        self.searchBox = QLineEdit()
        self.searchBox.textChanged.connect(self.searchBoxChanged)

        imgpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
        self.regionChkUS = QCheckBox()
        self.regionChkJP = QCheckBox()
        self.regionChkEU = QCheckBox()
        self.regionChkASIA = QCheckBox()
        self.regionChkUS.setCheckState(Qt.Checked)
        self.regionChkJP.setCheckState(Qt.Checked)
        self.regionChkEU.setCheckState(Qt.Checked)
        self.regionChkASIA.setCheckState(Qt.Checked)
        self.regionChkUSLabel = QLabel("US")
        self.regionChkUSLabel.setPixmap(QPixmap(os.path.join(imgpath, "flag_us32.png")))
        self.regionChkJPLabel = QLabel("JP")
        self.regionChkJPLabel.setPixmap(QPixmap(os.path.join(imgpath, "flag_jp32.png")))
        self.regionChkEULabel = QLabel("EU")
        self.regionChkEULabel.setPixmap(QPixmap(os.path.join(imgpath, "flag_eu32.png")))
        self.regionChkASIALabel = QLabel("ASIA")
        self.regionChkASIALabel.setPixmap(QPixmap(os.path.join(imgpath, "flag_asia32.png")))
        self.regionChkUS.stateChanged.connect(self.searchBoxChanged)
        self.regionChkJP.stateChanged.connect(self.searchBoxChanged)
        self.regionChkEU.stateChanged.connect(self.searchBoxChanged)
        self.regionChkASIA.stateChanged.connect(self.searchBoxChanged)

        rlayout.addWidget(self.regionChkUS)
        rlayout.addWidget(self.regionChkUSLabel)
        rlayout.addWidget(self.regionChkJP)
        rlayout.addWidget(self.regionChkJPLabel)
        rlayout.addWidget(self.regionChkEU)
        rlayout.addWidget(self.regionChkEULabel)
        rlayout.addWidget(self.regionChkASIA)
        rlayout.addWidget(self.regionChkASIALabel)
        rlayout.addStretch()

        self.regionGroup = QGroupBox()
        self.regionGroup.setFlat(True)
        self.regionGroup.setLayout(rlayout)

        flayout.addWidget(self.searchBox)
        flayout.addWidget(self.regionGroup)

        self.searchBoxGroup = QGroupBox("Filter")
        self.searchBoxGroup.setLayout(flayout)

        # Setup main layout
        layout = QVBoxLayout()
        layout.addWidget(self.gameList)
        layout.addWidget(self.searchBoxGroup)
        self.dataGroupBox = QGroupBox("Game List")
        self.dataGroupBox.setLayout(layout)

        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.dataGroupBox)
        self.mainWidget.setLayout(mainLayout)

        # Show main app window
        self.resize(1000, 700)
        self.show()

    def loadGameData(self):
        global gconf

        self.uconfig = load_config(interactive=False)
        if not isinstance(self.uconfig['tsv_urls'], dict):
            self.showConfigWarning()
            return

        gconf = self.uconfig

        self.statusBar().showMessage("Refreshing game list...")

        logger.debug("Launching update thread...")
        upThread = UpdateThread(self)
        upThread.signal.connect(self.loadGameDataComplete)
        upThread.start()
        logger.debug("Update thread launched")

    def loadGameDataComplete(self, resp):
        logger.debug("Finished loading game data. resp=%s", resp)
        if resp is True:
            self.statusBar().showMessage("Ready. Loaded %d games" % (self.glistModel.rowCount()))
            self.searchBoxChanged()
        else:
            self.statusBar().showMessage("Failed to load game list. Check config.")
            self.showConfigWarning()

    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(QAction("Preferences...", self, statusTip="Show Settings dialog", triggered=self.launchSettings))
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(QAction("Export config...", self, statusTip="Export configuration file", triggered=self.configExport))
        self.fileMenu.addAction(QAction("Import config...", self, statusTip="Import configuration file", triggered=self.configImport))
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(QAction("E&xit", self, shortcut="Ctrl+Q", statusTip="Exit", triggered=self.close))

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(QAction("About", self, statusTip="Show version information", triggered=self.about))
        self.helpMenu.addAction(QAction("About Qt", self, statusTip="Show Qt version information", triggered=QApplication.instance().aboutQt))

    def showConfigWarning(self):
        QMessageBox.warning(self, "Configuration Error", "Please visit the settings menu to configure psvpack with the correct TSV URLs")

    def about(self):
        #abox = QMessageBox.about(self, "About psvpack",
        #                               '<h3>psvpack</h3>'
        #                               '<p>Copyright &copy; 2018 J. Hipps<br><a href="https://ycnrg.org/">https://ycnrg.org/</a></p>'
        #                               '<p>Country icons by <a href="http://www.freepik.com">Freepik</a>, licensed under Creative Commons CC-BY 3.0</p>')

        imgpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img') # FIXME: replace with something better

        abox = QMessageBox(self)
        abox.setWindowTitle("About psvpack")
        abox.setText("""\
                    <h2>psvpack</h2>
                    <p>
                        <a href="https://ycnrg.org/">https://ycnrg.org/</a>
                    </p>
                    <p>
                        Country icons by <a href="http://www.freepik.com">Freepik</a>, licensed under Creative Commons CC-BY 3.0
                    </p>
                    <p>
                        psvpack, Copyright &copy; 2018 J. Hipps
                    </p>
                    <p>
                        Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
                        documentation files (the "Software"), to deal in the Software without restriction, including without limitation
                        the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
                        and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
                    </p>
                    <p>
                        The above copyright notice and this permission notice shall be included in all copies or substantial portions
                        of the Software.
                    </p>
                    <p>
                        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
                        TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
                        THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
                        CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
                        DEALINGS IN THE SOFTWARE.
                    </p>
                     """)
        abox.setStandardButtons(QMessageBox.Ok)
        abox.setDefaultButton(QMessageBox.Ok)
        abox.setIconPixmap(QPixmap(os.path.join(imgpath, "psvpack_cropvert.png")))
        abox_size = abox.size()
        abox.resize(abox_size)
        abox.setStyleSheet("QLabel{min-width: 400px;}")
        abox.show()
        abox.exec()

    def launchSettings(self):
        sd = SettingsDialog(self)
        return sd.exec_()

    def configExport(self):
        pathtup = QFileDialog.getSaveFileName(self, "Export config...",
                                              os.path.expanduser('~'),
                                              "*.yaml")
        if pathtup[0]:
            target_path = pathtup[0]
            if os.path.splitext(pathtup[0])[1] != '.yaml':
                target_path += '.yaml'
            rval = save_config(gconf, target_path)
            if rval is True:
                logger.info("Exported configuration to %s", target_path)
                QMessageBox.information(self, "Export Config", "Configuration exported successfully!")
            else:
                logger.warning("Failed to export config from %s: %s", target_path, rval)
                QMessageBox.warning(self, "Export Config", "Configuration export failed!<br><br>%s" % (rval))

    def configImport(self):
        global gconf

        target_path = QFileDialog.getOpenFileName(self, "Import config...",
                                                  os.path.expanduser('~'),
                                                  "*.yaml")
        if isinstance(target_path, str) and target_path:
            newconf = load_config(target_path, interactive=False)
            if newconf:
                self.uconfig = newconf
                gconf = self.uconfig
                save_config(gconf)
                logger.info("Imported configuration from %s successfully", target_path)
                QMessageBox.information(self, "Import Config", "Configuration imported successfully!")
            else:
                logger.warning("Failed to import config from %s", target_path)
                QMessageBox.warning(self, "Import Config", "Configuration import failed!")
        else:
            logger.debug("Config import aborted. target_path='%s'", target_path)

    def searchBoxChanged(self):
        regex = QRegExp(self.searchBox.text(), False, QRegExp.PatternSyntax(QRegExp.Wildcard))
        self.proxyModel.plainText = self.searchBox.text()
        self.proxyModel.regionList = ['']
        if self.regionChkUS.isChecked(): self.proxyModel.regionList += ['US']
        if self.regionChkJP.isChecked(): self.proxyModel.regionList += ['JP']
        if self.regionChkEU.isChecked(): self.proxyModel.regionList += ['EU']
        if self.regionChkASIA.isChecked(): self.proxyModel.regionList += ['ASIA']

        # setFilterRegExp() must be called last, as it triggers a re-sort of the proxyModel
        self.proxyModel.setFilterRegExp(regex)
        self.statusBar().showMessage("Displaying %d / %d" % (self.proxyModel.rowCount(), self.glistModel.rowCount()))
        #logger.debug("searchBoxChanged: regionList=%s / plainText=%s / matched rows=%d", self.proxyModel.regionList, self.proxyModel.plainText, self.proxyModel.rowCount())

    def createGlistModel(self, parent):
        model = QStandardItemModel(0, 6, parent)
        model.setHeaderData(0, Qt.Horizontal, "ID")
        model.setHeaderData(1, Qt.Horizontal, "Region")
        model.setHeaderData(2, Qt.Horizontal, "Title/Version")
        model.setHeaderData(3, Qt.Horizontal, "Updated")
        model.setHeaderData(4, Qt.Horizontal, "Size")
        model.setHeaderData(5, Qt.Horizontal, "Content ID")
        return model

    def addGame(self, idx, region, title, updated, size, cid):
        self.glistModel.insertRow(0)
        self.glistModel.setData(self.glistModel.index(0, 0), idx)
        self.glistModel.setData(self.glistModel.index(0, 1), region)
        self.glistModel.setData(self.glistModel.index(0, 2), title)
        self.glistModel.setData(self.glistModel.index(0, 3), updated)
        self.glistModel.setData(self.glistModel.index(0, 4), size)
        self.glistModel.setData(self.glistModel.index(0, 5), cid)


class UpdateThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self, mainapp):
        super().__init__(mainapp)
        self.mainapp = mainapp

    def run(self):
        # Setup progress dialog
        #logger.debug("Launching QProgressDialog for UpdateThread...")
        #progressDiag = QProgressDialog("Checking TSV cache...", "", 0, 100)
        #logger.debug(sys._getframe().f_lineno)
        #progressDiag.setWindowTitle("psvpack - Loading")
        #logger.debug(sys._getframe().f_lineno)
        #progressDiag.setValue(0)
        #logger.debug(sys._getframe().f_lineno)
        #progressDiag.setWindowModality(Qt.WindowModal)
        #logger.debug(sys._getframe().f_lineno)
        #progressDiag.show()

        # Load the TSV file (as well as download updates if necessary)
        logger.debug("Checking TSV cache...")
        #tsv = psfree.TSVManager('PSV', gconf, pd=progressDiag)
        tsv = psfree.TSVManager('PSV', gconf)

        if tsv.loaded is False:
            logger.error("Failed to load TSV")
            #progressDiag.close()
            #self.mainapp.showConfigWarning()
            self.signal.emit(False)
            return

        logger.debug("Clearing existing glistModel data...")
        self.mainapp.glistModel.removeRows(0, self.mainapp.glistModel.rowCount())

        #progressDiag.setLabelText("Loading game list...")
        logger.debug("Loading game list into glistModel")
        for tgame in tsv.glist:
            tdate = QDateTime.fromString(tgame['Last Modification Date'], "yyyy-MM-dd hh:mm:ss")
            self.mainapp.addGame(str(tgame['Title ID']), str(tgame['Region']), str(tgame['Name']), tdate, fmtsize(tgame['File Size']), str(tgame['Content ID']))

        gcount = self.mainapp.glistModel.rowCount()
        logger.debug("Loaded %d games", gcount)

        #progressDiag.setValue(100)
        #progressDiag.close()
        self.mainapp.gameList.setDisabled(False)
        self.signal.emit(True)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        tabWidget = QTabWidget()
        self.generalTab = GeneralTab()
        self.sourcesTab = SourcesTab()
        tabWidget.addTab(self.generalTab, "General")
        tabWidget.addTab(self.sourcesTab, "Sources")

        # Hook up buttons
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Settings")
        self.resize(450, 400)

    def accept(self):
        global gconf

        try:
            cache_ttl = int(self.generalTab.cacheTtlEdit.text())
        except:
            logger.warning("Failed to parse cache TTL from preferences. Falling back to default.")
            cache_ttl = default_config['cache_ttl']

        # get source list
        tsv_urls = {}
        for trow in range(self.sourcesTab.sourceModel.rowCount()):
            tkey = str(self.sourcesTab.sourceModel.item(trow, 0).text()).strip()
            tval = str(self.sourcesTab.sourceModel.item(trow, 1).text()).strip()
            if tkey:
                tsv_urls[tkey] = tval

        logger.info("tsv items update: %s", tsv_urls)

        gconf = {
            'cache_dir': self.generalTab.cacheDirEdit.text(),
            'cache_ttl': cache_ttl,
            'pkg2zip': self.generalTab.p2zPathEdit.text(),
            'install_root': self.generalTab.installRootEdit.text(),
            'tsv_urls': tsv_urls
        }

        save_rez = save_config(gconf)
        if save_rez is not True:
            QMessageBox.error(self.parent, "Failed to write configuration file:<br/><br/>%s" % (save_rez))

        self.parent.loadGameData()

        super().accept()


class GeneralTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Setup form items
        cacheDirLabel = QLabel("Cache Directory")
        self.cacheDirEdit = QLineEdit(str(gconf['cache_dir']))
        cacheDirBrowse = QPushButton("Browse...", self)
        cacheDirBrowse.clicked.connect(self.browse_cacheDir)

        cacheTtlLabel = QLabel("Cache TTL")
        self.cacheTtlEdit = QLineEdit(str(gconf['cache_ttl']))
        self.cacheTtlEdit.setInputMask('000009')
        self.cacheTtlEdit.setMaximumWidth(60)

        installRootLabel = QLabel("Default Install Root")
        self.installRootEdit = QLineEdit(str(gconf['install_root']))
        installRootBrowse = QPushButton("Browse...", self)
        installRootBrowse.clicked.connect(self.browse_installRoot)

        p2zPathLabel = QLabel("pkg2zip Path")
        self.p2zPathEdit = QLineEdit(str(gconf['pkg2zip']))
        p2zPathBrowse = QPushButton("Browse...", self)
        p2zPathBrowse.clicked.connect(self.browse_pkg2zip)

        # Create layout
        oLayout = QVBoxLayout()
        oGroup = QGroupBox()
        mainLayout = QGridLayout()

        mainLayout.addWidget(cacheDirLabel, 0, 0, 1, 2)
        mainLayout.addWidget(self.cacheDirEdit, 1, 0, 1, 1)
        mainLayout.addWidget(cacheDirBrowse, 1, 1, 1, 1)

        mainLayout.addWidget(cacheTtlLabel, 2, 0, 1, 2)
        mainLayout.addWidget(self.cacheTtlEdit, 3, 0, 1, 2)

        mainLayout.addWidget(installRootLabel, 4, 0, 1, 2)
        mainLayout.addWidget(self.installRootEdit, 5, 0, 1, 1)
        mainLayout.addWidget(installRootBrowse, 5, 1, 1, 1)

        mainLayout.addWidget(p2zPathLabel, 6, 0, 1, 2)
        mainLayout.addWidget(self.p2zPathEdit, 7, 0, 1, 1)
        mainLayout.addWidget(p2zPathBrowse, 7, 1, 1, 1)

        oLayout.addWidget(oGroup)
        oLayout.addStretch()
        oGroup.setLayout(mainLayout)
        self.setLayout(oLayout)

    def browse_cacheDir(self):
        target_path = QFileDialog.getExistingDirectory(self, "Select Base Cache Directory...",
                                                       os.path.expandvars(os.path.expanduser(self.cacheDirEdit.text())))
        if isinstance(target_path, str) and target_path:
            self.cacheDirEdit.setText(target_path)

    def browse_installRoot(self):
        target_path = QFileDialog.getExistingDirectory(self, "Select default install root...",
                                                       os.path.expandvars(os.path.expanduser(self.installRootEdit.text())))
        if isinstance(target_path, str) and target_path:
            self.installRootEdit.setText(target_path)

    def browse_pkg2zip(self):
        target_path = QFileDialog.getOpenFileName(self, "Locate pkg2zip...",
                                                  os.path.expandvars(os.path.expanduser(self.p2zPathEdit.text())),
                                                  "pkg2zip*")
        if isinstance(target_path, str) and target_path:
            self.p2zPathEdit.setText(target_path)


class SourcesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Setup treeview for editing TSV key/value pairs
        self.sourceModel = QStandardItemModel(0, 2, self)
        self.sourceModel.setHeaderData(0, Qt.Horizontal, "List ID")
        self.sourceModel.setHeaderData(1, Qt.Horizontal, "URL")

        for tkey, turl in gconf['tsv_urls'].items():
            self.sourceModel.insertRow(0)
            self.sourceModel.setData(self.sourceModel.index(0, 0), tkey)
            self.sourceModel.setData(self.sourceModel.index(0, 1), turl)

        #self.sourceList = QTreeView()
        self.sourceList = SourcesItemView()
        self.sourceList.setRootIsDecorated(False)
        self.sourceList.setAlternatingRowColors(True)
        self.sourceList.setModel(self.sourceModel)

        # Create +/- buttons for add/remove rows
        #self.addRowButton = QPushButton("+", self)
        #self.addRowButton.clicked.connect(self.add_row)

        # Create layout
        oLayout = QVBoxLayout()
        oGroup = QGroupBox()
        mainLayout = QGridLayout()

        mainLayout.addWidget(self.sourceList, 0, 0, 1, 1)
        #mainLayout.addWidget(self.addRowButton, 1, 0, 1, 1)

        oLayout.addWidget(oGroup)
        oLayout.addStretch()
        oGroup.setLayout(mainLayout)
        self.setLayout(oLayout)

    def add_row(self):
        self.sourceModel.appendRow(QStandardItem())


class SourcesItemView(QTreeView):

    def edit(self, index, trigger, event):
        if index.column() == 0:
            return False
        else:
            return super().edit(index, trigger, event)


class GameListFilter(QSortFilterProxyModel):
    regionList = ['US', 'JP', 'EU', 'ASIA', '']
    plainText = ""

    def __init__(self, parent=None):
        super().__init__(parent)

    def filterAcceptsRow(self, sourceRow, sourceParent):
        i_idx = self.sourceModel().index(sourceRow, 0, sourceParent)
        i_region = self.sourceModel().index(sourceRow, 1, sourceParent)
        i_title = self.sourceModel().index(sourceRow, 2, sourceParent)
        i_cid = self.sourceModel().index(sourceRow, 4, sourceParent)

        try:
            match_region = self.sourceModel().data(i_region).strip() in self.regionList
        except:
            match_region = True

        match_title = self.filterRegExp().indexIn(self.sourceModel().data(i_title)) >= 0
        match_idx = self.sourceModel().data(i_idx) == self.plainText.upper().strip()
        match_cid = self.sourceModel().data(i_cid) == self.plainText.upper().strip()

        return match_idx or match_cid or (match_title and match_region)

    def lessThan(self, left, right):
        leftData = self.sourceModel().data(left)
        rightData = self.sourceModel().data(right)

        if leftData is None:
            logger.debug("leftData is None!")
            return False
        elif rightData is None:
            logger.debug("rightData is None!")
            return True

        if not isinstance(leftData, QDate):
            emailPattern = QRegExp("([\\w\\.]*@[\\w\\.]*)")

            if left.column() == 1 and emailPattern.indexIn(leftData) != -1:
                leftData = emailPattern.cap(1)

            if right.column() == 1 and emailPattern.indexIn(rightData) != -1:
                rightData = emailPattern.cap(1)

        return leftData < rightData

def _gmain():
    """
    GUI Entry Point
    """
    setup_logging(logging.DEBUG)
    logger.info("Starting psvpack-qt")
    logger.info("PyQt %s / libqt5 %s / Qt5 Runtime %s", PYQT_VERSION_STR, QT_VERSION_STR, qVersion())

    qtApp = QApplication(sys.argv)
    app = App()

    sys.exit(qtApp.exec_())

if __name__ == '__main__':
    _gmain()
