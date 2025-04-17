
#pyinstaller --onefile --add-data "templates;templates" .\AIS_Flask_test.py

from flask import Flask, render_template, request, jsonify
import threading
import os
from pyais.stream import TCPConnection

app = Flask(__name__)

# Variabili globali per la configurazione
HOST = "xxx.xxx.xxx.xxx"
PORT = 4002
GOOGLE_API_KEY = "insertYourAPIKEY"
TARGET_MSIM = 249193000
SHIPS = {}  # Dizionario per memorizzare le navi
STOP_EVENT = threading.Event()

def connect_to_ais_stream():
    """Connessione al server AIS e ricezione dei dati."""
    try:
        connection = TCPConnection(HOST, PORT)
        print(f"Connected to AIS server at {HOST}:{PORT}")
        for msg in connection:
            if STOP_EVENT.is_set():
                break
            try:
                decoded_message = msg.decode()
                process_ais_data(decoded_message)
            except Exception as e:
                print(f"Error decoding AIS message: {e}")
    except Exception as e:
        print(f"Error connecting to AIS server: {e}")

def process_ais_data(decoded_message):
    """Elabora i dati AIS e aggiorna il dizionario delle navi."""
    try:
        mmsi = decoded_message.mmsi
        lat = decoded_message.lat
        lon = decoded_message.lon
        status = decoded_message.status if hasattr(decoded_message, 'status') else 'N/A'
        turn = decoded_message.turn if hasattr(decoded_message, 'turn') else 'N/A'
        speed = decoded_message.speed if hasattr(decoded_message, 'speed') else 'N/A'
        course = decoded_message.course if hasattr(decoded_message, 'course') else 'N/A'
        heading = decoded_message.heading if hasattr(decoded_message, 'heading') else course  # Usa course come fallback
        
        if mmsi is not None and lat is not None and lon is not None:
            SHIPS[mmsi] = (lat, lon, status, turn, speed, course, heading)
            print(f"processing decoded message...:  {decoded_message}")
        else:
            print(f"Message missing position data: {decoded_message}")
    except AttributeError as e:
        print(f"Error processing decoded message: {e}, message: {decoded_message}")

@app.route("/")
def index():
    """Pagina principale con la mappa."""
    return render_template("mapv3.html", google_api_key=GOOGLE_API_KEY, target_msim=TARGET_MSIM)

@app.route("/get_ships")
def get_ships():
    """Restituisce i dati delle navi in formato JSON."""
    return jsonify(SHIPS)

@app.route("/configure", methods=["GET", "POST"])
def configure():
    """Pagina di configurazione per impostare i parametri."""
    global HOST, PORT, GOOGLE_API_KEY, TARGET_MSIM

    if request.method == "POST":
        HOST = request.form.get("host", HOST)
        PORT = int(request.form.get("port", PORT))
        GOOGLE_API_KEY = request.form.get("google_api_key", GOOGLE_API_KEY)
        TARGET_MSIM = int(request.form.get("target_msim", TARGET_MSIM))
        return "Configuration updated successfully! <a href='/'>Go to Map</a>"

    return """
    <h1>Configuration</h1>
    <form method="POST">
        <label for="host">AIS Server IP:</label>
        <input type="text" id="host" name="host" value="{}"><br><br>
        <label for="port">AIS Server Port:</label>
        <input type="number" id="port" name="port" value="{}"><br><br>
        <label for="google_api_key">Google API Key:</label>
        <input type="text" id="google_api_key" name="google_api_key" value="{}"><br><br>
        <label for="target_msim">Target MMSI:</label>
        <input type="number" id="target_msim" name="target_msim" value="{}"><br><br>
        <button type="submit">Save</button>
    </form>
    <a href="/">Back to Map</a>
    """.format(HOST, PORT, GOOGLE_API_KEY, TARGET_MSIM)

def start_ais_thread():
    """Avvia il thread per la connessione AIS."""
    ais_thread = threading.Thread(target=connect_to_ais_stream, daemon=True)
    ais_thread.start()

if __name__ == "__main__":
    # Avvia il thread AIS
    start_ais_thread()
    # Avvia l'app Flask
    app.run("0.0.0.0", debug=False)