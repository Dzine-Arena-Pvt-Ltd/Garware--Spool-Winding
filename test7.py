from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import imutils
import time
import cv2
import numpy as np
import datetime

date = datetime.datetime.today()


def nothing(x):
    pass



def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)


cv2.namedWindow("Trackbars", cv2.WINDOW_NORMAL)

cv2.createTrackbar("line1_left", "Trackbars", 0, 800, nothing)
cv2.createTrackbar("line1_Y", "Trackbars", 0, 800, nothing)
cv2.createTrackbar("line1_right", "Trackbars", 0, 800, nothing)
cv2.createTrackbar("line2_left", "Trackbars", 0, 800, nothing)
cv2.createTrackbar("line2_right", "Trackbars", 0, 800, nothing)
cv2.createTrackbar("line2_Y", "Trackbars", 0, 800, nothing)


cv2.createTrackbar("X", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("Y", "Trackbars", 0, 255, nothing)

cv2.setTrackbarPos("line1_left", "Trackbars", 0)
cv2.setTrackbarPos("line1_right", "Trackbars", 695)
cv2.setTrackbarPos("line2_left", "Trackbars", 0)
cv2.setTrackbarPos("line2_right", "Trackbars", 692)
cv2.setTrackbarPos("line1_Y", "Trackbars", 184)
cv2.setTrackbarPos("line2_Y", "Trackbars", 219)

cv2.setTrackbarPos("X", "Trackbars", 155)
cv2.setTrackbarPos("Y", "Trackbars", 140)


def side_camera_result(image):
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)

        X = cv2.getTrackbarPos("X", "Trackbars")
        Y = cv2.getTrackbarPos("Y", "Trackbars")
        line1_left = cv2.getTrackbarPos("line1_left", "Trackbars")
        line1_right = cv2.getTrackbarPos("line1_right", "Trackbars")
        line2_left = cv2.getTrackbarPos("line2_left", "Trackbars")
        line2_right = cv2.getTrackbarPos("line2_right", "Trackbars")
        line1_Y = cv2.getTrackbarPos("line1_Y", "Trackbars")
        line2_Y = cv2.getTrackbarPos("line2_Y", "Trackbars")

        edged = cv2.Canny(gray, X, Y)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)

        cv2.line(edged, (line1_left, line1_Y), (line1_right, line1_Y),
                 (255, 255, 255), 1)
        cv2.line(edged, (line2_left, line2_Y), (line2_right, line2_Y),
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
                pixelsPerMetric = dB / 11.67125

            dimA = dA / pixelsPerMetric
            dimB = dB / pixelsPerMetric
            dimA *= 25.4
            dimB *= 25.4

        # cv2.putText(orig, "{:.2f}mm".format(dimB),
        #             (int(trbrX - 100), int(trbrY - 20)), cv2.FONT_HERSHEY_SIMPLEX,
        #             0.60, (100, 0, 160), 2)

        # print('dimA = ', dimA)
        # print('dimB = ', dimB)
        val = set()
        for i in range(50):
            val.add(dimB)
            if i not in val:
                val.add(dimB)
        # val.sort()
                print("val = ", val)

        cv2.imshow("Result", orig)
        return val

    except Exception as e:
        print(e)

if __name__ == "__main__":
    cap = cv2.VideoCapture("/home/pankaj/Pankaj Projects/Spool Winding/Final Code/resources/video/40022418.avi")
    file_path = "test7_1.txt"
    while True:
        ret, img = cap.read()
        val1 = side_camera_result(img)
        # val1 = "%.2f" % val1
        # val2 = "%.2f" % val2
        print("val1 = {0}".format(val1))
        with open(file_path, "a+") as file:
            file.write("{0} : {1}\n".format(date.now().time(), val1))
            print("saved :- {0} : {1}\n".format(date.now().time(), val1))

        # time.sleep(0.5)

        k = cv2.waitKey(1) & 0xFF
        if k == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
