import cv2
from flask import Flask, Response
from pygrabber.dshow_graph import FilterGraph

app = Flask(__name__)

def list_devices():
    graph = FilterGraph()
    devices = "ID | Name\n---|--------------------------------\n"
    for i, device in enumerate(graph.get_input_devices()):
        devices += f' {i} | {device}\n'
    return devices
    
def handle_user_device_id_selection(devices_list):
    print(devices_list)
    while True:
        user_input = input("Introduce the ID of the device camera you want to serve video from:")
        try:
            user_integer = int(user_input)
            print("selected id: " + user_input )
            return user_integer
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

def generate_frames(cap):
    while True:
        success, frame = cap.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
def handle_camera(camera_id):
    cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW) #cv2.CAP_DSHOW stands for Direct Show API for Windows
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap    

listed_devices = list_devices()
camera_id = handle_user_device_id_selection(listed_devices)
cap = handle_camera(camera_id)

#server routing
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(cap), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
