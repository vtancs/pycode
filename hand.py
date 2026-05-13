"""
Hand Gesture Control WITHOUT MediaPipe
--------------------------------------

Features:
✔ Move mouse cursor
✔ Scroll up/down
✔ Left click
✔ No MediaPipe dependency
✔ PyAutoGUI fail-safe fixed
✔ Cursor smoothing
✔ Edge protection

Controls:
1 Finger  -> Move Cursor
2 Fingers -> Scroll Up
3 Fingers -> Scroll Down
4 Fingers -> Left Click

Press Q to quit
"""

import cv2
import numpy as np
import pyautogui
from math import hypot

# =====================================
# PYAUTO GUI SAFETY
# =====================================
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.01

# =====================================
# CAMERA
# =====================================
cap = cv2.VideoCapture(0)

# =====================================
# SCREEN SIZE
# =====================================
screen_w, screen_h = pyautogui.size()

# =====================================
# SMOOTHING VARIABLES
# =====================================
prev_x = 0
prev_y = 0

# =====================================
# MAIN LOOP
# =====================================
while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Flip horizontally
    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    # =====================================
    # REGION OF INTEREST
    # =====================================
    roi = frame[100:400, 100:400]

    cv2.rectangle(
        frame,
        (100, 100),
        (400, 400),
        (0, 255, 0),
        2
    )

    # =====================================
    # HSV CONVERSION
    # =====================================
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # =====================================
    # SKIN MASK
    # =====================================
    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
    upper_skin = np.array([20, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    # Blur mask
    mask = cv2.GaussianBlur(mask, (5, 5), 0)

    # Morphological operations
    kernel = np.ones((3, 3), np.uint8)

    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.erode(mask, kernel, iterations=1)

    # =====================================
    # FIND CONTOURS
    # =====================================
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if contours:

        # Largest contour
        cnt = max(contours, key=cv2.contourArea)

        area = cv2.contourArea(cnt)

        # Ignore small contours
        if area > 3000:

            # Draw contour
            cv2.drawContours(
                roi,
                [cnt],
                -1,
                (0, 255, 0),
                2
            )

            # =====================================
            # CONVEX HULL
            # =====================================
            hull = cv2.convexHull(cnt)

            cv2.drawContours(
                roi,
                [hull],
                -1,
                (255, 0, 0),
                2
            )

            # =====================================
            # CONVEXITY DEFECTS
            # =====================================
            hull2 = cv2.convexHull(
                cnt,
                returnPoints=False
            )

            defects = cv2.convexityDefects(
                cnt,
                hull2
            )

            finger_count = 0

            if defects is not None:

                for i in range(defects.shape[0]):

                    s, e, f, d = defects[i, 0]

                    start = tuple(cnt[s][0])
                    end = tuple(cnt[e][0])
                    far = tuple(cnt[f][0])

                    # Side lengths
                    a = hypot(
                        end[0] - start[0],
                        end[1] - start[1]
                    )

                    b = hypot(
                        far[0] - start[0],
                        far[1] - start[1]
                    )

                    c = hypot(
                        end[0] - far[0],
                        end[1] - far[1]
                    )

                    # Avoid division by zero
                    if b * c == 0:
                        continue

                    # Cosine rule
                    angle = np.arccos(
                        (b**2 + c**2 - a**2) / (2 * b * c)
                    ) * 57

                    # Detect fingers
                    if angle <= 90:

                        finger_count += 1

                        cv2.circle(
                            roi,
                            far,
                            5,
                            (0, 0, 255),
                            -1
                        )

                    cv2.line(
                        roi,
                        start,
                        end,
                        (255, 255, 0),
                        2
                    )

            # =====================================
            # GESTURES
            # =====================================

            # ---------------------------------
            # 1 Finger -> Move Cursor
            # ---------------------------------
            if finger_count == 1:

                x, y, ww, hh = cv2.boundingRect(cnt)

                center_x = x + ww // 2
                center_y = y + hh // 2

                # Draw center
                cv2.circle(
                    roi,
                    (center_x, center_y),
                    8,
                    (255, 0, 255),
                    -1
                )

                # Convert ROI -> Screen coordinates
                screen_x = np.interp(
                    center_x,
                    [0, 300],
                    [0, screen_w]
                )

                screen_y = np.interp(
                    center_y,
                    [0, 300],
                    [0, screen_h]
                )

                # Smooth movement
                curr_x = prev_x + (screen_x - prev_x) / 5
                curr_y = prev_y + (screen_y - prev_y) / 5

                # Prevent corners
                safe_x = max(
                    10,
                    min(screen_w - 10, curr_x)
                )

                safe_y = max(
                    10,
                    min(screen_h - 10, curr_y)
                )

                pyautogui.moveTo(safe_x, safe_y)

                prev_x = curr_x
                prev_y = curr_y

                cv2.putText(
                    frame,
                    "MOVE CURSOR",
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    3
                )

            # ---------------------------------
            # 2 Fingers -> Scroll Up
            # ---------------------------------
            elif finger_count == 2:

                pyautogui.scroll(300)

                cv2.putText(
                    frame,
                    "SCROLL UP",
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 0, 0),
                    3
                )

            # ---------------------------------
            # 3 Fingers -> Scroll Down
            # ---------------------------------
            elif finger_count == 3:

                pyautogui.scroll(-300)

                cv2.putText(
                    frame,
                    "SCROLL DOWN",
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    3
                )

            # ---------------------------------
            # 4 Fingers -> Left Click
            # ---------------------------------
            elif finger_count >= 4:

                pyautogui.click()

                cv2.putText(
                    frame,
                    "LEFT CLICK",
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 0),
                    3
                )

    # =====================================
    # DISPLAY WINDOWS
    # =====================================
    cv2.imshow("Mask", mask)
    cv2.imshow("Hand Gesture AI", frame)

    key = cv2.waitKey(1)

    # Quit
    if key == ord('q'):
        break

# =====================================
# CLEANUP
# =====================================
cap.release()
cv2.destroyAllWindows()