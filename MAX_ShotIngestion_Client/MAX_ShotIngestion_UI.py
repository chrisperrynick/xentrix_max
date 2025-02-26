import os
import sys
import Config as Config
from importlib import *
from PySide2 import QtWidgets, QtGui, QtCore
import MAX_ShotIngestionMain as MAX_ShotIngestionMain

reload(MAX_ShotIngestionMain)
reload(Config)


class ShotIngestionUI(QtWidgets.QMainWindow):
    def __init__(self):
        self.open_browser = None
        self.seq_path = None
        super(ShotIngestionUI, self).__init__()
        self.setWindowTitle('MAX Shot Ingestion')
        self.resize(350, 550)

        # creating MainWidget
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)

        # creating Horizontal layout
        main_hor_layout = QtWidgets.QHBoxLayout()
        main_widget.setLayout(main_hor_layout)

        # creating gridLayout
        grid_layout = QtWidgets.QGridLayout()
        main_hor_layout.addLayout(grid_layout)
        # Browser path
        self.browse_btn = QtWidgets.QPushButton('Browse Bake path')
        self.browse_btn.resize(30, 30)

        # Shot Import
        self.dont_import_sd_cb = QtWidgets.QCheckBox("Don't Import Shot Data")

        # Search LineEdit
        self.search_ldt = QtWidgets.QLineEdit()
        self.search_ldt.setPlaceholderText('Search...')

        # shot list
        self.shotList_LWgt = QtWidgets.QListWidget()
        self.shot_Num_LWgt = QtWidgets.QListWidget()

        # inject button
        self.inject = QtWidgets.QPushButton('Ingest')

        grid_layout.addWidget(self.browse_btn, 0, 0)
        grid_layout.addWidget(self.dont_import_sd_cb, 0, 1)
        grid_layout.addWidget(self.search_ldt, 0, 2)
        grid_layout.addWidget(self.shotList_LWgt, 1, 0, 1, -1)
        grid_layout.addWidget(self.inject, 3, 0, 1, -1)

        self.show()
        self.browse_btn.clicked.connect(self.project_shot_list)
        self.shotList_LWgt.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.inject.clicked.connect(self.get_shot_versions_to_inject)
        self.search_ldt.textChanged.connect(lambda: self.search_info(self.search_ldt, self.shotList_LWgt))

    def project_shot_list(self):
        self.shotList_LWgt.clear()
        self.open_browser = QtWidgets.QFileDialog.getExistingDirectory(dir='')
        self.seq_path = '{path}/Game/Conform'.format(path=self.open_browser)
        if os.path.exists(self.open_browser):
            for each_epi in os.listdir(self.seq_path):
                for each_seq in sorted(os.listdir(os.path.join(self.seq_path, each_epi))):
                    if not os.path.isdir(os.path.join(self.seq_path, each_epi, each_seq)):
                        continue
                    shots_path = '{seq_path}/{each_epi}/{each_seq}/Shots'.format(seq_path=self.seq_path,
                                                                                 each_epi=each_epi, each_seq=each_seq)
                    if not os.path.exists(shots_path):
                        continue
                    for each_shot in sorted(os.listdir(shots_path)):
                        if not os.path.isdir(os.path.join(shots_path, each_shot)):
                            continue
                        self.shotList_LWgt.addItem(each_shot)
        else:
            QtWidgets.QMessageBox.warning(self, 'Warning!!!!', "Provide The Specific Folder Path")

    def get_shot_versions_to_inject(self):
        shot_list = []
        if len(self.shotList_LWgt.selectedItems()) > 0:
            message_box = QtWidgets.QMessageBox()
            message_box.setText("Are you sure you want to ingest selected  files ?")
            message_box.setIcon(QtWidgets.QMessageBox.Question)
            message_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
            message_box.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
            message_box.setDefaultButton(QtWidgets.QMessageBox.No)
            result = message_box.exec_()
            if result == QtWidgets.QMessageBox.Yes:
                for each in self.shotList_LWgt.selectedItems():
                    shot_list.append(each.text())

        else:
            self.xen_message_box(title='Warning!!!',
                                 message='<p style = "color:#ff6666">Please Select the Shots...</p>')
            return

        MAX_ShotIngestionMain.main(shot_list, Config.MAYA_EXE_PATH, self.seq_path, self.dont_import_sd_cb.isChecked())

        sucess_data, error_data = self.erorr_sucess_data()

        self.xen_message_box(title='Done!!!',
                             message='<p style = "color:green">"Sucessfull shots -{} <br></p><p style = "color:red"> '
                                     'Errors shots - {} <br> for erros shots, please check {}"...</p>'.format(
                                 sucess_data, error_data, Config.FILES_SAVING_PATH))


    def erorr_sucess_data(self):
        log_path = r'{}\Logs\max_ingestion_error_success_data.log'.format(Config.FILES_SAVING_PATH)
        error_sucess_log = open(log_path, 'r')
        sucess_data = []
        error_data = []
        for i in error_sucess_log:
            if i.split(':')[0] == 'success':
                sucess_data.append(i.split(':')[-1])
            elif i.split(':')[0] == 'error':
                error_data.append(i.split(':')[-1])
        error_sucess_log.close()
        os.remove(log_path)
        return sucess_data, error_data

    def search_info(self, lineEdit, listWidget):
        """
            Process for searching items from listwidget
        """

        search_string = str(lineEdit.text()).lower()
        for system in [listWidget.item(i) for i in range(listWidget.count())]:
            system.setHidden(search_string not in str(system.text()).lower())

    def xen_message_box(self, title='No Title!!!', message='Information..', icon_path=''):
        """
            Process of notifying messages
        """

        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIconPixmap(QtGui.QPixmap(icon_path))
        msg_box.exec_()


if __name__ == "__main__":
    if not Config.MAYA_DOLLAR_PATH or not Config.MAYA_EXE_PATH or not Config.FILES_SAVING_PATH:
        print("Please Enter MAYA_DOLLAR_PATH, FILES_SAVING_PATH and MAYA_EXE_PATH")
    else:
        app = QtWidgets.QApplication(sys.argv)
        win = ShotIngestionUI()
        win.show()
        sys.exit(app.exec_())
