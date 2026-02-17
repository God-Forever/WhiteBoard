import sys
import os
import ctypes
from ctypes import wintypes
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGraphicsDropShadowEffect,
    QSlider,
    QSizePolicy,
    QSystemTrayIcon,
    QMenu,
)
from PySide6.QtCore import (
    Qt,
    QPoint,
    QSize,
    QPropertyAnimation,
    QRect,
    QEvent,
    QUrl,
    QObject,
    Signal,
    Slot,
)
from PySide6.QtGui import (
    QIcon,
    QPainter,
    QColor,
    QPixmap,
    QFont,
    QPen,
    QPolygon,
    QCursor,
    QGuiApplication,
    QRegion,
    QPainterPath,
    QBrush,
    QAction,
    QBitmap,
)

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript
from PySide6.QtWebChannel import QWebChannel


class WebBridge(QObject):
    closeRequested = Signal()

    @Slot()
    def hideWindow(self):
        self.closeRequested.emit()


class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)

    def contextMenuEvent(self, event):
        pass


class FullScreenWhiteboard(QWidget):
    def __init__(self, html_path, zoom_factor=1.0):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.browser = QWebEngineView()

        custom_page = CustomWebEnginePage(self.browser)
        self.browser.setPage(custom_page)
        self.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)

        self.channel = QWebChannel()
        self.bridge = WebBridge()

        self.bridge.closeRequested.connect(self.hide)
        self.channel.registerObject("external", self.bridge)
        custom_page.setWebChannel(self.channel)

        absolute_path = os.path.abspath(html_path)
        if not os.path.exists(absolute_path):
            pass
        else:
            self.browser.setUrl(QUrl.fromLocalFile(absolute_path))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)

        self.browser.setZoomFactor(zoom_factor)

        screen = QGuiApplication.primaryScreen()
        self.setGeometry(screen.geometry())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.raise_()
        self.activateWindow()


user32 = ctypes.windll.user32
WH_MOUSE_LL = 14
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202


class MOUSEHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("hwnd", wintypes.HWND),
        ("wHitTestCode", wintypes.UINT),
        ("dwExtraInfo", wintypes.ULONG),
    ]


hook_callback = None
canvas_instance = None
hook_id = None


def low_level_mouse_handler(nCode, wParam, lParam):
    if nCode >= 0 and canvas_instance:
        pos = QCursor.pos()

        if canvas_instance.is_drawing:
            if wParam == WM_MOUSEMOVE:
                canvas_instance.on_mouse_move(pos)
            elif wParam == WM_LBUTTONUP:
                canvas_instance.on_mouse_up(pos)
            if wParam == WM_MOUSEMOVE:
                return user32.CallNextHookEx(None, nCode, wParam, lParam)
            else:
                return 1

        is_over_panel = False
        if canvas_instance.control_panel:
            if canvas_instance.control_panel.geometry().contains(pos):
                local_pos = canvas_instance.control_panel.mapFromGlobal(pos)
                if canvas_instance.control_panel.childAt(local_pos):
                    is_over_panel = True

        if is_over_panel:
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        if canvas_instance.is_active():
            if wParam == WM_LBUTTONDOWN:
                canvas_instance.on_mouse_down(pos)
            elif wParam == WM_LBUTTONUP:
                canvas_instance.on_mouse_up(pos)
            elif wParam == WM_MOUSEMOVE:
                canvas_instance.on_mouse_move(pos)

            if wParam == WM_MOUSEMOVE:
                return user32.CallNextHookEx(None, nCode, wParam, lParam)
            else:
                return 1

    return user32.CallNextHookEx(None, nCode, wParam, lParam)


