import cv2
import sys


face_patterns = cv2.CascadeClassifier("/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml")
sample_img = sys.argv[1]
detect_img = sys.argv[2]
sample = cv2.imread(sample_img)
faces = face_patterns.detectMultiScale(sample, scaleFactor = 1.1, minNeighbors = 4, minSize = (100, 100))

for x, y, w, h in faces:
    cv2.rectangle(sample, (x, y), (x + w, y + h), (0, 255), 2)

cv2.imwrite(detect_img, sample)
