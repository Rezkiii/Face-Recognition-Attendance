import argparse
import os
import pickle
from pathlib import Path
import datetime
import json
import face_recognition
import mysql.connector
from decimal import Decimal

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def load_encodings(encodings_path):
    with encodings_path.open(mode="rb") as f:
        encodings = pickle.load(f)
    return encodings

def recognize_faces(image_path, encodings):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    results = []

    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(
            [data["encoding"] for data in encodings],
            face_encoding
        )

        date = datetime.datetime.now().date()
        time = datetime.datetime.now().strftime("%H:%M:%S")

        if any(matches):
            face_distances = face_recognition.face_distance([data["encoding"] for data in encodings], face_encoding)
            min_distance = min(face_distances)
            min_distance_index = face_distances.argmin()

            if matches[min_distance_index]:
                matched_nip = encodings[min_distance_index]["nip"]
                matched_name = encodings[min_distance_index]["nama"]
                accuracy = Decimal((1 - min_distance) * 100)

                if accuracy >= 75:
                    result = {
                        "Nama": matched_name,
                        "NIP": matched_nip,
                        "Tanggal": str(date),
                        "Jam": str(time),
                        "Accuracy": accuracy
                    }

                    results.append(result)
        else:
            result = {
                "Nama": "Unknown",
                "NIP": "",
                "Tanggal": str(date),
                "Jam": str(time),
                "Accuracy": Decimal(0.0)
            }

            results.append(result)

    return results

# Fungsi untuk menyimpan hasil ke database MySQL
def save_to_database(results):
    cnx = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="testing"
    )
    cursor = cnx.cursor()

    create_table_query = """
        CREATE TABLE IF NOT EXISTS face_recognition_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Nama VARCHAR(255),
            NIP VARCHAR(255),
            Tanggal DATE,
            Jam TIME,
            Accuracy DECIMAL(5, 2)
        )
    """
    cursor.execute(create_table_query)

    insert_query = """
        INSERT INTO face_recognition_results
        (Nama, NIP, Tanggal, Jam, Accuracy)
        VALUES (%s, %s, %s, %s, %s)
    """
    for result in results:
        values = (
            result["Nama"],
            result["NIP"],
            result["Tanggal"],
            result["Jam"],
            result["Accuracy"]
        )
        cursor.execute(insert_query, values)

    cnx.commit()
    cursor.close()
    cnx.close()

    print("Output saved to the MySQL database.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Face Recognition Testing Script")
    parser.add_argument("--image_dir", metavar="IMAGE_DIR", default="validation", help="Directory containing the test images")

    args = parser.parse_args()

    DEFAULT_ENCODINGS_PATH = Path("output/encodings.pkl")
    image_dir = Path(args.image_dir)

    if not image_dir.exists() or not image_dir.is_dir():
        print(f"Directory '{args.image_dir}' does not exist.")
        exit()

    image_paths = list(image_dir.glob("*"))

    if not image_paths:
        print(f"No images found in directory '{args.image_dir}'.")
        exit()

    encodings = load_encodings(DEFAULT_ENCODINGS_PATH)

    results_all = []

    for image_path in image_paths:
        if image_path.is_file():
            results = recognize_faces(image_path, encodings)
            results_all.extend(results)

    output_path = "output/results.json"

    filtered_results = [result for result in results_all if result["Accuracy"] >= 75]

    with open(output_path, "w") as f:
        json.dump(filtered_results, f, indent=4, default=decimal_default)

    save_to_database(filtered_results)

    for image_path in image_paths:
        if image_path.is_file():
            os.remove(image_path)
