import psutil
from PyQt5.QtCore import QItemSelectionModel, QSortFilterProxyModel, Qt, pyqtSlot
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QMainWindow

from traffictoll.gui.views.mainwindow import Ui_MainWindow
from traffictoll.net import get_net_connections


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.processes = QStandardItemModel(0, 5)
        self.processes.setHeaderData(0, Qt.Horizontal, 'Name', Qt.DisplayRole)
        self.processes.setHeaderData(1, Qt.Horizontal, 'PID', Qt.DisplayRole)
        self.processes.setHeaderData(2, Qt.Horizontal, 'Executable', Qt.DisplayRole)
        self.processes.setHeaderData(3, Qt.Horizontal, 'CMD', Qt.DisplayRole)
        self.processes.setHeaderData(4, Qt.Horizontal, 'Networked', Qt.DisplayRole)

        # TODO: Subclass QSortFilterProxyModel to match on any child
        self.processes_filter = QSortFilterProxyModel(self.processes)
        self.processes_filter.setSourceModel(self.processes)
        self.processes_filter.setFilterKeyColumn(-1)
        self.processes_filter.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.processes_selection = QItemSelectionModel(self.processes_filter)
        self.processes_selection.selectionChanged.connect(self._on_selection_changed)

        self.ui.processes.setModel(self.processes_filter)
        self.ui.processes.setSelectionModel(self.processes_selection)

        self.networked_pids = {connection.pid for connection in get_net_connections()}
        root = psutil.Process(1)
        self._insert_tree(root)

    def _insert_tree(self, tree, parent=None):
        root_item = QStandardItem(tree.name())
        root_item.setData(tree, Qt.UserRole)
        for child in tree.children():
            self._insert_tree(child, root_item)

        columns = [
            QStandardItem(str(tree.pid)),
            QStandardItem(tree.exe()),
            QStandardItem(' '.join(tree.cmdline())),
            QStandardItem('Yes' if tree.pid in self.networked_pids else 'No')]
        (parent or self.processes).appendRow([root_item, *columns])

    @pyqtSlot(str)
    def on_search_textChanged(self, text):
        self.processes_filter.setFilterFixedString(text)
        print(self.processes_selection.selectedRows())

    def _on_selection_changed(self, before, now):
        pids = []
        for selected in self.processes_selection.selectedRows():
            process = selected.data(Qt.UserRole)
            pids.append(process.pid)
            pids.extend(c.pid for c in process.children(recursive=True))

        print(pids)
