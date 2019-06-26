
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import imutils
import threading
import time
import random
import os
from os import path
from functools import partial
import pypylon
from pypylon import pylon
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import os
import json
import cv2
import numpy as np
import glob
import mbus
import datetime

date = datetime.datetime.today()
objects = 30
machine_counter = [[(0, 0),  (0, 0), (0, 0)] for x in range(objects+1)]
default_state = 1

config_file = "resources/config/config.json"
config_backup_file = "resources/config/config_backup.json"
config_plc_file = "resources/config/config_plc.json"
file_flag = False
# data_file = "resources/data/{0}"

def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)


class CameraControl0(threading.Thread):
    def __init__(self, cam,  *args):
        threading.Thread.__init__(self, *args)
        self.job_done = threading.Event()
        self.qt_object = QObject()
        global machine_counter, objects
        self.camera_flag = False
        self.video_read = True

        self.Live = True
        self.Video = False
        self.Record = False
        # self.Image = not self.Live
        self.Test = False

        self.config_js_data = None
        self.cam_js = cam

        self.fault_state = ["O", "A", "A"]

        # with open(config_plc_file, "r") as file:
        #     js_data = json.load(file)

        with open(config_file, "r") as file:
            self.config_js_data = json.load(file)


            # self.config_js_data = json.load(file)

        self.serial_number = self.config_js_data[self.cam_js]["serial_number"]
        for index in range(len(self.config_js_data[self.cam_js]["settings"])):
            name = self.config_js_data[self.cam_js]["settings"][index]["name"]
            val = self.config_js_data[self.cam_js]["settings"][index]["val"]
            setattr(self, name, val)

        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        self.factory = pylon.TlFactory.GetInstance()

        self.camera = None
        self.pfs_file_path = "resources/pfs"
        self.video_file_path = "resources/video"
        self.video_file = ""
        self.video_header = None
        video_dir_list = [item for sublist in [glob.glob(self.video_file_path  + ext) for ext in ["/*.avi", "/*.mp4"]] for item in sublist]
        videos = [video for video in video_dir_list if os.path.splitext(os.path.basename(video))[0] == self.serial_number]
        if any(videos):
            self.video_file = videos[0]
            self.video_obj = cv2.VideoCapture(self.video_file)
            print("found video", videos)

        self.writer = None

        self.video_setting = False

        self.scan_device()

        self.camera_trigger = False

        self.camera_index = self.config_js_data[self.cam_js]["camera_index"]



    def reset_all(self):
        print("data clear")
        self.data = ""


    def tool_trigger(self, btn_txt):
        print(self.serial_number, btn_txt)
        self.Live = False
        self.Video = False
        self.Record = False

        if btn_txt == "Live":
            self.Live = True
        elif btn_txt == "Video":
            self.Video = True
            self.video_speed = 20
        elif btn_txt == "Record":
            self.Record = True
            self.video_speed = 20

    def reset_device(self):

        self.camera.StopGrabbing()
        pfs_file = self.pfs_file_path + "/" + [x for x in os.listdir(self.pfs_file_path) if self.serial_number in x][0]
        print("loading parameter {}".format(pfs_file))
        self.camera.Open()
        # pylon.FeaturePersistence.Save(self.pfs_file, self.camera.GetNodeMap())
        pylon.FeaturePersistence.Load(pfs_file, self.camera.GetNodeMap(), True)
        self.camera.Close()

    def scan_device(self):
        device = [dev for dev in self.factory.EnumerateDevices() if dev.GetSerialNumber() == self.serial_number]
        if any(device):
            self.camera = pylon.InstantCamera(self.factory.GetInstance().CreateDevice(device[0]))
            self.camera_flag = True
            print("device {}  available".format(self.serial_number))
            self.reset_device()

        else:
            print("device {} not available".format(self.serial_number))
            QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number, "state",
                         False)
            self.camera_flag = False

    def camera_stop(self):
        QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number, "state", False)
        self.camera_flag = False

    def denoise(self, frame):
        frame = cv2.medianBlur(frame, 5)
        frame = cv2.GaussianBlur(frame, (5, 5), 0)
        return frame


    def side_camera_result(self, image):
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)

            edged = cv2.Canny(gray, self.canny_x, self.canny_y)
            edged = cv2.dilate(edged, None, iterations=1)
            edged = cv2.erode(edged, None, iterations=1)

            cv2.line(edged, (self.line1_left, self.line1_Y), (self.line1_right, self.line1_Y),
                     (255, 255, 255), 1)
            cv2.line(edged, (self.line2_left, self.line2_Y), (self.line2_right, self.line2_Y),
                     (255, 255, 255), 1)

            # find contours in the edge map
            cnts = cv2.findContours(edged.copy(), cv2.RETR_CCOMP,
                                    cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)

            (cnts, _) = contours.sort_contours(cnts)
            pixelsPerMetric = None
            dimB = 0
            orig = None
            # loop over the contours individually
            for c in cnts:
                # if the contour is not sufficiently large, ignore it
                if cv2.contourArea(c) < 100:
                    continue

                # compute the rotated bounding box of the contour
                orig = image.copy()
                box = cv2.minAreaRect(c)
                box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
                box = np.array(box, dtype="int")

                box = perspective.order_points(box)
                cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)

                # loop over the original points and draw them
                for (x, y) in box:
                    cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)

                (tl, tr, br, bl) = box
                (tltrX, tltrY) = midpoint(tl, tr)
                (blbrX, blbrY) = midpoint(bl, br)

                (tlblX, tlblY) = midpoint(tl, bl)
                (trbrX, trbrY) = midpoint(tr, br)


                cv2.circle(orig, (int(tlblX), int(tlblY)), 5, (255, 0, 0), -1)
                cv2.circle(orig, (int(trbrX), int(trbrY)), 5, (255, 0, 0), -1)

                cv2.line(orig, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),
                         (255, 0, 255), 2)

                dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
                dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))
                # print("dB = ", dB)
                if pixelsPerMetric is None:
                    pixelsPerMetric = dB / 11.67

                dimA = dA / pixelsPerMetric
                dimB = dB / pixelsPerMetric
                dimA *= 25.4
                dimB *= 25.4



            # cv2.putText(orig, "{:.2f}mm".format(dimB),
            #             (int(trbrX - 100), int(trbrY - 20)), cv2.FONT_HERSHEY_SIMPLEX,
            #             0.60, (100, 0, 160), 2)


            # print('dimA = ', dimA)
            # print('dimB = ', dimB)
            val = []
            for i in range(10):
                val.append(dimB)
            val.sort()
            print("val = ", val[0])

            display = orig
            if not self.Test:
                return val[0], orig
            else:

                return val[0], [orig, cv2.cvtColor(edged, cv2.COLOR_GRAY2BGR), display]

        except Exception as e:
             print(e)

    def cam0_test(self, image):
        # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = image
        return 146, gray

    def cam0_operation(self, img):
        try:

            # if self.Live:
            if self.Video:
                time.sleep(0.7)
                print("sleep over")
                res, final = self.side_camera_result(img)

                # res, final = self.cam0_test(img)


                if type(final) is not list:
                        resize_threshold = float("%.2f" % (self.resize / 100))
                        image = cv2.resize(final, (0, 0), None, resize_threshold, resize_threshold)
                        # image = final
                        # working_image = cv2.rotate(working_image, 0)
                        QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                                     "frame", image)

                        self.data = "%.2f\n"%(res)
                        QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number, "data",
                                     self.data)
                else:
                    resize_threshold = float("%.2f" % (self.resize / 100))
                    image1 = cv2.resize(final[0], (0, 0), None, resize_threshold, resize_threshold)

                    resize_threshold2 = float("%.2f" % (self.resize2 / 100))
                    image2 = cv2.resize(final[1], (0, 0), None, resize_threshold2, resize_threshold2)

                    resize_threshold3 = float("%.2f" % (self.resize3 / 100))
                    image3 = cv2.resize(final[2], (0, 0), None, resize_threshold3, resize_threshold3)
                    if type(res) is int:
                        QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                                     "test", [image1, image2, image3])
                    else:
                        QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                                     "test", [image1, image2, image3])

        except Exception as e:
            print(e)

    def get_frame_live(self):
        try:
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            time.sleep(1)
            print(self.serial_number, " > grabing", self.camera.IsGrabbing())
            while self.camera.IsGrabbing() and self.Live:
                grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    image = self.converter.Convert(grabResult)
                    frame = image.GetArray()

                    if self.serial_number == self.config_js_data["cam0"]["serial_number"]:
                           self.cam0_operation(frame)

                grabResult.Release()
            self.camera.StopGrabbing()
        except Exception as e:
            print("timeout error\n", e)
            self.camera_flag = False
            QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number, "state", False)

    def record_video(self):
        self.video_setting = None
        while self.Record:
            try:
                self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
                time.sleep(1)
                print(self.serial_number, "grabing", self.camera.IsGrabbing())
                while self.camera.IsGrabbing() and self.Record:
                    grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                    if grabResult.GrabSucceeded():
                        image = self.converter.Convert(grabResult)
                        frame = image.GetArray()
                        if self.video_setting is None:
                            self.video_setting = False
                            fshape = frame.shape
                            fheight = fshape[0]
                            fwidth = fshape[1]
                            fourcc = cv2.VideoWriter_fourcc(*'DIVX')
                            print("writer initaite")
                            self.writer = cv2.VideoWriter('{}/{}.avi'.format(self.video_file_path, self.serial_number), fourcc, 25.0, (fwidth, fheight))

                        self.writer.write(frame)
                        # time.sleep(self.video_speed / 1000)
                        QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                                     "frame", frame)

                    grabResult.Release()

                self.camera.StopGrabbing()
            except Exception as e:
                print("timeout error", e)
                self.camera_flag = False
                QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number, "state",
                             False)

    def end_job(self):
        self.job_done.set()

    def play_video(self):

        while self.Video:
                ret, video_frame = self.video_obj.read()
                if ret:
                    time.sleep(self.video_speed/1000)
                    # cv2.waitKey(self.video_speed)

                    if self.serial_number == self.config_js_data["cam0"]["serial_number"]:
                        self.cam0_operation(video_frame)
                    # resize_threshold = float("%.2f" % (self.resize / 100))
                    # resized_image = cv2.resize(video_frame, (0, 0), None, resize_threshold, resize_threshold)

                    # QObject.emit(self.qt_object, SIGNAL("cam_{}".format(self.serial_number)), self.serial_number,
                    #              "frame", resized_image)
                else:
                    self.video_obj.open(self.video_file)
                    print('no video')

    def run(self):
        while not self.job_done.is_set():
                if self.Live:
                    if self.camera_flag:
                        self.get_frame_live()
                    else:
                        self.scan_device()
                        time.sleep(5)
                elif self.Video:
                        self.play_video()
                elif self.Record:
                        self.record_video()


