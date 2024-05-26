import argparse
import datetime
import pickle
import json
from collections import Counter
from pathlib import Path
import os
import mysql.connector

import face_recognition
from PIL import Image, ImageDraw

DEFAULT_ENCODINGS_PATH = Path("output/encodings.pkl")


def connect_db():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="testing"
    )
    return db


def create_table(db):
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS encodings (
            id INT PRIMARY KEY AUTO_INCREMENT,
            nip VARCHAR(255) NOT NULL,
            nama VARCHAR(255) NOT NULL,
            gender VARCHAR(255) NOT NULL,
            encoding TEXT NOT NULL
        );
    """)

    db.commit()
    cursor.close()


def encode_known_faces():
    db = connect_db()
    create_table(db)
    cursor = db.cursor()

    data = []
    for filepath in Path("training").glob("*/*"):
        id = filepath.parent.name
        image = face_recognition.load_image_file(filepath)

        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)

        for encoding in face_encodings:
            data.append({"nip": None, "nama": None, "gender": None, "encoding": encoding.tolist()})

    for row in data:
        cursor.execute("INSERT INTO encodings (nip, nama, gender, encoding) VALUES (%s, %s, %s, %s)",
                       (row["nip"], row["nama"], row["gender"], json.dumps(row["encoding"])))

    db.commit()
    cursor.close()
    db.close()

    print("Training completed.")


def add_training_data(folder_name, nip=None, nama=None, gender=None):
    db = connect_db()
    create_table(db)
    cursor = db.cursor()

    folder_path = Path("training") / folder_name

    if folder_path.exists() and folder_path.is_dir():
        existing_entries = set()
        for filepath in folder_path.glob("*"):
            image = face_recognition.load_image_file(filepath)

            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)

            for encoding in face_encodings:
                encoding_str = json.dumps(encoding.tolist())
                entry = (nip, nama, gender, encoding_str)

                if entry not in existing_entries:
                    cursor.execute("INSERT INTO encodings (nip, nama, gender, encoding) VALUES (%s, %s, %s, %s)", entry)
                    existing_entries.add(entry)

        db.commit()
        cursor.close()
        db.close()

        print(f"Training data added for folder '{folder_name}' with NIP '{nip}', Nama '{nama}', and gender '{gender}'.")
    else:
        print(f"Folder '{folder_name}' does not exist in the 'training' directory.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Face Recognition Training Script")
    parser.add_argument("--train", action="store_true", help="Perform training on all images in the 'training' folder")
    parser.add_argument("--add", metavar="FOLDER_NAME", help="Add training data for a specific folder")
    parser.add_argument("--nip", metavar="NIP", help="Specify NIP for the added training data")
    parser.add_argument("--nama", metavar="NAMA", help="Specify name for the added training data")
    parser.add_argument("--gender", metavar="GENDER", help="Specify gender for the added training data")

    args = parser.parse_args()

    if args.train:
        encode_known_faces()
        print("Training completed.")

    if args.add:
        add_training_data(args.add, args.nip, args.nama, args.gender)
        print(f"Training data added for folder '{args.add}' with NIP '{args.nip}', Nama '{args.nama}', and gender '{args.gender}'.")
