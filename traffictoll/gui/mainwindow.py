import psutil
from PyQt5.QtCore import QItemSelectionModel, QSortFilterProxyModel, Qt, pyqtSlot
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QMainWindow

from traffictoll.gui.views.mainwindow import Ui_MainWindow


class LeafSortFilterProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        if super().filterAcceptsRow(source_row, source_parent):
            return True

        # Check if any ancestors accept the filter
        parent = source_parent
        while parent.isValid():
            if super().filterAcceptsRow(parent.row(), parent.parent()):
                return True
            parent = parent.parent()

        # Check if any descendants accept the filter
        model = self.sourceModel()

        children_indices = [model.index(source_row, 0, source_parent)]
        while children_indices:
            child_index = children_indices.pop()
            for row in range(model.rowCount(child_index)):
                if super().filterAcceptsRow(row, child_index):
                    return True

                children_indices.append(model.index(row, 0, child_index))

        return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.processes = QStandardItemModel(0, 5)
        self.processes.setHeaderData(0, Qt.Horizontal, 'Name', Qt.DisplayRole)
        self.processes.setHeaderData(1, Qt.Horizontal, 'PID', Qt.DisplayRole)
        self.processes.setHeaderData(2, Qt.Horizontal, 'Command', Qt.DisplayRole)
        self.processes.setHeaderData(3, Qt.Horizontal, 'Download Limit', Qt.DisplayRole)
        self.processes.setHeaderData(4, Qt.Horizontal, 'Upload Limit', Qt.DisplayRole)

        # TODO: Subclass QSortFilterProxyModel to match on any child
        self.processes_filter = LeafSortFilterProxyModel(self.processes)
        self.processes_filter.setSourceModel(self.processes)
        self.processes_filter.setFilterKeyColumn(-1)
        self.processes_filter.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.processes_selection = QItemSelectionModel(self.processes_filter)
        self.processes_selection.selectionChanged.connect(self._on_selection_changed)

        self.ui.processes.setModel(self.processes_filter)
        self.ui.processes.setSelectionModel(self.processes_selection)

        root = psutil.Process(1)
        self._insert_tree(root, self.processes)

    def _insert_tree(self, tree, parent):
        root_item = QStandardItem(tree.name())
        root_item.setData(tree, Qt.UserRole)
        for child in tree.children():
            self._insert_tree(child, root_item)

        columns = [
            QStandardItem(str(tree.pid)),
            QStandardItem(' '.join(tree.cmdline())),
            QStandardItem(),
            QStandardItem()]
        parent.appendRow([root_item, *columns])

    @pyqtSlot(str)
    def on_search_textChanged(self, text):
        self.processes_filter.setFilterFixedString(text)

    def _on_selection_changed(self, before, now):
        pids = []
        for selected in self.processes_selection.selectedRows():
            process = selected.data(Qt.UserRole)
            pids.append(process.pid)
            pids.extend(c.pid for c in process.children(recursive=True))
