import cv2
import threading

cap_res = [False]
read_res = [False]

def loop():
    cap = cv2.VideoCapture(0)
    cap_res[0] = cap.isOpened()
    if cap_res[0]:
        read_res[0] = cap.read()[0]
    cap.release()

t = threading.Thread(target=loop)
t.start()
t.join()

print(f"Opened: {cap_res[0]}, Read: {read_res[0]}")
