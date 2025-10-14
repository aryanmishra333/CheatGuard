import cv2

url = "http://192.168.1.2:4747/video"  # same IP shown in your DroidCam app

cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't read frame")
        break
    cv2.imshow("DroidCam Feed", frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
