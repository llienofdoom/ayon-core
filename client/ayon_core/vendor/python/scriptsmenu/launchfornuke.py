from __future__ import annotations
import scriptsmenu
from qtpy import QtWidgets


def _nuke_main_window():
    """Return Nuke's main window"""
    for obj in QtWidgets.QApplication.topLevelWidgets():
        if (obj.inherits('QMainWindow') and
                    obj.metaObject().className() == 'Foundry::UI::DockMainWindow'):
            return obj
    raise RuntimeError('Could not find Nuke MainWindow instance')


def _nuke_main_menubar():
    """Retrieve the main menubar of the Nuke window"""
    nuke_window = _nuke_main_window()

    # Older PySide2 (e.g. Nuke 13) may not wrap the window as
    # QMainWindow in Python, so .menuBar() is unavailable.
    # Use findChild as a fallback to support both old and new versions.
    if hasattr(nuke_window, 'menuBar'):
        return nuke_window.menuBar()

    menu_bar = nuke_window.findChild(QtWidgets.QMenuBar)
    if menu_bar is None:
        raise RuntimeError('Could not find Nuke menu bar')
    return menu_bar


def main(title="Scripts"):
    nuke_main_bar = _nuke_main_menubar()
    for nuke_bar in nuke_main_bar.children():
        if isinstance(nuke_bar, scriptsmenu.ScriptsMenu):
            if nuke_bar.title() == title:
                menu = nuke_bar
                return menu

    menu = scriptsmenu.ScriptsMenu(title=title, parent=nuke_main_bar)
    return menu
