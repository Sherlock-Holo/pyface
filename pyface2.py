#!/usr/bin/env python3

import cv2
import sys

face_patterns = cv2.CascadeClassifier("/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml")
sample_img = sys.argv[1]
#detect_img = sys.argv[2]
sample = cv2.imread(sample_img)
faces = face_patterns.detectMultiScale(sample, scaleFactor = 1.2, minNeighbors = 2, minSize = (100, 100))

for x, y, w, h in faces:
    cv2.rectangle(sample, (x, y), (x + w, y + h), (0, 255), 2)

#cv2.imwrite(detect_img, sample)

while sample.shape[0] >= 1920 or sample.shape[1] >= 1080:
    sample = cv2.resize(sample, None, fx = 0.5, fy = 0.5, interpolation = cv2.INTER_CUBIC)

cv2.imshow('Face', sample)
cv2.waitKey(0)
