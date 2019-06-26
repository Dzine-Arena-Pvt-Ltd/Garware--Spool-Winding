try:
    import psutil
except:
   pass
from PyQt4.QtGui import *
from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
try:
    _encoding = QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)

import cv2
import os
import sys
from mainDesign import Ui_MainWindow
import json

config_file = "resources/config/config.json"
config_backup_file = "resources/config/config_backup.json"
config_plc_file = "resources/config/config_plc.json"

with open(config_plc_file, "r") as file:
    config_js_data = json.load(file)


from camera_handler import cameraHandler
import mbus
# from modbusHandler import ModbusHandler
import json
from  functools import partial


class ExampleApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.move(0, 0)
        self.config_js_data = None
        #
        # with open(config_plc_file, "r") as file:
        #     js_data = json.load(file)


        with open(config_file, "r") as file:
            self.config_js_data = json.load(file)

        with open(config_backup_file, "r") as file:
            self.config_js_backup = json.load(file)

        self.camHandler = cameraHandler(self)

        # self.btn_start.clicked.connect(lambda state, arg=self.btn_start: self.btnApplicationHandler(arg, state))
        self.btn_login.clicked.connect(lambda state, arg=self.btn_login: self.btnApplicationHandler(arg, state))
        self.btnTest.clicked.connect(lambda state, arg=self.btnTest: self.camHandler.btnToolHandler(arg, state))
        self.btn_measure.clicked.connect(lambda state, arg=self.btn_measure: self.camHandler.btnToolHandler(arg, state))
        self.btn_manual.clicked.connect(lambda state, arg=self.btn_manual: self.camHandler.btnToolHandler(arg, state))
        self.btn_start.clicked.connect(lambda state, arg=self.btn_start: self.camHandler.btnToolHandler(arg, state))
        self.btn_fname.clicked.connect(self.camHandler.set_file_name)
        # self.btn_measure.clicked.connect(self.camHandler.measure_view)

        self.swView.setCurrentWidget(self.live_view)

        for btn in self.gpSourceTools_0.children():
            btn.clicked.connect(lambda state, arg=btn: self.camHandler.btnToolHandler(arg, state))

        self.btnBackup.clicked.connect(self.get_Backup)
        self.btnReload.clicked.connect(self.get_Reload)
        # self.btnReset.clicked.connect(lambda state, arg=self.btnReset: self.camHandler.btnToolHandler(arg, state))

        # self.gpSourceTools
        # self.plc_handler = ModbusHandler()




