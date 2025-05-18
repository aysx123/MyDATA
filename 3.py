import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QCursor
from PyQt5.QtCore import Qt, QTimer, QPoint
from ctypes import windll
import win32api
import win32con

class TransparentOverlay(QWidget):
    def __init__(self):
        super().__init__()

        # ======= 自定义参数 =======
        self.window_width = 800           # 窗口宽度
        self.window_height = 600          # 窗口高度
        self.window_opacity = 0.4         # 窗口透明度 (0~1)
        self.line_color = QColor(225, 0, 0, 220)  # 线颜色
        self.line_width = 4              # 十字线线宽
        self.growth_rate = 270           # 线增长速率 y = growth_rate * t (像素/秒)
        # =========================

        # 设置窗口属性：无边框、置顶、工具窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(self.window_width, self.window_height)
        self.move(300, 200)
        self.setWindowOpacity(self.window_opacity)

        # 获取窗口句柄
        self.hwnd = self.winId().__int__()
        # 开启穿透
        self.enable_mouse_penetration(True)

        # 绘图控制变量
        self.is_pressed = False
        self.start_time = 0
        self.press_pos = QPoint(0, 0)

        # 中键拖动相关
        self.is_dragging = False
        self.drag_start_pos = QPoint(0, 0)

        # 定时器轮询按键状态
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_mouse_state)
        self.timer.start(16)  # 60 FPS

        self.show()

    def enable_mouse_penetration(self, enable=True):
        """开启或关闭鼠标穿透"""
        style = windll.user32.GetWindowLongW(self.hwnd, -20)
        if enable:
            windll.user32.SetWindowLongW(self.hwnd, -20, style | 0x80000 | 0x20)
        else:
            windll.user32.SetWindowLongW(self.hwnd, -20, style & ~0x20)

    def check_mouse_state(self):
        """轮询鼠标按键状态"""

        # 判断中键是否按下
        if win32api.GetAsyncKeyState(win32con.VK_MBUTTON) & 0x8000:
            # 中键按下，开始拖动或继续拖动
            if not self.is_dragging:
                self.is_dragging = True
                self.drag_start_pos = QCursor.pos() - self.pos()
                self.enable_mouse_penetration(False)
            else:
                # 拖动中，更新位置
                new_pos = QCursor.pos() - self.drag_start_pos
                self.move(new_pos)
        else:
            # 中键松开，结束拖动
            if self.is_dragging:
                self.is_dragging = False
                self.enable_mouse_penetration(True)

        # 右键：关闭窗口（已取消）
        if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) & 0x8000:
            QApplication.quit()

        # 左键：长按绘制十字线（穿透状态，靠轮询监测）
        if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000:
            if not self.is_pressed:
                # 左键刚按下
                self.is_pressed = True
                self.start_time = time.time()
                self.press_pos = QCursor.pos() - self.pos()
        else:
            if self.is_pressed:
                # 左键松开，停止绘制
                self.is_pressed = False
                self.update()  # 擦除线条

        # 实时刷新绘制
        if self.is_pressed:
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(225, 225, 225, 100))  # 半透明背景

        if self.is_pressed:
            pen = QPen(self.line_color, self.line_width)
            painter.setPen(pen)
            painter.setRenderHint(QPainter.Antialiasing)

            elapsed = time.time() - self.start_time
            length = int(self.growth_rate * elapsed)

            x, y = self.press_pos.x(), self.press_pos.y()

            painter.translate(x, y)  # 坐标系移动到按下点

            angle = 30  # 你设置的夹角度数

            # 画第一条线，逆时针偏移 angle/2 度
            painter.save()
            painter.rotate(-angle)
            painter.drawLine(-length, 0, length, 0)
            painter.restore()

            # 画第二条线，顺时针偏移 angle/2 度
            painter.save()
            painter.rotate(angle)
            painter.drawLine(-length, 0, length, 0)
            painter.restore()

        painter.end()

    def keyPressEvent(self, event):
        """监听键盘事件，Esc退出程序"""
        if event.key() == Qt.Key_Escape:
            QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    overlay = TransparentOverlay()
    sys.exit(app.exec_())
