# -*- coding: utf-8 -*-
"""
Inject per-row Range buttons next to action widgets across all streets.
This keeps the existing range-selector function (openRangeSelector or similar).
We look for a function named openRangeSelector(self, street, position, action)
in the host dialog. If not found, we fall back to open_range_selector.
Call `attach_per_row_range_buttons(dialog)` right after the dialog builds its tabs.
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt

def _guess_open_fn(host):
    for name in ("openRangeSelector", "open_range_selector", "onOpenRange", "open_range"):
        fn = getattr(host, name, None)
        if callable(fn):
            return fn
    return None

def attach_per_row_range_buttons(host):
    """
    Host contract (best-effort):
      - host has `tabs` (QTabWidget)
      - each tab has a layout with rows for positions, and somewhere a current action widget per row,
        typically a QComboBox named like 'action' or similar.
      - We add a small "R" button to the right of the action widget on each row.
    """
    open_fn = _guess_open_fn(host)
    if open_fn is None:
        return  # can't wire

    try:
        tabw = host.tabs
    except Exception:
        return

    # Discover rows by scanning tab children: for each row, find a combobox and a label that looks like a position.
    POS_HINTS = ("UTG","HJ","CO","BTN","SB","BB")
    STREETS = []
    for i in range(tabw.count()):
        STREETS.append(tabw.tabText(i))

    for idx, street in enumerate(STREETS):
        tab = tabw.widget(idx)
        # For each child layout row: find a combo named/typed like action
        combos = tab.findChildren(type(getattr(host, "action_combo_type", None)) or __import__("PyQt6.QtWidgets").QtWidgets.QComboBox)
        # fallback: all QComboBox
        if not combos:
            from PyQt6.QtWidgets import QComboBox
            combos = tab.findChildren(QComboBox)
        # Find labels that contain position hints
        from PyQt6.QtWidgets import QLabel, QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLayout
        labels = tab.findChildren(QLabel)

        pos_map = {}  # position -> [combos in same row order]
        for lab in labels:
            txt = lab.text().strip()
            if txt in POS_HINTS:
                pos_map[txt] = []

        # crude row grouping: go through combos in visual order and map to nearest preceding position label
        current_pos = None
        for combo in combos:
            # walk up to row container
            pos_label = None
            w = combo
            # find sibling labels
            sib_labels = w.parent().findChildren(QLabel)
            # choose closest with pos hint
            for lab in sib_labels:
                if lab.text().strip() in POS_HINTS:
                    pos_label = lab.text().strip()
                    break
            if pos_label:
                current_pos = pos_label
            if current_pos and current_pos in pos_map:
                pos_map[current_pos].append(combo)

        # Now attach an R button next to each combo (one per row).
        for pos, combos_in_row in pos_map.items():
            if not combos_in_row:
                continue
            action_widget = combos_in_row[0]  # first combo considered the action selector of the row
            parent = action_widget.parent()
            # Create button
            btn = QPushButton("R", parent)
            btn.setFixedWidth(36)
            btn.setToolTip("Range választó – %s / %s" % (street, pos))
            # Place the button to the right: if parent layout is grid or hbox, insert next to combo
            # Best-effort insertion
            inserted = False
            for lay_attr in ("layout", "layout()"):
                try:
                    layout = parent.layout()
                except Exception:
                    layout = None
                if layout is None:
                    continue
                from PyQt6.QtWidgets import QGridLayout, QHBoxLayout
                if isinstance(layout, QGridLayout):
                    # find combo position
                    for r in range(layout.rowCount()):
                        for c in range(layout.columnCount()):
                            item = layout.itemAtPosition(r, c)
                            if item and item.widget() is action_widget:
                                layout.addWidget(btn, r, c+1, alignment=Qt.AlignmentFlag.AlignLeft)
                                inserted = True
                                break
                        if inserted:
                            break
                elif isinstance(layout, QHBoxLayout):
                    # add after combo
                    # find index
                    for i in range(layout.count()):
                        if layout.itemAt(i).widget() is action_widget:
                            layout.insertWidget(i+1, btn, alignment=Qt.AlignmentFlag.AlignLeft)
                            inserted = True
                            break
            if not inserted:
                # absolute fallback: just move near the combo
                btn.move(action_widget.x() + action_widget.width() + 6, action_widget.y())

            # wire click
            def _on_click(street=street, pos=pos, aw=action_widget):
                act_text = getattr(aw, "currentText", lambda: "Action")()
                open_fn(street, pos, act_text)
            btn.clicked.connect(_on_click)