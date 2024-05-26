folder_name = input("Masukkan nama folder: ")
num_images = int(input("Masukkan jumlah gambar: "))
camera_url = input("Masukkan URL kamera: ")
person_id = input("Masukkan ID: ")

create_training_folder(folder_name)
capture_images(folder_name, num_images=num_images, camera_url=camera_url)

# Connect to the database with error handling
try:
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="testing"  # Assuming the database is named 'testing'
    )
except mysql.connector.Error as err:
    print(f"Database connection error: {err}")
    exit()

mycursor = mydb.cursor()

# Retrieve nip, nama, and gender based on ID with error handling
sql = "SELECT nip, nama, gender FROM data_nama WHERE id = %s"
val = (person_id,)
mycursor.execute(sql, val)
result = mycursor.fetchone()

if result:
    nip, nama, gender = result
else:
    # Handle the case where no person is found with the given ID
    print("Person not found in the database")
    exit()

training_command = f"python3 trainingRev2.py --add {folder_name} --nip {nip} --nama {nama} --gender {gender}"
os.system(training_command)

mycursor.close()
mydb.close()

# Display output with formatting
print(f"""
Input data:
- Folder Name: {folder_name}
- Number of Images: {num_images}
- Camera URL: {camera_url}
- ID: {person_id}

Retrieved data from database:
- Nama: {nama}
- NIP: {nip}
- Gender: {gender}

Image capture and training completed.
""")

