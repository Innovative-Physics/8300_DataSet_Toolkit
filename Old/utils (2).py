from PyQt6.QtWidgets import QFrame, QGraphicsOpacityEffect
    
    
    
    
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