# camera_0
        self.camera0 = "cam0"

        camera = self.camera0
        self.fmCamSample_0.hide()

        self.fm_prefix_cam0 = "fmCam0_"
        self.hs_prefix_cam0 = "hsCam0_"
        self.lb_prefix_cam0 = "lbCam0_"

        for index in range(0, len(self.config_js_data[camera]["settings"]), 1):
            fm_name = self.fm_prefix_cam0 + str(index)
            hs_name = self.hs_prefix_cam0 + str(index)
            lb_name = self.lb_prefix_cam0 + str(index)

            setattr(self, fm_name, QtGui.QFrame(self.sawcsCam_0))
            fm = getattr(self, fm_name)

            fm.setMinimumSize(QtCore.QSize(220, 100))
            fm.setMaximumSize(QtCore.QSize(220, 100))
            fm.setFrameShape(QtGui.QFrame.StyledPanel)
            fm.setFrameShadow(QtGui.QFrame.Raised)
            fm.setObjectName(_fromUtf8(fm_name))

            setattr(self, hs_name, QtGui.QSlider(fm))
            hs = getattr(self, hs_name)

            hs.setGeometry(QtCore.QRect(20, 20, 181, 29))
            hs.setOrientation(QtCore.Qt.Horizontal)
            hs.setObjectName(_fromUtf8(hs_name))

            setattr(self, lb_name, QtGui.QLabel(fm))
            lb = getattr(self, lb_name)

            lb.setGeometry(QtCore.QRect(30, 60, 171, 31))
            lb.setAlignment(QtCore.Qt.AlignCenter)
            lb.setObjectName(_fromUtf8(lb_name))

            self.gridLayout_8.addWidget(fm, index, 0, 1, 1)

            hs.valueChanged[int].connect(partial(self.camHandler.slider_handler_click, hs))
            hs.sliderReleased.connect(partial(self.camHandler.slider_handler_release, hs))
            hs.setRange(self.config_js_data[camera]["settings"][index]["min"],
                        self.config_js_data[camera]["settings"][index]["max"])
            hs.setValue(self.config_js_data[camera]["settings"][index]["val"])

            lb_text = self.config_js_data[camera]["settings"][index]["name"]+"-"+str(hs.value())
            lb.setText(lb_text)

        self.val_mstrwdt.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_mode.setStyleSheet('color: red')
        self.btn_measure.setChecked(False)
        self.lbl_mode.setText("LIVE")

        self.lbl_warn.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_warn.setStyleSheet('color: red')

        self.login = True
        self.btn_login.setChecked(self.login)
        self.tabWidget.setCurrentIndex(0)
        self.val_mstrwdt.setDisabled(True)

        # Login Unable

        if not self.login:
            self.tabWidget.setTabEnabled(1, False)
            self.p_tolerance.setDisabled(True)
            self.n_tolerance.setDisabled(True)
            self.val_awdth.setDisabled(True)


        # for key, val in self.config_js_data.items():
        #       self.cb_objects.addItem(key)


    def config_update(self, obj, key=None, val=None):
        print("updated > ", obj, val)
        if key is None:
            self.config_js_data[self.machine_type][obj] = val
        else:
            self.config_js_data[self.machine_type][obj][key] = val
        with open(config_file, "w") as file:
            json.dump(self.config_js_data, file, indent=4)

    def update_camera_setting(self, cam, index, par, val):
        self.config_js_data[cam]["settings"][index][par] = val

        with open(config_file, "w") as file:
            json.dump(self.config_js_data, file, indent=4)

    def get_Backup(self):
        with open(config_backup_file, "w") as file:
            json.dump(self.config_js_data, file, indent=4)
            print("backup updated")

    def get_Reload(self):
        with open(config_file, "w") as file:
            json.dump(self.config_js_backup, file, indent=4)
            print("backup reloaded")

    def showlogo_bycv(self, obj, img, path=None):
        if path:
            img = cv2.imread(img)
        frame = cv2.resize(img, (obj.size().width(), obj.size().height()))
        resizedImage = QImage(frame, frame.shape[1], frame.shape[0],
                              frame.strides[0], QImage.Format_RGB888).rgbSwapped()
        obj.setPixmap(QPixmap.fromImage(resizedImage))

    def btnApplicationHandler(self, btn, state):
        btn_text = btn.text()
        if btn_text == "Test":
             print("test")
        else:
            if state:
                # if btn_text == "Start":
                #     btn.setText("Stop")
                #     mbus.start_plc()
                #     cameraHandler.set_file_flag()
                #     # mbus.auto_mode()


                if btn_text == "login":
                        text, ok = QInputDialog.getText(self, 'admin login', 'Enter password:', QLineEdit.Password)

                        if ok:
                            if text == "dzine":
                                QMessageBox.information(None, "Message", "Admin login successfully")
                                btn.setChecked(True)
                                self.login = True
                                self.tabWidget.setTabEnabled(1, True)
                                self.p_tolerance.setDisabled(False)
                                self.n_tolerance.setDisabled(False)
                                self.val_awdth.setDisabled(False)
                            elif text == "spool":
                                QMessageBox.information(None, "Message", "Client login successfully")
                                btn.setChecked(True)
                                self.login = True
                                self.p_tolerance.setDisabled(False)
                                self.n_tolerance.setDisabled(False)
                                self.val_awdth.setDisabled(False)
                                # self.tabWidget.setCurrentIndex(0)
                            else:
                                QMessageBox.warning(None, "Message", "login failed")
                                btn.setChecked(False)
                                self.login = False
                                self.tabWidget.setTabEnabled(1, False)
                                self.p_tolerance.setDisabled(True)
                                self.n_tolerance.setDisabled(True)
                                self.val_awdth.setDisabled(True)
                                self.tabWidget.setCurrentIndex(0)

            else:
                # if btn_text == "Stop":
                #     btn.setText("Start")
                #     mbus.stop_plc()
                #     cameraHandler.clear_file_flag()
                #     # print("stop")
                if btn_text == "login":
                    btn.setChecked(False)
                    self.login = False
                    self.tabWidget.setTabEnabled(1, False)
                    self.tabWidget.setCurrentIndex(0)
                    # self.sa_result_0.hide()
                    # self.sa_result_1.hide()
                    # self.sa_result_2.hide()
                    # self.lb_reportCard_1.hide()

    def closeApp(self):
        def kill_proc(pid, including_parent=True):
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.kill()
            if including_parent:
                parent.kill()

        me = os.getpid()
        kill_proc(me)

    def closeEvent(self, evnt):
        try:
            mbus.manual_mode()
            mbus.stop_plc()
            # cameraHandler.colse_file()
            self.closeApp()

        except Exception as e:
            print(e)


def main():
    app = QApplication(sys.argv)
    form = ExampleApp()
    form.show()
    app.exec_()


if __name__ == '__main__':
    main()
