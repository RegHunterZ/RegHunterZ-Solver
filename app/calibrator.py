
from PyQt6 import QtWidgets, QtGui, QtCore
import os, json
from .utils_cv import imread_unicode, cv_to_qimage

SEATS_6 = ["BTN","SB","BB","UTG","MP","CO"]
SEATS_9 = ["BTN","SB","BB","UTG","UTG1","MP","MP1","CO","HJ"]

class RectAnno:
    def __init__(self, rect: QtCore.QRectF, target: str = "", color: QtGui.QColor = QtGui.QColor(0,180,255)):
        self.rect = rect
        self.target = target
        self.color = color

class CalibCanvas(QtWidgets.QWidget):
    rectAdded = QtCore.pyqtSignal(int)
    rectDeleted = QtCore.pyqtSignal(int)
    selectionChanged = QtCore.pyqtSignal(int)

    _UNDO_MAX = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = QtGui.QImage()
        self.viewScale = 1.0
        self.annos = []
        self.selected = -1
        self.dragging = False
        self.startPos = QtCore.QPointF()
        self._undo = []

    def load_image(self, path: str):
        self.image = cv_to_qimage(imread_unicode(path))
        self.updateGeometry()
        self.update()

    def sizeHint(self):
        return QtCore.QSize(960, 720)

    def paintEvent(self, e):
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor(20,20,20))
        if not self.image.isNull():
            scaled = self.image.scaled(self.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
            p.drawImage(QtCore.QPoint(0,0), scaled)
            if self.image.width():
                self.viewScale = scaled.width() / self.image.width()
        pen_sel = QtGui.QPen(QtGui.QColor(255,200,0), 2)
        pen = QtGui.QPen(QtGui.QColor(0,180,255), 2, QtCore.Qt.PenStyle.DashLine)
        for i, a in enumerate(self.annos):
            p.setPen(pen_sel if i == self.selected else pen)
            p.drawRect(a.rect)

    def mousePressEvent(self, e: QtGui.QMouseEvent):
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            self.dragging = True
            self.startPos = e.position()
        elif e.button() == QtCore.Qt.MouseButton.RightButton:
            for i, a in enumerate(self.annos):
                if a.rect.contains(e.position()):
                    self.selected = i
                    self.selectionChanged.emit(i)
                    self.update()
                    break

    def mouseMoveEvent(self, e: QtGui.QMouseEvent):
        if self.dragging:
            self._tempRect = QtCore.QRectF(self.startPos, e.position()).normalized()
            self.update()

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent):
        if self.dragging and e.button() == QtCore.Qt.MouseButton.LeftButton:
            self.dragging = False
            r = QtCore.QRectF(self.startPos, e.position()).normalized()
            # save undo
            self._undo.append([RectAnno(a.rect, a.target, a.color) for a in self.annos])
            self._undo = self._undo[-self._UNDO_MAX:]
            self.annos.append(RectAnno(r))
            idx = len(self.annos) - 1
            self.selected = idx
            self.rectAdded.emit(idx)
            self.selectionChanged.emit(idx)
            self.update()

    def keyPressEvent(self, e: QtGui.QKeyEvent):
        if e.key() == QtCore.Qt.Key.Key_Z and (e.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier):
            if self._undo:
                self.annos = self._undo.pop()
                self.selected = -1
                self.selectionChanged.emit(-1)
                self.update()
            return
        if e.key() in (QtCore.Qt.Key.Key_Delete, QtCore.Qt.Key.Key_Backspace) and 0 <= self.selected < len(self.annos):
            self._undo.append([RectAnno(a.rect, a.target, a.color) for a in self.annos])
            self._undo = self._undo[-self._UNDO_MAX:]
            self.annos.pop(self.selected)
            self.selected = -1
            self.rectDeleted.emit(-1)
            self.selectionChanged.emit(-1)
            self.update()
        else:
            super().keyPressEvent(e)