class cameraHandler(QMainWindow):
    def __init__(self, parent):
        super(cameraHandler, self).__init__(parent)

        cam = "cam0"
        self.cam0_serialNumber = self.parent().config_js_data[cam]["serial_number"]
        self.parent().gbCam_0.setTitle("Camera - {}".format(self.cam0_serialNumber))
        self.parent().btnCam_0.setText("CAM_{}".format(self.cam0_serialNumber))
        self.cam0 = CameraControl0(cam)
        QObject.connect(self.cam0.qt_object, SIGNAL('cam_{}'.format(self.cam0_serialNumber)), self.camera_handler)
        self.cam0.start()

        self.active_cam = "cam0"
        self.parent().swParameter.setCurrentWidget(self.parent().parm_cam_0)
        self.measure_flag = False
        self.auto_flag = True
        self.file_flag = False
        self.file_name = "test1"
        self.file_path = "resources/data/spool_{0}_{1}.txt".format(date.now().date(), self.file_name)
        # self.file = open(file_path, "w")

    def btnToolHandler(self, btn, state):
        btn_text = btn.text()
        if "CAM" in btn_text:
            btn_name = btn_text.split('_')[1]
            if btn_name == self.cam0_serialNumber:
                self.parent().swParameter.setCurrentWidget(self.parent().parm_cam_0)
                self.active_cam = "cam0"

        else:
            cam = getattr(self, self.active_cam)
            if btn_text == "Reset":
                self.cam0.reset_all()
                # self.timer_object.stop()
                # self.parent().plc_handler.reg_reset()
                # self.timers_control("reset")
                self.object_count_new = 0
                self.object_count_old = 0
                # self.timer_object.start()
                print("reset_all")

            elif btn_text == "Manual":
                if btn.isChecked():
                    print("Manual Mode On")
                    mbus.manual_mode()
                    mbus.stop_plc()
                    self.set_file_flag()

            elif btn_text == "Start":
                btn.setText("Stop")
                mbus.auto_mode()
                self.parent().lbl_warning.clear()
                mbus.start_plc()
                # m1_curr = mbus.m1_current()
                # if not m1_curr == 1:
                #     mbus.stop_plc()

                self.set_file_flag()

            elif btn_text == "Stop":
                btn.setText("Start")
                mbus.stop_plc()
                self.clear_file_flag()
                # print("stop")

            elif btn_text == "Measure":

                if btn.isChecked():
                    print("Measure view on")
                    self.parent().lbl_mode.setStyleSheet('color: green')
                    self.parent().lbl_mode.setText("MEASUREMENT VIEW")
                    self.measure_flag = True
                else:
                    print("Measure view off")
                    self.parent().lbl_mode.setStyleSheet('color: red')
                    self.parent().lbl_mode.setText("LIVE")
                    self.measure_flag = False

            elif btn_text == "Test":
                self.cam0.Test = False
                if btn.isChecked():
                    print("test on")
                    cam.Test = True

                    self.parent().swView.setCurrentWidget(self.parent().test_view)
                    self.parent().gpCameraTools.setEnabled(False)
                else:
                    print("test off")
                    cam.Test = False
                    self.parent().swView.setCurrentWidget(self.parent().live_view)
                    self.parent().gpCameraTools.setEnabled(True)
            else:
                cam.tool_trigger(btn_text)

    def slider_handler_click(self, slider, value):
        if "Cam" in slider.objectName():
            cam = slider.objectName()[2:6]
            if cam == "Cam0":
                cam_id = slider.objectName().split('_')[1]
                lb_name = self.parent().lb_prefix_cam0 + cam_id
                lb = getattr(self.parent(), lb_name)
                lb_text = lb.text().split('-')[0] + "-" + str(value)
                lb.setText(lb_text)

    def set_file_flag(self):
        self.file_flag = True

    def clear_file_flag(self):
        self.file_flag = False

    def slider_handler_release(self, slider):

        if "Cam" in slider.objectName():
            cam = slider.objectName()[2:6]
            if cam == "Cam0":
                value = slider.value()
                cam_id = slider.objectName().split('_')[1]
                lb_name = self.parent().lb_prefix_cam0 + cam_id
                lb = getattr(self.parent(), lb_name)
                lb_par = lb.text().split('-')[0]
                lb_text = lb_par+"-"+str(value)
                lb.setText(lb_text)
                print("cam0", lb_text)
                self.parent().update_camera_setting("cam0", int(cam_id), "val", value)
                setattr(self.cam0, lb_par, value)

    def set_file_name(self):
        self.file_name = self.parent().val_file_name.toPlainText()
        self.file_path = "resources/data/spool_{0}_{1}.txt".format(date.now().date(), self.file_name)
        print("file name changed to \n {0}", self.file_path)

    def save_data(self, val):

        try:
            print("measure_flag = ", self.measure_flag)

            if not self.measure_flag and self.file_flag:
                with open(self.file_path, "a+") as file:
                    file.write("{0} : {1}\n".format(date.now().time(), val))
                    print("saved :- {0} : {1}\n".format(date.now().time(), val))

        except Exception as e:
            print("Error from file is : {0}".format(e))

    def camera_handler(self, camera_num=None, sig=None, val=None):
        if camera_num == self.cam0_serialNumber:
            if sig == "state":
                if not val:
                    self.parent().lbCam_0.setText("cam_{}\nDisconnected".format(camera_num))
            elif sig == "frame":
                self.showlogo_bycv(self.parent().lbCam_0, val)
            elif sig == "working_image":
                self.showlogo_bycv(self.parent().lbCam_0, val)
            elif sig == "data":

                self.parent().val_mstrwdt.setStyleSheet('color: green')
                act_wdth = float(self.parent().val_awdth.toPlainText())
                act_tol = float(self.parent().val_actol.toPlainText())
                min_tol = float(act_wdth - float(self.parent().n_tolerance.toPlainText()))
                max_tol = float(act_wdth + float(self.parent().p_tolerance.toPlainText()))
                # print("val from data write = ", val)
                # print("min_tol= ",min_tol)
                # print("max_tol =", max_tol)

                if act_tol > 0.5:
                    val = float(val) - float(act_tol)
                    if float(val) > float(max_tol) or float(val) < float(min_tol):
                        # print("val from if = ", val)
                        val = str(val)
                        self.parent().val_mstrwdt.setText(val)
                        self.parent().val_mstrwdt.setStyleSheet('color: red')
                        self.file_flag = False
                        self.parent().lbl_warning.clear()
                        self.parent().lbl_warning.setText("Spool Width is not Equal to\n Actual Width"
                                                          "\n Width = {0}".format(val))
                        self.parent().lbl_warning.setStyleSheet('color: red')
                        mbus.stop_plc()

                    else:
                        self.parent().val_mstrwdt.clear()
                        self.parent().val_mstrwdt.setText(val)
                        self.parent().val_mstrwdt.setStyleSheet('color: green')

                self.save_data(val)
                spool_complete = mbus.spool()
                if spool_complete == 1:
                    mbus.stop_plc()
                    self.parent().lbl_warning.clear()
                    self.parent().lbl_warning.setText("Spool Completed!!!")
                    self.parent().lbl_warning.setStyleSheet('color: red')
                if float(val) > float(max_tol) + 0.3 or float(val) < float(min_tol) - 1:

                    # if float(val) == 244.88:
                    #     ls = [245.33, 245.66, 246.55, 246.28]
                    #     random.shuffle(ls)
                    #     self.parent().val_mstrwdt.setText(ls[0])

                    self.parent().val_mstrwdt.setText(val)
                    self.parent().val_mstrwdt.setStyleSheet('color: red')
                    self.file_flag = False
                    self.parent().lbl_warning.clear()
                    self.parent().lbl_warning.setText("Spool Width is not Equal to \n Actual Width"
                                                      "\n Width = {0}".format(val))
                    self.parent().lbl_warning.setStyleSheet('color: red')
                    mbus.stop_plc()

                else:
                    self.parent().val_mstrwdt.clear()
                    self.parent().val_mstrwdt.setText(val)
                    self.parent().val_mstrwdt.setStyleSheet('color: green')
            elif sig == "test":
                if type(val) is list:
                    # self.parent().lb_test_0.setText(val)
                    self.showlogo_bycv(self.parent().lb_test_1, val[1])
                    self.showlogo_bycv(self.parent().lb_test_2, val[2])
                    # self.showlogo_bycv(self.parent().lb_test_3, val[3])
                else:
                    self.showlogo_bycv(self.parent().lbCam_0, val)

    def showlogo_bycv(self, obj, frame, path=None):
        if path:
            img = cv2.imread(frame)
            frame = img

        # frame = cv2.resize(frame, (obj.size().width(), obj.size().height()), interpolation=cv2.INTER_AREA)

        re_img = QImage(frame, frame.shape[1], frame.shape[0],
                              frame.strides[0], QImage.Format_RGB888).rgbSwapped()
        pix_img = QPixmap.fromImage(re_img)
        # sc_pix = pix_img.scaled(, Qt.KeepAspectRatio)
        obj.setPixmap(pix_img)
