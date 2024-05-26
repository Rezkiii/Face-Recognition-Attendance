import pickle
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for
import os
import cv2
import time
import urllib.request
import numpy as np
import subprocess

app = Flask(__name__)


# Konfigurasi folder statis
app.static_folder = 'templates/static'

# Load pickle data
pickle_file_path = Path("output/encodings.pkl")

try:
    with open(pickle_file_path, 'rb') as file:
        data = pickle.load(file)
except FileNotFoundError:
    data = None
    print("File pickle tidak ditemukan.")
except Exception as e:
    data = None
    print("Terjadi kesalahan saat membuka file pickle:", str(e))

# Global face_cascade variable
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
validation_folder = "validation"


def create_training_folder(folder_name):
    folder_path = os.path.join("training", folder_name)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Folder '{folder_name}' created successfully in the 'training' directory.")
    else:
        print(f"Folder '{folder_name}' already exists in the 'training' directory.")


def capture_images(folder_name, num_images=10, camera_url=""):
    folder_path = os.path.join("training", folder_name)

    if os.path.exists(folder_path):
        print("Starting image capture. Please align your face straight towards the camera.")

        if not camera_url:
            camera_url = request.form['camera_url']

        count = 0
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        while count < num_images:
            stream = urllib.request.urlopen(camera_url)
            byte_data = bytes()

            while True:
                data = stream.read(1024)
                if not data:
                    break

                byte_data += data
                a = byte_data.find(b"\xff\xd8")
                b = byte_data.find(b"\xff\xd9")

                if a != -1 and b != -1:
                    jpg = byte_data[a:b + 2]
                    byte_data = byte_data[b + 2:]

                    frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    flipped_frame = cv2.flip(frame, -1)
                    gray_frame = cv2.cvtColor(flipped_frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                    for (x, y, w, h) in faces:
                        cv2.rectangle(flipped_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        face_image = flipped_frame

                        time.sleep(1)
                        image_path = os.path.join(folder_path, f"{count + 1}.png")
                        cv2.imwrite(image_path, face_image)

                        print(f"Image {count + 1}/{num_images} captured.")

                        count += 1

                        if count == num_images:
                            break

                    if count == num_images:
                        break

        print("Image capture completed.")
    else:
        print(f"Folder '{folder_name}' does not exist in the 'training' directory.")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/check_data')
def show_data():
    if data:
        unique_data = []
        seen = set()
        for item in data:
            key = (item['nama'], item['nip'])
            if key not in seen:
                seen.add(key)
                unique_data.append(item)

        data_count = len(data)

        merged_data = []
        for item in unique_data:
            item['jumlah_data'] = data_count
            merged_data.append(item)

        return render_template('checkData.html', data=merged_data)
    else:
        return "Data not available."

@app.route('/enroll')
def enroll():
    return render_template('enroll.html')


@app.route('/capture', methods=['POST'])
def capture():
    folder_name = request.form['folder_name']
    num_images = int(request.form['num_images'])
    camera_url = request.form['camera_url']

    create_training_folder(folder_name)
    capture_images(folder_name, num_images=num_images, camera_url=camera_url)

    nip = request.form['nip']
    nama = request.form['nama']
    gender = request.form['gender']

    training_command = f"python3 trainingRev2.py --add {folder_name} --nip {nip} --nama {nama} --gender {gender}"
    os.system(training_command)

    return "Image capture and training completed."


def create_validation_folder():
    if not os.path.exists("validation"):
        os.makedirs("validation")
        print("Validation folder created successfully.")
    else:
        print("Validation folder already exists.")


def capture_and_validate(url):
    capture_stream = cv2.VideoCapture(url)
    faces_detected = False
    start_time = 0
    validate_process = None

    while True:
        ret, frame = capture_stream.read()

        if not ret:
            # Reconnect stream if connection is lost
            capture_stream = cv2.VideoCapture(url)
            continue

        # Rotate frame 180 degrees
        rotated_frame = cv2.rotate(frame, cv2.ROTATE_180)

        gray = cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            # Wajah terdeteksi, perbarui waktu mulai jika belum ada wajah sebelumnya
            if not faces_detected:
                start_time = time.time()
            faces_detected = True

            # Gambar kotak pembatas (bounding box) di sekitar wajah
            for (x, y, w, h) in faces:
                cv2.rectangle(rotated_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Cek apakah wajah terdeteksi selama 3 detik sebelum mengambil gambar
            current_time = time.time()
            if current_time - start_time >= 3:
                # Simpan frame yang memiliki wajah terdeteksi
                timestamp = int(time.time())
                image_name = f"{validation_folder}/camera_frame_{timestamp}.jpg"
                cv2.imwrite(image_name, rotated_frame)
                faces_detected = False

                # Jalankan program validateRev4.py
                if validate_process is None or validate_process.poll() is not None:
                    validate_process = subprocess.Popen(["python3", "validateRev4.py"])

        #cv2.imshow("Camera", rotated_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()



@app.route('/absensi_index', methods=['GET', 'POST'])
def absensi_index():
    if request.method == 'POST':
        url = request.form['url']
        create_validation_folder()
        capture_and_validate(url)
        return "Validation program exited. Restarting image capture and validation."
    return render_template('absensi.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

