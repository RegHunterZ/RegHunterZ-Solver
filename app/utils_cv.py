import cv2, numpy as np
from PyQt6 import QtGui
def imread_unicode(path: str):
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)
def cv_to_qimage(img):
    if img is None: return QtGui.QImage()
    if len(img.shape)==2:
        h,w = img.shape; return QtGui.QImage(img.data, w, h, w, QtGui.QImage.Format.Format_Grayscale8).copy()
    h,w,_ = img.shape
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return QtGui.QImage(rgb.data, w, h, 3*w, QtGui.QImage.Format.Format_RGB888).copy()
