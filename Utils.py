from PyQt6.QtWidgets import QFrame, QGraphicsOpacityEffect, QFileDialog
from PyQt6.QtCore import QFileInfo

'''
Utility module for common functions used by multiple modules, consolidating the code-base for basic functionality including:
- UI functions; createHDivider() & createVDivider().
- Drag & Drop directory functionality; drag_enter_event() & drop_event.
- Browsing functionality for loading files manually; browse_path
'''

def createHDivider():
    """
    Create a styled horizontal divider with reduced opacity.
    Returns:
        QFrame: A customized divider with specific visual styling.
    """
    divider = QFrame()
    divider.setFrameShape(QFrame.Shape.HLine)
    divider.setFrameShadow(QFrame.Shadow.Sunken)
    opacity_effect = QGraphicsOpacityEffect()
    opacity_effect.setOpacity(0.3)
    divider.setGraphicsEffect(opacity_effect)
    divider.setStyleSheet("""
        QFrame {
            background-color: #0057e7;
            height: 2px;
        }
    """)
    return divider

def createVDivider():
    """
    Create a styled vert divider with reduced opacity.
    Returns:
        QFrame: A customized divider with specific visual styling.
    """
    divider = QFrame()
    divider.setFrameShape(QFrame.Shape.VLine)
    divider.setFrameShadow(QFrame.Shadow.Sunken)
    opacity_effect = QGraphicsOpacityEffect()
    opacity_effect.setOpacity(0.3)
    divider.setGraphicsEffect(opacity_effect)
    divider.setStyleSheet("""
        QFrame {
            background-color: #0057e7;
            height: 2px;
        }
    """)
    return divider


def drag_enter_event(event):
    if event.mimeData().hasUrls():
        event.accept()
    else:
        event.ignore()

def drop_event(event, input_field, update_file_list=None, save_last_used_folder=None, folder=True):
    if event.mimeData().hasUrls():
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if folder and QFileInfo(path).isDir():
                input_field.setText(path)
                if update_file_list:
                    update_file_list()
                if save_last_used_folder:
                    save_last_used_folder(path)
            elif not folder and QFileInfo(path).isFile():
                input_field.setText(path)
                if update_file_list:
                    update_file_list()
                if save_last_used_folder:
                    save_last_used_folder(path)
            break
        
def browse_path(input_field, update_file_list=None, save_last_used_folder=None, folder=False):
    if folder:
        path = QFileDialog.getExistingDirectory(None, "Select Folder")
        if update_file_list:
            update_file_list()
        if save_last_used_folder:
            save_last_used_folder(path)
    else:
        path = QFileDialog.getOpenFileName(None, "Select File")[0]
    if path:
        input_field.setText(path)
        if update_file_list:
            update_file_list()
        if save_last_used_folder:
            save_last_used_folder(path)    
            
            
