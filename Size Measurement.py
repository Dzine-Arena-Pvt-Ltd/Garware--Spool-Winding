# import the necessary packages
from scipy.spatial import distance as dist
from imutils import perspective
from imutils import contours
import numpy as np
import imutils
import cv2


# Class for point
class point:
    x = 0
    y = 0


# Points for Left Right Top and Bottom
plL = point()
plR = point()
plU = point()
plD = point()


# For finding midpoint
def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)


def bg_sub(frame):
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    lower_green = np.array([100, 0, 0])
    upper_green = np.array([197, 255, 255])

    mask = cv2.inRange(hsv, lower_green, upper_green)
    mask_inv = cv2.bitwise_not(mask)

    bg = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow('BG_SUB', bg)
    return bg

# cap = cv2.VideoCapture(0)
cv2.namedWindow("Size Of Object", cv2.WINDOW_NORMAL)
image = cv2.imread("test.png")
while(1):

    try:

        # ret, image = cap.read()
        #roi = image1[90:320, 200:420]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        # perform edge detection, then perform a dilation + erosion to
        # close gaps in between object edges
        edged = cv2.Canny(gray, 50, 100)
        edged = cv2.dilate(edged, None, iterations=1)
        edged = cv2.erode(edged, None, iterations=1)

        # find contours in the edge map
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]

        # sort the contours from left-to-right and, then initialize the
        # distance colors and reference object
        (cnts, _) = contours.sort_contours(cnts)
        colors = ((0, 0, 255), (240, 0, 159), (0, 165, 255), (255, 255, 0),
                  (255, 0, 255))
        refObj = None
        pixelsPerMetric = None

        # loop over the contours individually
        for c in cnts:
            # if the contour is not sufficiently large, ignore it
            if cv2.contourArea(c) < 100:
                continue

            # compute the rotated bounding box of the contour
            box = cv2.minAreaRect(c)
            box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
            box = np.array(box, dtype="int")
            box = perspective.order_points(box)
            # compute the center of the bounding box
            cX = np.average(box[:, 0])
            cY = np.average(box[:, 1])

            if refObj is None:
                box1 = np.zeros(box.shape)
                rcX = 0
                rcY = 0
                refObj = (box1, (rcX, rcY),116)

            # draw the contours on the image
            orig = image.copy()

            cv2.drawContours(image, [box.astype("int")], -1, (0, 255, 0), 1)
            cv2.drawContours(image, [refObj[0].astype("int")], -1, (0, 255, 0), 1)

            # stack the reference coordinates and the object coordinates
            # to include the object center
            refCoords = np.vstack([refObj[0], refObj[1]])
            objCoords = np.vstack([box, (cX, cY)])

            # Give them values
            plL.x = box[0][0]
            plL.y = box[0][1]

            plR.x = box[1][0]
            plR.y = box[1][1]

            plU.x = box[2][0]
            plU.y = box[2][1]

            plD.x = box[3][0]
            plD.y = box[3][1]

            # Finding Height and width
            for (x, y) in box:
                cv2.circle(orig, (int(x), int(y)), 3, (0, 0, 255), -1)

            # unpack the ordered bounding box, then compute the midpoint
            # between the top-left and top-right coordinates, followed by
            # the midpoint between bottom-left and bottom-right coordinates
            (tl, tr, br, bl) = box
            (tltrX, tltrY) = midpoint(tl, tr)
            (blbrX, blbrY) = midpoint(bl, br)

            # compute the midpoint between the top-left and top-right points,
            # followed by the midpoint between the top-righ and bottom-right
            (tlblX, tlblY) = midpoint(tl, bl)
            (trbrX, trbrY) = midpoint(tr, br)

            # draw the midpoints on the image
            cv2.circle(orig, (int(tltrX), int(tltrY)), 3, (255, 0, 0), -1)
            cv2.circle(orig, (int(blbrX), int(blbrY)), 3, (255, 0, 0), -1)
            cv2.circle(orig, (int(tlblX), int(tlblY)), 3, (255, 0, 0), -1)
            cv2.circle(orig, (int(trbrX), int(trbrY)), 3, (255, 0, 0), -1)

            # draw lines between the midpoints
            cv2.line(orig, (int(tltrX), int(tltrY)), (int(blbrX), int(blbrY)),
                     (255, 0, 255), 1)
            cv2.line(orig, (int(tlblX), int(tlblY)), (int(trbrX), int(trbrY)),
                     (255, 0, 255), 1)

            # compute the Euclidean distance between the midpoints
            dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
            dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))

            # if the pixels per metric has not been initialized, then
            # compute it as the ratio of pixels to supplied metric
            # (in this case, inches)
            if pixelsPerMetric is None:
                pixelsPerMetric = 116  # This ratio needs to be set manually

            # compute the size of the object
            dimA = dA / pixelsPerMetric
            dimB = dB / pixelsPerMetric
            dimA *= 25.4
            dimB *= 25.4
            if dimA <= 26 and dimA >= 23.9:

                # draw the object sizes on the imagecharm
                cv2.putText(orig, "{:.1f}mm".format(25),
                            (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.60, (0, 0, 220), 1)
                cv2.putText(orig, "{:.1f}mm".format(25),
                            (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.60, (0, 0, 220), 1)
            elif dimB <= 26 and dimA >= 23.9:
                # draw the object sizes on the image
                cv2.putText(orig, "{:.1f}mm".format(25),
                            (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.60, (0, 0, 220), 1)
                cv2.putText(orig, "{:.1f}mm".format(25),
                            (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.60, (0, 0, 220), 1)
            elif dimA <= 21.6 and dimB >= 16.2:
                if dimA > dimB:
                    # draw the object sizes on the image
                    cv2.putText(orig, "{:.1f}mm".format(21),
                                (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.60, (0, 0, 220), 1)
                    cv2.putText(orig, "{:.1f}mm".format(17),
                                (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.60, (0, 0, 220), 1)
                else :
                    # draw the object sizes on the image
                    cv2.putText(orig, "{:.1f}mm".format(17),
                                (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.60, (0, 0, 220), 1)
                    cv2.putText(orig, "{:.1f}mm".format(21),
                                (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.60, (0, 0, 220), 1)
            elif dimA <= 8.3 and dimB >= 7:
                cv2.putText(orig, "{:.1f}mm".format(8),
                            (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.60, (0, 0, 220), 1)
                cv2.putText(orig, "{:.1f}mm".format(8),
                            (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.60, (0, 0, 220), 1)


            else:

                cv2.putText(orig, "{:.1f}mm".format(dimA),
                            (int(tltrX - 15), int(tltrY - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.60, (0, 0, 220), 1)
                cv2.putText(orig, "{:.1f}mm".format(dimB),
                            (int(trbrX + 10), int(trbrY)), cv2.FONT_HERSHEY_SIMPLEX,
                            0.60, (0, 0, 220), 1)
            # show the output image

            cv2.imshow("Size Of Object", orig)

        k = cv2.waitKey(2) & 0xFF
        if k == 27:
            break

    except Exception as e:
        print(e)

cap.release()
cv2.destroyAllWindows()
