from flask import Flask, render_template
import pymysql

app = Flask(__name__)

# Konfigurasi folder statis
app.static_folder = 'templates/static'

# Konfigurasi database
mydb = pymysql.connect(
    host="localhost",
    user="root",
    password="1",
    database="testing"
)

@app.route('/')
def display_index():
    # Render template halaman index.html
    return render_template('index.html')

@app.route('/dataAbsen')
def display_results():
    # Mengambil data dari tabel face_recognition_results
    #cursor = mydb.cursor()
    #cursor.execute("SELECT * FROM face_recognition_results")
    #mydb.session.commit()
    #results = cursor.fetchall()
    #cursor.close()

    conn = pymysql.connect(host="localhost", user="root", password="1", database="testing")
    cursor  = conn.cursor()
    select_query = f"SELECT * FROM face_recognition_results"
    # Execute the query
    cursor.execute(select_query)
    # Fetch all rows
    rows = cursor.fetchall()
    print(rows)
    # Close the cursor and connection
    cursor.close()
    conn.close()
    #print(results)

    # Render template dan kirimkan data ke halaman HTML
    return render_template('dataAbsen.html', results=rows)


@app.route('/kehadiran')
def display_kehadiran():
    # Mengambil data dari tabel Hadir
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM Hadir")
    results_hadir = cursor.fetchall()
    cursor.close()

    # Mengambil data dari tabel Pulang
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM Pulang")
    results_pulang = cursor.fetchall()
    cursor.close()

    # Render template dan kirimkan data ke halaman HTML
    return render_template('Kehadiran.html', results_hadir=results_hadir, results_pulang=results_pulang)

@app.route('/absenkeluar')
def display_absen_keluar():
    # Mengambil data dari tabel Pulang
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM Pulang")
    results_pulang = cursor.fetchall()
    cursor.close()

    # Render template dan kirimkan data ke halaman HTML
    return render_template('AbsenKeluar.html', results_pulang=results_pulang)

if __name__ == '__main__':
    app.run(port=5001, host='0.0.0.0', debug=True)
