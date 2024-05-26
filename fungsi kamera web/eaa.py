from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/')
def video_feed():
    url = "http://10.2.3.16/1024x768.mjpeg"
    response = requests.get(url, stream=True)
    return Response(response.iter_content(chunk_size=1024), content_type='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run()



