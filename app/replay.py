import app.safe as safe
from PyQt6 import QtWidgets, QtGui, QtCore
import os, json
from .ocr_engine import read_table
from .calibrator import Calibrator
from .config_io import load_cfg, save_cfg

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Beállítások"); self.resize(500,150)
        lay=QtWidgets.QFormLayout(self); cfg=load_cfg()
        self.tess=QtWidgets.QLineEdit(safe.get(cfg, "tesseract_cmd","")); btn=QtWidgets.QPushButton("Tallózás...")
        def browse():
            fn,_=QtWidgets.QFileDialog.getOpenFileName(self,"tesseract.exe","","Exe (*.exe)")
            if fn: self.tess.setText(fn)
        btn.clicked.connect(browse)
        hb=QtWidgets.QHBoxLayout(); hb.addWidget(self.tess,1); hb.addWidget(btn); lay.addRow("Tesseract elérési út:", hb)
        bb=QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        def accept_(): cfg=load_cfg(); cfg["tesseract_cmd"]=self.tess.text().strip(); save_cfg(cfg); self.accept()
        bb.accepted.connect(accept_); bb.rejected.connect(self.reject); lay.addRow(bb)

class ReplayWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("KKPoker Replay / OCR"); self.resize(1200,800); self.image_path=None
        central=QtWidgets.QWidget(self); self.setCentralWidget(central); h=QtWidgets.QHBoxLayout(central)
        self.scroll=QtWidgets.QScrollArea(self); self.scroll.setWidgetResizable(True)
        self.image_label=QtWidgets.QLabel("Tölts be egy képet (Fájl → Kép megnyitása)."); self.image_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.image_label); h.addWidget(self.scroll,2)
        right=QtWidgets.QWidget(self); vr=QtWidgets.QVBoxLayout(right)
        self.table=QtWidgets.QTableWidget(0,6,self); self.table.setHorizontalHeaderLabels(["Seat","Stack","Preflop","Flop","Turn","River"]); self.table.horizontalHeader().setStretchLastSection(True)
        vr.addWidget(self.table,1); h.addWidget(right,1)
        self.status=QtWidgets.QStatusBar(self); self.setStatusBar(self.status)
        mbar=self.menuBar(); m_file=mbar.addMenu("Fájl"); act_open=QtGui.QAction("Kép megnyitása",self); act_open.triggered.connect(self.load_image); m_file.addAction(act_open)
        m_tools=mbar.addMenu("Eszközök"); act_run=QtGui.QAction("OCR futtatása",self); act_run.triggered.connect(self.run_ocr); m_tools.addAction(act_run); act_cal=QtGui.QAction("Kalibrálás",self); act_cal.triggered.connect(self.open_calibrator); m_tools.addAction(act_cal)
        m_set=mbar.addMenu("Beállítások"); act_set=QtGui.QAction("Beállítások…",self); act_set.triggered.connect(self.open_settings); m_set.addAction(act_set)
        bottom=QtWidgets.QWidget(self); hb=QtWidgets.QHBoxLayout(bottom); hb.addWidget(QtWidgets.QLabel("Profil:")); self.profile_sel=QtWidgets.QComboBox(self); hb.addWidget(self.profile_sel,1); h.addWidget(bottom,0)
        self._reload_profiles()
    def _profiles_path(self)->str: return os.path.join(os.path.dirname(__file__),"profiles","kkpoker_profiles.json")
    def _reload_profiles(self):
        self.profile_sel.clear()
        try:
            with open(self._profiles_path(),"r",encoding="utf-8") as f: data=json.load(f); self.profile_sel.addItems(list(data.keys()))
        except Exception: self.profile_sel.addItems(["kkpoker_6max"])
    def load_image(self):
        fn,_=QtWidgets.QFileDialog.getOpenFileName(self,"Kép megnyitása","","Images (*.png *.jpg *.jpeg *.bmp)")
        if not fn: return
        self.image_path=fn; pix=QtGui.QPixmap(fn)
        self.image_label.setPixmap(pix if not pix.isNull() else QtGui.QPixmap()); self.status.showMessage(os.path.basename(fn),4000)
    def run_ocr(self):
        if not self.image_path: QtWidgets.QMessageBox.information(self,"Nincs kép","Előbb tölts be egy képernyőképet."); return
        name=self.profile_sel.currentText()
        try:
            out=read_table(self.image_path, self._profiles_path(), name)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self,"OCR hiba",str(e)); return
        seats=safe.get(out, "seats",[]); self.table.setRowCount(len(seats)); hh_by_seat=safe.get(out, "hh_by_seat",{})
        for r,s in enumerate(seats):
            seat=safe.get(s, "name") or safe.get(s, "seat") or ""; stack=safe.get(s, "stack","")
            self.table.setItem(r,0,QtWidgets.QTableWidgetItem(str(seat))); self.table.setItem(r,1,QtWidgets.QTableWidgetItem(str(stack)))
            for j,street in enumerate(["Preflop","Flop","Turn","River"], start=2):
                txt="; ".join(safe.get(hh_by_seat, seat,{}).get(street,[])); self.table.setItem(r,j,QtWidgets.QTableWidgetItem(txt))
        self.status.showMessage("OCR kész.",4000)
    def open_settings(self): dlg=SettingsDialog(self); dlg.exec()
    def open_calibrator(self):
        if not self.image_path: QtWidgets.QMessageBox.information(self,"Nincs kép","Kalibráláshoz előbb tölts be egy asztal-képernyőképet."); return
        dlg=Calibrator(self.image_path, self._profiles_path(), self.profile_sel.currentText(), self)
        if dlg.exec(): self._reload_profiles(); self.status.showMessage("Új profil elmentve. Válaszd ki és futtasd az OCR-t.",6000)
