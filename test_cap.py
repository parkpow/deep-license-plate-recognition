import cv2

cap = cv2.VideoCapture('rtsp://admin:123abc456@minhtuanvt2019.ddns.net:554/Streaming/channels/101/out.h264')

while(True):
    ret, frame = cap.read()
    print(frame)
    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break