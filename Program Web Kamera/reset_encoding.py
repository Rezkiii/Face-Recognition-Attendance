import pickle
from pathlib import Path


DEFAULT_ENCODINGS_PATH = Path("output/encodings.pkl")


def reset_encodings_file():
    data = []
    with DEFAULT_ENCODINGS_PATH.open(mode="wb") as f:
        pickle.dump(data, f)
    print("Isi file 'encodings.pkl' berhasil direset.")


if __name__ == "__main__":
    reset_encodings_file()