class IconPainter:
    @staticmethod
    def draw_paper_icon():
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        w = 22
        h = 28
        x = (64 - w) / 2
        y = (64 - h) / 2
        fold = 7
        path = QPainterPath()
        path.moveTo(x, y)
        path.lineTo(x + w - fold, y)
        path.lineTo(x + w - fold, y + fold)
        path.lineTo(x + w, y + fold)
        path.lineTo(x + w, y + h)
        path.lineTo(x, y + h)
        path.closeSubpath()
        painter.drawPath(path)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def draw_mouse_icon():
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        x = 3.0
        y = 0
        path.moveTo(3.0 + x, 3.0 + y)
        path.lineTo(16.0 + x, 16.0 + y)
        path.lineTo(10.0 + x, 16.0 + y)
        path.lineTo(12.0 + x, 21.0 + y)
        path.lineTo(11.0 + x, 23.0 + y)
        path.lineTo(8.0 + x, 17.0 + y)
        path.lineTo(3.0 + x, 21.0 + y)
        path.closeSubpath()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawPath(path)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def draw_pen_icon(size=QSize(24, 24)):
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.translate(size.width() / 2 + 2, size.height() / 2 + 2)
        scale = size.width() / 24.0
        painter.scale(scale, scale)
        painter.rotate(-45)
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(Qt.NoPen)
        body_width = 6
        body_height = 13
        painter.drawRect(-body_width // 2, -12, body_width, body_height)
        tip_top_width = 2
        tip_height = 8
        tip_base_width = body_width
        painter.drawPolygon(
            QPolygon(
                [
                    QPoint(-tip_base_width // 2, 0),
                    QPoint(tip_base_width // 2, 0),
                    QPoint(tip_top_width // 2, tip_height),
                    QPoint(-tip_top_width // 2, tip_height),
                ]
            )
        )
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def draw_eraser_icon(size=QSize(24, 24)):
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FFFFFF"))
        path = QPainterPath()
        path.moveTo(3, 12)
        path.lineTo(7, 5)
        path.lineTo(20, 10)
        path.lineTo(16, 17)
        path.closeSubpath()
        painter.drawPath(path)
        path_bottom = QPainterPath()
        path_bottom.moveTo(3, 12)
        path_bottom.lineTo(16, 17)
        path_bottom.lineTo(16, 20)
        path_bottom.lineTo(3, 15)
        path_bottom.closeSubpath()
        painter.drawPath(path_bottom)
        painter.setPen(QPen(QColor(225, 225, 225), 1))
        painter.drawLine(QPoint(16, 20), QPoint(20, 13))
        painter.drawLine(QPoint(20, 13), QPoint(20, 10))
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def draw_trash_icon(size=QSize(24, 24)):
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawRect(6, 8, 12, 14)
        painter.drawRect(4, 6, 16, 2)
        painter.drawRect(8, 3, 8, 3)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def draw_power_icon(size=QSize(24, 24)):
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        w = size.width()
        h = size.height()
        line_length = w * 0.5
        thickness = 2
        center_y = h / 2
        start_x = (w - line_length) / 2
        end_x = start_x + line_length
        painter.setPen(QPen(QColor("#FFFFFF"), thickness, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(start_x, center_y, end_x, center_y)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def draw_app_icon(size=QSize(64, 64)):
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(45, 45, 45, 255))
        margin = 0
        painter.drawEllipse(
            margin, margin, size.width() - margin * 2, size.height() - margin * 2
        )
        painter.translate(size.width() / 2 + 2, size.height() / 2 + 2)
        scale = size.width() / 24.0
        painter.scale(scale, scale)
        painter.rotate(-45)
        painter.setBrush(QColor("#FFFFFF"))
        painter.setPen(Qt.NoPen)
        body_width = 6
        body_height = 12
        painter.drawRect(-body_width // 2, -12, body_width, body_height)
        tip_top_width = 2
        tip_height = 8
        tip_base_width = body_width
        painter.drawPolygon(
            QPolygon(
                [
                    QPoint(-tip_base_width // 2, 0),
                    QPoint(tip_base_width // 2, 0),
                    QPoint(tip_top_width // 2, tip_height),
                    QPoint(-tip_top_width // 2, tip_height),
                ]
            )
        )
        painter.end()
        return QIcon(pixmap)


class CircleBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_color = QColor(45, 45, 45, 200)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.bg_color)
        painter.drawEllipse(self.rect())


class ScreenCanvas(QWidget):
    def __init__(self):
        super().__init__()
        global canvas_instance
        canvas_instance = self

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        screen = QGuiApplication.primaryScreen()
        self.setGeometry(screen.geometry())

        self.paths = []
        self.path_colors = []
        self.path_widths = []
        self.current_path = []
        self.colors = [
            QColor(255, 0, 0),
            QColor(0, 255, 0),
            QColor(0, 0, 255),
            QColor(255, 255, 0),
            QColor(0, 0, 0),
            QColor(255, 255, 255),
        ]
        self.color_index = 0
        self.current_color = self.colors[0]
        self.pen_width = 3
        self.eraser_radius = 15
        self.eraser_mode = 0
        self.drawing_mode = False
        self.is_drawing = False
        self.control_panel = None
        self.setup_hook()

    def set_control_panel(self, panel):
        self.control_panel = panel

    def setup_hook(self):
        global hook_callback, hook_id
        CMPFUNC = ctypes.WINFUNCTYPE(
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int
        )
        hook_callback = CMPFUNC(low_level_mouse_handler)
        hook_id = user32.SetWindowsHookExA(WH_MOUSE_LL, hook_callback, None, 0)

    def is_active(self):
        return self.drawing_mode

    def set_drawing_mode(self, enabled):
        self.drawing_mode = enabled
        if enabled:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            self.update()
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self.finish_drawing()
            self.update()

    def set_eraser_mode(self, mode):
        self.eraser_mode = mode

    def set_pen_thickness(self, width):
        self.pen_width = width

    def set_eraser_radius(self, radius):
        self.eraser_radius = radius

    def cycle_color(self):
        self.color_index = (self.color_index + 1) % len(self.colors)
        self.current_color = self.colors[self.color_index]
        if self.control_panel:
            self.control_panel.update_color_btn()

    def on_mouse_down(self, pos):
        self.is_drawing = True
        self.current_path = [pos]

    def on_mouse_up(self, pos):
        self.finish_drawing()

    def on_mouse_move(self, pos):
        if self.is_drawing:
            if self.eraser_mode == 1:
                self.erase_whole_at_pos(pos)
            elif self.eraser_mode == 2:
                self.erase_brush_at_pos(pos)
            else:
                self.current_path.append(pos)
                self.update()

    def erase_whole_at_pos(self, pos):
        radius = self.eraser_radius
        indices_to_remove = []
        for i, path in enumerate(self.paths):
            for point in path:
                if (point.x() - pos.x()) ** 2 + (point.y() - pos.y()) ** 2 < radius**2:
                    indices_to_remove.append(i)
                    break
        if indices_to_remove:
            indices_to_remove = sorted(list(set(indices_to_remove)), reverse=True)
            for idx in indices_to_remove:
                del self.paths[idx]
                del self.path_colors[idx]
                del self.path_widths[idx]
            self.update()

    def erase_brush_at_pos(self, pos):
        radius = self.eraser_radius
        new_paths = []
        new_colors = []
        new_widths = []
        for i, path in enumerate(self.paths):
            path_width = self.path_widths[i] if i < len(self.path_widths) else 3
            if len(path) < 2:
                if (path[0].x() - pos.x()) ** 2 + (
                    path[0].y() - pos.y()
                ) ** 2 >= radius**2:
                    new_paths.append(path)
                    new_colors.append(self.path_colors[i])
                    new_widths.append(path_width)
                continue
            current_segment = []
            segment_color = self.path_colors[i]
            for j in range(len(path)):
                p = path[j]
                dist_sq = (p.x() - pos.x()) ** 2 + (p.y() - pos.y()) ** 2
                if dist_sq < radius**2:
                    if current_segment:
                        new_paths.append(current_segment)
                        new_colors.append(segment_color)
                        new_widths.append(path_width)
                        current_segment = []
                else:
                    current_segment.append(p)
            if current_segment:
                new_paths.append(current_segment)
                new_colors.append(segment_color)
                new_widths.append(path_width)
        if len(new_paths) != len(self.paths):
            self.paths = new_paths
            self.path_colors = new_colors
            self.path_widths = new_widths
            self.update()

    def finish_drawing(self):
        if self.is_drawing:
            self.is_drawing = False
            if self.eraser_mode == 0 and self.current_path:
                self.paths.append(self.current_path)
                self.path_colors.append(QColor(self.current_color))
                self.path_widths.append(self.pen_width)
            self.current_path = []
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.drawing_mode:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
        for i, path in enumerate(self.paths):
            if len(path) < 2:
                continue
            if i < len(self.path_colors):
                w = self.path_widths[i] if i < len(self.path_widths) else 3
                painter.setPen(QPen(self.path_colors[i], w))
                for j in range(1, len(path)):
                    painter.drawLine(path[j - 1], path[j])
        if self.current_path and len(self.current_path) > 1:
            painter.setPen(QPen(self.current_color, self.pen_width))
            for i in range(1, len(self.current_path)):
                painter.drawLine(self.current_path[i - 1], self.current_path[i])

    def clear_canvas(self):
        self.paths.clear()
        self.path_colors.clear()
        self.path_widths.clear()
        self.current_path = []
        self.update()

    def closeEvent(self, event):
        global hook_id
        if hook_id:
            user32.UnhookWindowsHookEx(hook_id)
            hook_id = None
        event.accept()


class ShapeButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_color = QColor(60, 60, 60, 200)
        self.hover_color = QColor(80, 80, 80, 230)
        self.is_hover = False
        self.is_rounded = False

    def set_shape_color(self, color, hover_color):
        self.bg_color = color
        self.hover_color = hover_color

    def paintEvent(self, event):
        if self.is_rounded:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.is_hover:
            painter.setBrush(QBrush(self.hover_color))
        else:
            painter.setBrush(QBrush(self.bg_color))
        painter.setPen(Qt.NoPen)
        path = QPainterPath()
        self.build_shape_path(path)
        painter.drawPath(path)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        icon = self.icon()
        if not icon.isNull():
            size = self.iconSize()
            x = (self.width() - size.width()) / 2
            y = (self.height() - size.height()) / 2
            icon.paint(painter, x, y, size.width(), size.height())

    def build_shape_path(self, path):
        path.addRect(self.rect())

    def enterEvent(self, event):
        self.is_hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hover = False
        self.update()
        super().leaveEvent(event)


class TTopButton(ShapeButton):
    def build_shape_path(self, path):
        path.moveTo(64 - 6.4, 12.8)
        path.arcTo(0, 0, 64, 64, 36.86989764584401, 106.26020470831197)
        path.lineTo(20.8, 23.6)
        path.arcTo(
            18, 18, 28, 28, 36.86989764584401 + 106.26020470831197, -106.26020470831197
        )
        path.lineTo(64 - 6.4, 12.8)
        path.closeSubpath()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.is_hover:
            painter.setBrush(QBrush(self.hover_color))
        else:
            painter.setBrush(QBrush(self.bg_color))
        painter.setPen(Qt.NoPen)
        path = QPainterPath()
        self.build_shape_path(path)
        painter.drawPath(path)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        icon = self.icon()
        if not icon.isNull():
            size = self.iconSize()
            x = (self.width() - size.width()) / 2
            y = (self.height() - size.height()) / 2
            y -= 2
            icon.paint(painter, int(x), int(y), size.width(), size.height())


class TopButton(ShapeButton):
    def build_shape_path(self, path):
        path.moveTo(16, 0)
        path.arcTo(18, 0, 28, 28, 90, 360)
        path.closeSubpath()


class BottomButton(ShapeButton):
    def build_shape_path(self, path):
        path.moveTo(64 - 6.4, 32 - 12.8 - 8.4)
        path.arcTo(0, -32 - 8.4, 64, 64, -36.86989764584401, -106.26020470831197)
        path.lineTo(20.8, 0)
        path.arcTo(
            18,
            -32 + 18 - 8.4,
            28,
            28,
            -36.86989764584401 - 106.26020470831197,
            106.26020470831197,
        )
        path.moveTo(64 - 6.4, 32 - 12.8 - 8.4)
        path.closeSubpath()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        if self.is_hover:
            painter.setBrush(QBrush(self.hover_color))
        else:
            painter.setBrush(QBrush(self.bg_color))
        painter.setPen(Qt.NoPen)
        path = QPainterPath()
        self.build_shape_path(path)
        painter.drawPath(path)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        icon = self.icon()
        if not icon.isNull():
            size = self.iconSize()
            x = (self.width() - size.width()) / 2
            y = (self.height() - size.height()) / 2
            y += 3
            icon.paint(painter, int(x), int(y), size.width(), size.height())


class FloatingBall(QWidget):
    def __init__(self, canvas, web_window):
        super().__init__()

        self.canvas = canvas
        self.web_window = web_window

        self.canvas.set_control_panel(self)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.is_expanded = False
        self.current_tool = "pen"
        self.drag_pos = QPoint()

        self.colors = self.canvas.colors
        self.current_color_index = self.canvas.color_index

        self.ball_diameter = 64
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = screen_geometry.width() - self.ball_diameter - 80
        y = 40
        self.move(x, y)

        self.panel_width = 220
        self.panel_height = 220

        self.init_ui()
        self.resize(self.ball_diameter, self.ball_diameter)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.bg_widget = CircleBackground(self)

        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.container.installEventFilter(self)

        self.main_layout.addWidget(self.container)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)

        self.btn_toggle_ball = TTopButton()
        self.btn_toggle_ball.setIcon(IconPainter.draw_paper_icon())
        self.btn_toggle_ball.setIconSize(QSize(23, 23))
        self.btn_toggle_ball.setCursor(Qt.PointingHandCursor)

        self.btn_toggle_ball.clicked.connect(self.show_web_window)

        self.btn_power_ball = TopButton()
        self.btn_power_ball.setIcon(IconPainter.draw_pen_icon())
        self.btn_power_ball.setIconSize(QSize(16, 16))
        self.btn_power_ball.setFixedSize(64, 2)
        self.btn_power_ball.setCursor(Qt.PointingHandCursor)
        self.btn_power_ball.clicked.connect(self.toggle_panel)
        self.btn_power_ball.setCheckable(True)
        self.btn_power_ball.toggled.connect(self.toggle_drawing_mode) 
        

        self.btn_clear_ball = BottomButton()
        self.btn_clear_ball.setIcon(IconPainter.draw_trash_icon())
        self.btn_clear_ball.setIconSize(QSize(15, 15))
        self.btn_clear_ball.setCursor(Qt.PointingHandCursor)
        self.btn_clear_ball.clicked.connect(self.canvas.clear_canvas)

        self.container_layout.addWidget(self.btn_toggle_ball)
        self.container_layout.addWidget(self.btn_power_ball)
        self.container_layout.addWidget(self.btn_clear_ball)

        self.btn_toggle_panel = QPushButton()
        self.btn_toggle_panel.setIcon(IconPainter.draw_power_icon())
        self.btn_toggle_panel.setIconSize(QSize(20, 20))
        self.btn_toggle_panel.setFixedSize(40, 40)
        self.btn_toggle_panel.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_panel.clicked.connect(self.toggle_panel)
        self.btn_toggle_panel.setStyleSheet(
            "QPushButton { background-color: rgba(100, 100, 100, 200); border-radius: 8px; border: none; } QPushButton:hover { background-color: rgba(120, 120, 120, 230); }"
        )

        self.widget_tools = QWidget()
        layout_tools = QHBoxLayout(self.widget_tools)
        layout_tools.setContentsMargins(0, 0, 0, 0)
        layout_tools.setSpacing(0)

        self.btn_mouse = QPushButton()
        self.btn_mouse.setIcon(IconPainter.draw_mouse_icon())
        self.btn_mouse.setIconSize(QSize(20, 20))
        self.btn_mouse.setFixedSize(44, 36)
        self.btn_mouse.setCursor(Qt.PointingHandCursor)
        self.btn_mouse.clicked.connect(self.on_mouse_clicked)

        self.btn_pen = QPushButton()
        self.btn_pen.setIcon(IconPainter.draw_pen_icon())
        self.btn_pen.setIconSize(QSize(20, 20))
        self.btn_pen.setFixedSize(44, 36)
        self.btn_pen.setCursor(Qt.PointingHandCursor)
        self.btn_pen.clicked.connect(self.on_pen_clicked)

        self.btn_eraser = QPushButton()
        self.btn_eraser.setIcon(IconPainter.draw_eraser_icon())
        self.btn_eraser.setIconSize(QSize(20, 20))
        self.btn_eraser.setFixedSize(44, 36)
        self.btn_eraser.setCursor(Qt.PointingHandCursor)
        self.btn_eraser.clicked.connect(self.on_eraser_clicked)

        layout_tools.addStretch()
        layout_tools.addWidget(self.btn_mouse)
        layout_tools.addWidget(self.btn_pen)
        layout_tools.addWidget(self.btn_eraser)
        layout_tools.addStretch()

        self.slider_size = QSlider(Qt.Horizontal)
        self.slider_size.setRange(2, 50)
        self.slider_size.setValue(self.canvas.pen_width)
        self.slider_size.valueChanged.connect(self.on_slider_changed)
        self.slider_size.setCursor(Qt.PointingHandCursor)
        self.slider_size.setStyleSheet(
            "QSlider::groove:horizontal { background: rgba(255,255,255,50); height: 6px; border-radius: 3px; } QSlider::handle:horizontal { background: white; width: 18px; margin: -6px 0; border-radius: 9px; }"
        )

        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(36, 36)
        self.btn_color.setCursor(Qt.PointingHandCursor)
        self.btn_color.clicked.connect(self.canvas.cycle_color)

        self.btn_clear_panel = QPushButton()
        self.btn_clear_panel.setIcon(IconPainter.draw_trash_icon())
        self.btn_clear_panel.setIconSize(QSize(20, 20))
        self.btn_clear_panel.setFixedSize(40, 40)
        self.btn_clear_panel.setCursor(Qt.PointingHandCursor)
        self.btn_clear_panel.clicked.connect(self.canvas.clear_canvas)
        self.btn_clear_panel.setStyleSheet(
            "QPushButton { background-color: rgba(100, 100, 100, 200); border-radius: 8px; border: none; } QPushButton:hover { background-color: rgba(120, 120, 120, 230); }"
        )

        self.select_tool("pen")
        self.update_color_btn()
        self.show_ball_widgets()

    def resizeEvent(self, event):
        self.bg_widget.resize(self.width(), self.height())
        super().resizeEvent(event)

    def show_web_window(self):
        if self.web_window:
            self.web_window.show()

    def toggle_drawing_mode(self, checked):
        self.canvas.set_drawing_mode(checked)

    def on_mouse_clicked(self):
        self.select_tool("mouse")
        if self.btn_power_ball.isChecked():
            self.btn_power_ball.setChecked(False)

    def on_pen_clicked(self):
        self.select_tool("pen")
        self.canvas.set_eraser_mode(0)
        if not self.btn_power_ball.isChecked():
            self.btn_power_ball.setChecked(True)

    def on_eraser_clicked(self):
        self.select_tool("eraser")
        if self.canvas.eraser_mode == 0:
            self.canvas.set_eraser_mode(2)
        if not self.btn_power_ball.isChecked():
            self.btn_power_ball.setChecked(True)

    def on_slider_changed(self, value):
        if self.current_tool == "mouse":
            return
        if self.current_tool == "pen":
            self.canvas.set_pen_thickness(value)
        elif self.current_tool == "eraser":
            self.canvas.set_eraser_radius(value)

    def apply_ball_mode_settings(self):
        self.container.setFixedWidth(self.ball_diameter)
        self.container.setMinimumHeight(self.ball_diameter)
        self.container_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

    def apply_panel_mode_settings(self):
        self.container.setMaximumWidth(16707215)
        self.container.setMinimumWidth(0)
        self.container.setMinimumHeight(0)
        self.container_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

    def apply_ball_mode_styles(self):
        self.btn_toggle_ball.setFixedSize(64, 23.6)
        self.btn_power_ball.setFixedSize(64, 28)
        self.btn_clear_ball.setFixedSize(64, 23.6)

        self.btn_toggle_ball.move(0, 0)
        self.btn_power_ball.move(0, 18)
        self.btn_clear_ball.move(0, 18 + 28 - 5.6)

        self.btn_toggle_ball.is_rounded = False
        self.btn_power_ball.is_rounded = False
        self.btn_clear_ball.is_rounded = False

        self.btn_toggle_ball.set_shape_color(
            QColor(100, 100, 100, 100), QColor(120, 120, 120, 230)
        )
        self.btn_power_ball.set_shape_color(
            QColor(100, 100, 100, 100), QColor(120, 120, 120, 230)
        )
        self.btn_clear_ball.set_shape_color(
            QColor(100, 100, 100, 100), QColor(120, 120, 120, 230)
        )

        self.btn_toggle_ball.update()
        self.btn_power_ball.update()
        self.btn_clear_ball.update()

    def get_switch_btn_style(self, is_selected, pos):
        base_bg = (
            "rgba(100, 100, 100, 200)"
            if not is_selected
            else "rgba(130, 130, 130, 200)"
        )
        hover_bg = (
            "rgba(120, 120, 120, 230)"
            if not is_selected
            else "rgba(150, 150, 150, 230)"
        )
        radius_style = ""
        if pos == "left":
            radius_style = "border-top-left-radius: 6px; border-bottom-left-radius: 6px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;"
        elif pos == "right":
            radius_style = "border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 6px; border-bottom-right-radius: 6px;"
        else:
            radius_style = "border-radius: 0px;"
        return f"QPushButton {{ background-color: {base_bg}; color: white; border: none; {radius_style} }} QPushButton:hover {{ background-color: {hover_bg}; }}"

    def update_color_btn(self):
        color = self.canvas.current_color
        border = (
            "2px solid #555" if color == QColor(255, 255, 255) else "2px solid white"
        )
        self.btn_color.setStyleSheet(
            f"QPushButton {{ background-color: {color.name()}; border-radius: 18px; border: {border}; }} QPushButton:hover {{ border: 3px solid #EEE; }}"
        )

    def select_tool(self, tool):
        self.current_tool = tool
        self.btn_mouse.setStyleSheet(self.get_switch_btn_style(tool == "mouse", "left"))
        self.btn_pen.setStyleSheet(self.get_switch_btn_style(tool == "pen", "center"))
        self.btn_eraser.setStyleSheet(
            self.get_switch_btn_style(tool == "eraser", "right")
        )

        if tool == "mouse":
            self.slider_size.setEnabled(False)
            self.slider_size.setValue(2)
        else:
            self.slider_size.setEnabled(True)
            if tool == "pen":
                self.slider_size.setValue(self.canvas.pen_width)
            elif tool == "eraser":
                self.slider_size.setValue(self.canvas.eraser_radius)

    def eventFilter(self, watched, event):
        if watched == self.container:
            if event.type() == QEvent.MouseMove:
                if not self.drag_pos.isNull():
                    self.move(event.globalPosition().toPoint() - self.drag_pos)
                    return True

            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    global_pos = event.globalPosition().toPoint()
                    local_pos = event.position().toPoint()
                    if self.is_expanded:
                        child = self.container.childAt(local_pos)
                        if child and child != self.container:
                            return False
                        self.drag_pos = global_pos - self.pos()
                        self.container.setCursor(Qt.SizeAllCursor)
                        return True
                    else:
                        w = self.container.width()
                        drag_zone = 15
                        if local_pos.x() < drag_zone or local_pos.x() > w - drag_zone:
                            self.drag_pos = global_pos - self.pos()
                            self.container.setCursor(Qt.SizeAllCursor)
                            return True
                        else:
                            return False

            elif event.type() == QEvent.MouseButtonRelease:
                if not self.drag_pos.isNull():
                    self.drag_pos = QPoint()
                    self.container.unsetCursor()
                    return True
        return super().eventFilter(watched, event)

    def toggle_panel(self):
        self.is_expanded = not self.is_expanded
        self.container.hide()
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(250)
        current_geo = self.geometry()

        if self.is_expanded:
            self.apply_panel_mode_settings()
            new_x = current_geo.x() + (self.width() - self.panel_width) // 2
            new_y = current_geo.y()
            target_rect = QRect(new_x, new_y, self.panel_width, self.panel_height)
            self.anim.setStartValue(current_geo)
            self.anim.setEndValue(target_rect)
            self.anim.finished.connect(self.show_panel_widgets)
            self.on_pen_clicked()
        else:
            if self.btn_power_ball.isChecked():
                self.btn_power_ball.setChecked(False)
            self.apply_ball_mode_settings()
            new_x = current_geo.x() + (self.width() - self.ball_diameter) // 2
            new_y = current_geo.y()
            target_rect = QRect(new_x, new_y, self.ball_diameter, self.ball_diameter)
            self.anim.setStartValue(current_geo)
            self.anim.setEndValue(target_rect)
            self.anim.finished.connect(self.show_ball_widgets)
        self.anim.start()

    def show_panel_widgets(self):
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setSpacing(8)
        self.btn_toggle_ball.hide()
        self.btn_power_ball.hide()
        self.btn_clear_ball.hide()
        self.container_layout.removeWidget(self.btn_toggle_ball)
        self.container_layout.removeWidget(self.btn_power_ball)
        self.container_layout.removeWidget(self.btn_clear_ball)
        self.container_layout.insertWidget(0, self.btn_toggle_panel, 0, Qt.AlignHCenter)
        self.btn_toggle_panel.show()
        self.container_layout.insertWidget(1, self.widget_tools)
        self.widget_tools.show()
        self.container_layout.insertWidget(2, self.slider_size)
        self.slider_size.show()
        self.container_layout.insertWidget(3, self.btn_color, 0, Qt.AlignCenter)
        self.btn_color.show()
        self.btn_clear_panel.setFixedSize(40, 40)
        self.container_layout.insertWidget(4, self.btn_clear_panel, 0, Qt.AlignCenter)
        self.btn_clear_panel.show()
        self.container.show()

    def hide_panel_widgets(self):
        self.widget_tools.hide()
        self.slider_size.hide()
        self.btn_color.hide()
        self.btn_clear_panel.hide()
        self.btn_toggle_panel.hide()
        self.container_layout.removeWidget(self.widget_tools)
        self.container_layout.removeWidget(self.slider_size)
        self.container_layout.removeWidget(self.btn_color)
        self.container_layout.removeWidget(self.btn_clear_panel)
        self.container_layout.removeWidget(self.btn_toggle_panel)

    def show_ball_widgets(self):
        self.hide_panel_widgets()
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        self.apply_ball_mode_styles()
        self.container_layout.removeWidget(self.btn_toggle_ball)
        self.container_layout.removeWidget(self.btn_power_ball)
        self.container_layout.removeWidget(self.btn_clear_ball)
        self.btn_toggle_ball.setParent(self.container)
        self.btn_power_ball.setParent(self.container)
        self.btn_clear_ball.setParent(self.container)
        self.apply_ball_mode_styles()
        self.btn_toggle_ball.show()
        self.btn_power_ball.show()
        self.btn_clear_ball.show()
        self.container.show()

    def closeEvent(self, event):
        global hook_id
        if hook_id:
            user32.UnhookWindowsHookEx(hook_id)
            hook_id = None
        if self.canvas:
            self.canvas.close()
        if self.web_window:
            self.web_window.close()
        event.accept()
        QApplication.instance().quit()
        sys.exit()


if __name__ == "__main__":
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    canvas = ScreenCanvas()
    canvas.show()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(script_dir, "WhiteBoard.html")
    web_window = None

    if os.path.exists(html_file):
        web_window = FullScreenWhiteboard(html_file, zoom_factor=1)
        web_window.hide()
    else:
        pass

    ball = FloatingBall(canvas, web_window)
    ball.show()

    tray = QSystemTrayIcon()
    tray.setIcon(IconPainter.draw_app_icon(QSize(64, 64)))
    tray.setToolTip("标注工具")

    tray_menu = QMenu()
    quit_action = QAction("退出", app)

    def safe_quit():
        global hook_id
        if hook_id:
            user32.UnhookWindowsHookEx(hook_id)
        app.quit()

    quit_action.triggered.connect(safe_quit)
    tray_menu.addAction(quit_action)
    tray.setContextMenu(tray_menu)

    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            ball.show()
            ball.activateWindow()

    tray.activated.connect(on_tray_activated)
    tray.show()

    sys.exit(app.exec())