class Calibrator(QtWidgets.QDialog):
    def __init__(self, image_path: str, profiles_json: str, base_profile: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kalibrálás")
        self.resize(1280, 800)
        self.image_path = image_path
        self.profiles_json = profiles_json

        self.canvas = CalibCanvas(self)
        self.canvas.load_image(image_path)

        right = QtWidgets.QWidget(self)
        vr = QtWidgets.QVBoxLayout(right)

        form = QtWidgets.QFormLayout()
        self.profile_name = QtWidgets.QLineEdit(base_profile + "_custom" if base_profile else "kkpoker_custom")
        form.addRow("Új profil neve:", self.profile_name)

        self.model_sel = QtWidgets.QComboBox()
        self.model_sel.addItems(["6-max", "9-max"])
        self.model_sel.setCurrentIndex(0 if "6" in (base_profile or "6") else 1)
        form.addRow("Asztal típusa:", self.model_sel)

        self.target_sel = QtWidgets.QComboBox()
        self._reload_targets()
        form.addRow("Cél hozzárendelés:", self.target_sel)

        add_row = QtWidgets.QHBoxLayout()
        self.manual_target = QtWidgets.QLineEdit()
        self.manual_target.setPlaceholderText("Pl.: BTN.stack vagy HH.flop")
        btn_add_manual = QtWidgets.QPushButton("Hozzáadás")
        btn_add_manual.clicked.connect(self._add_manual_target)
        add_row.addWidget(self.manual_target)
        add_row.addWidget(btn_add_manual)
        form.addRow("Új cél (kézzel):", add_row)

        btn_assign = QtWidgets.QPushButton("Kijelölt doboz → Cél")
        btn_assign.clicked.connect(self._assign_selected)
        btn_delete_row = QtWidgets.QPushButton("Kijelölt cél törlése")
        btn_delete_row.clicked.connect(self._delete_selected_row)
        btn_save = QtWidgets.QPushButton("Mentés profilba")
        btn_save.clicked.connect(self._save_profile)
        hint = QtWidgets.QLabel("Tipp: Bal klikk+húzás új doboz. Jobb klikk kijelöl. Delete/Backspace töröl. Ctrl+Z visszavon.")

        self.list = QtWidgets.QTableWidget(0, 2)
        self.list.setHorizontalHeaderLabels(["Cél", "Rel. koordináták (x,y,w,h)"])
        self.list.horizontalHeader().setStretchLastSection(True)
        self.list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        vr.addLayout(form)
        vr.addWidget(btn_assign)
        vr.addWidget(btn_delete_row)
        vr.addWidget(self.list, 1)
        vr.addWidget(btn_save)
        vr.addWidget(hint)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.canvas, 2)
        layout.addWidget(right, 1)

        self.canvas.rectAdded.connect(self._on_rect_added)

    def _reload_targets(self):
        seats = SEATS_6 if self.model_sel.currentIndex() == 0 else SEATS_9
        targets = ["pot", "Dealer.button", "HH.preflop", "HH.flop", "HH.turn", "HH.river"] + [f"{s}.stack" for s in seats]
        self.target_sel.clear()
        self.target_sel.addItems(targets)

    def _add_manual_target(self):
        t = self.manual_target.text().strip()
        if not t:
            return
        if self.target_sel.findText(t) == -1:
            self.target_sel.addItem(t)
        self.target_sel.setCurrentText(t)
        self.manual_target.clear()

    def _on_rect_added(self, idx: int):
        pass

    def _assign_selected(self):
        idx = self.canvas.selected if self.canvas.selected >= 0 else (len(self.canvas.annos) - 1)
        if not (0 <= idx < len(self.canvas.annos)):
            QtWidgets.QMessageBox.information(self, "Nincs kijelölés", "Válassz dobozt balról (jobb klikk).")
            return
        target = self.target_sel.currentText().strip()
        if not target:
            return
        self.canvas.annos[idx].target = target
        rel = self.to_rel(self.canvas.annos[idx].rect)
        self._upsert_table_row(target, rel)
        self.canvas.update()

    def to_rel(self, rect: QtCore.QRectF):
        W = self.canvas.width()
        H = self.canvas.height()
        x = max(0.0, rect.left()/W)
        y = max(0.0, rect.top()/H)
        w = max(0.0, rect.width()/W)
        h = max(0.0, rect.height()/H)
        return (round(x,2), round(y,2), round(w,2), round(h,2))

    def _upsert_table_row(self, target: str, rel):
        for r in range(self.list.rowCount()):
            if self.list.item(r, 0).text() == target:
                self.list.setItem(r, 1, QtWidgets.QTableWidgetItem(str(rel)))
                return
        r = self.list.rowCount()
        self.list.insertRow(r)
        self.list.setItem(r, 0, QtWidgets.QTableWidgetItem(target))
        self.list.setItem(r, 1, QtWidgets.QTableWidgetItem(str(rel)))

    def _delete_selected_row(self):
        rows = self.list.selectionModel().selectedRows()
        for idx in rows:
            self.list.removeRow(idx.row())

    def _save_profile(self):
        name = self.profile_name.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Hiányzó név", "Adj nevet az új profilnak.")
            return
        seats = {}
        pot_rel = None
        dealer_rel = None
        hh_pre = None
        hh_fl = None
        hh_tu = None
        hh_ri = None

        for r in range(self.list.rowCount()):
            target = self.list.item(r, 0).text()
            rel_txt = self.list.item(r, 1).text()
            try:
                rel = eval(rel_txt)
            except Exception:
                continue
            key = target.lower()
            if target == "pot":
                pot_rel = rel
            elif key == "dealer.button":
                dealer_rel = rel
            elif key == "hh.preflop":
                hh_pre = rel
            elif key == "hh.flop":
                hh_fl = rel
            elif key == "hh.turn":
                hh_tu = rel
            elif key == "hh.river":
                hh_ri = rel
            elif "." in target:
                seat, field = target.split(".", 1)
                seats.setdefault(seat, {})[field] = rel

        prof = {
            "table": "6-max" if self.model_sel.currentIndex() == 0 else "9-max",
            "pot": pot_rel,
            "dealer": dealer_rel,
            "hh_preflop": hh_pre,
            "hh_flop": hh_fl,
            "hh_turn": hh_tu,
            "hh_river": hh_ri,
            "seats": seats
        }
        os.makedirs(os.path.dirname(self.profiles_json), exist_ok=True)
        try:
            data = {}
            if os.path.isfile(self.profiles_json):
                with open(self.profiles_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data[name] = prof
            with open(self.profiles_json, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Hiba", f"Nem sikerült menteni: {e}")
            return
        QtWidgets.QMessageBox.information(self, "Kész", f"Profil elmentve: {name}")
        self.accept()
