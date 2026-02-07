"""
Camera Service - Handle webcam/scanner input with QThread
"""
import cv2
import numpy as np
from pyzbar import pyzbar
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from PyQt6.QtGui import QImage
from typing import Optional
import time

from ..config import CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS


class CameraDiscoveryThread(QThread):
    """
    Thread riêng để tìm kiếm camera mà không làm đơ giao diện
    """
    cameras_found = pyqtSignal(list)

    def run(self):
        available = []
        # Kiểm tra 3 index đầu tiên (thường là đủ cho laptop/PC)
        # Giảm số lượng loop để nhanh hơn
        for i in range(3):
            try:
                # Dùng CAP_DSHOW trên Windows để khởi động nhanh hơn
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    available.append(i)
                    cap.release()
            except:
                pass
        self.cameras_found.emit(available)


class CameraService(QThread):
    """
    Camera service running on separate thread for QR scanning
    Emits signals when frames are captured or QR codes detected
    """
    
    # Signals
    frame_ready = pyqtSignal(QImage)  # Emitted when a new frame is ready
    qr_detected = pyqtSignal(str)      # Emitted when QR code is detected
    error_occurred = pyqtSignal(str)   # Emitted on error
    camera_started = pyqtSignal()      # Emitted when camera starts
    camera_stopped = pyqtSignal()      # Emitted when camera stops
    
    def __init__(self, camera_index: int = 0, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._mutex = QMutex()
        self._last_qr_data = ""
        self._last_qr_time = 0
        self._qr_cooldown = 2.0  # Seconds between same QR detections
        
        # Camera settings from Config
        self.frame_width = CAMERA_WIDTH
        self.frame_height = CAMERA_HEIGHT
        self.fps = CAMERA_FPS
    
    def run(self):
        """Main thread loop - capture and process frames"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            
            if not self.cap.isOpened():
                self.error_occurred.emit("Không thể mở camera. Vui lòng kiểm tra kết nối.")
                return
            
            # Configure camera resolution (HD)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            self._running = True
            self.camera_started.emit()
            
            while self._running:
                ret, frame = self.cap.read()
                
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # Process frame for QR codes
                self._process_frame(frame)
                
                # Convert frame to QImage and emit
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                bytes_per_line = ch * w
                
                q_image = QImage(
                    rgb_frame.data, 
                    w, h, 
                    bytes_per_line, 
                    QImage.Format.Format_RGB888
                )
                
                self.frame_ready.emit(q_image.copy())
                
                # Control frame rate
                time.sleep(1.0 / self.fps)
                
        except Exception as e:
            self.error_occurred.emit(f"Lỗi camera: {str(e)}")
        finally:
            self._cleanup()
    
    def _process_frame(self, frame: np.ndarray):
        """Process frame to detect QR codes"""
        try:
            # Decode QR codes in frame
            decoded_objects = pyzbar.decode(frame)
            
            for obj in decoded_objects:
                qr_data = obj.data.decode('utf-8')
                current_time = time.time()
                
                # Avoid duplicate detections
                with QMutexLocker(self._mutex):
                    if (qr_data != self._last_qr_data or 
                        current_time - self._last_qr_time > self._qr_cooldown):
                        self._last_qr_data = qr_data
                        self._last_qr_time = current_time
                        self.qr_detected.emit(qr_data)
                
                # Draw rectangle around QR code
                points = obj.polygon
                if len(points) == 4:
                    pts = np.array(points, dtype=np.int32)
                    cv2.polylines(frame, [pts], True, (0, 255, 0), 3)
                    
        except Exception as e:
            print(f"QR decode error: {e}")
    
    def stop(self):
        """Stop the camera thread"""
        self._running = False
        self.wait(3000)  # Wait up to 3 seconds for thread to finish
    
    def _cleanup(self):
        """Release camera resources"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None
        self._running = False
        self.camera_stopped.emit()
    
    def is_running(self) -> bool:
        """Check if camera is currently running"""
        return self._running
    
    def set_camera_index(self, index: int):
        """Set camera index (call before starting)"""
        if not self._running:
            self.camera_index = index
    
    def reset_qr_detection(self):
        """Reset QR detection state (allow re-detection of same code)"""
        with QMutexLocker(self._mutex):
            self._last_qr_data = ""
            self._last_qr_time = 0
            
    # Xóa hàm static get_available_cameras cũ gây lag
    @staticmethod
    def decode_qr_from_image(image_path: str) -> Optional[str]:
        try:
            img = cv2.imread(image_path)
            if img is None: return None
            decoded = pyzbar.decode(img)
            if decoded: return decoded[0].data.decode('utf-8')
            return None
        except Exception: return None
    
    @staticmethod
    def decode_qr_from_qimage(qimage: QImage) -> Optional[str]:
        try:
            qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)
            width = qimage.width()
            height = qimage.height()
            ptr = qimage.bits()
            ptr.setsize(height * width * 3)
            arr = np.array(ptr).reshape(height, width, 3)
            decoded = pyzbar.decode(arr)
            if decoded: return decoded[0].data.decode('utf-8')
            return None
        except Exception: return None


class SingleShotCamera:
    """Utility class for single frame capture"""
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
    
    def capture_frame(self) -> Optional[np.ndarray]:
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened(): return None
        ret, frame = cap.read()
        cap.release()
        return frame if ret else None
    
    def capture_and_decode(self) -> Optional[str]:
        frame = self.capture_frame()
        if frame is None: return None
        decoded = pyzbar.decode(frame)
        if decoded: return decoded[0].data.decode('utf-8')
        return None