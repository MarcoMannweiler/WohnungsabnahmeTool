import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image

# Define the directory to save the photos
PHOTO_DIR = "Mängel"

# Ensure the directory exists
if not os.path.exists(PHOTO_DIR):
    os.makedirs(PHOTO_DIR)

# Initialize the DataFrame or load it if it already exists
if os.path.exists("mangelmanagement.csv"):
    df = pd.read_csv("mangelmanagement.csv")
else:
    df = pd.DataFrame(columns=[
        "ID", "Erfassungsdatum", "Unternehmer", "Gewerk", "Mangelname",
        "Mangelbeschreibung", "Wohnung", "Zimmer", "Ort", "Fotos", "Bemerkung", "Zu erledigen bis"
    ])


# Function to generate a new ID
def generate_new_id(df):
    if df.empty:
        return 1000  # Start with 1000 if no data exists
    else:
        max_id = df["ID"].max()  # Find the current maximum ID
        return max_id + 1  # Increment by 1


# Function to save photos with the right filenames and return the filenames
def save_photos(images, id_, date, company, apartment, room):
    photo_filenames = []
    for idx, image in enumerate(images):
        filename = f"{id_}-{date}-{company}-{apartment}-{room}-{idx + 1}.jpg"  # Add index for multiple photos
        file_path = os.path.join(PHOTO_DIR, filename)
        image.save(file_path)
        photo_filenames.append(filename)
    return photo_filenames


# Function to add a new record
def add_record(data):
    global df
    new_df = pd.DataFrame([data])
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv("mangelmanagement.csv", index=False)


# Streamlit app
st.title("Mangelmanagement für Bau- und Wohnungsabnahmen")

# Form to collect the data
with st.form(key='mangel_form'):
    # Automatically generate the next ID
    id_ = generate_new_id(df)

    erfassungsdatum = st.date_input("Erfassungsdatum", datetime.today())
    unternehmer = st.text_input("Unternehmer")
    gewerk = st.text_input("Gewerk")
    mangelname = st.text_input("Mangelname")
    mangelbeschreibung = st.text_area("Mangelbeschreibung")
    apartment = st.text_input("Wohnung")
    room = st.text_input("Zimmer")
    location = st.text_input("Ort")

    # Photo capture using Streamlit's camera_input (multiple times)
    st.write("Fotos aufnehmen (mindestens eines)")
    photos = []

    for i in range(3):  # Allow capturing up to 3 photos
        photo = st.camera_input(f"Foto {i + 1} (Optional)", key=f"photo_{i}")
        if photo:
            image = Image.open(photo)
            photos.append(image)

    remarks = st.text_area("Bemerkung")
    zu_erledigen_bis = st.date_input("Zu erledigen bis")

    submit_button = st.form_submit_button("Absenden")

    if submit_button:
        if len(photos) > 0:
            photo_filenames = save_photos(photos, id_, erfassungsdatum.strftime("%Y-%m-%d"), unternehmer, apartment,
                                          room)
        else:
            photo_filenames = []

        data = {
            "ID": id_,
            "Erfassungsdatum": erfassungsdatum,
            "Unternehmer": unternehmer,
            "Gewerk": gewerk,
            "Mangelname": mangelname,
            "Mangelbeschreibung": mangelbeschreibung,
            "Wohnung": apartment,
            "Zimmer": room,
            "Ort": location,
            "Fotos": ";".join(photo_filenames),  # Save photo filenames as a semicolon-separated string
            "Bemerkung": remarks,
            "Zu erledigen bis": zu_erledigen_bis
        }

        add_record(data)
        st.success(f"Mangel erfolgreich hinzugefügt! ID: {id_}")

# Display existing records
st.subheader("Bestehende Mängel")
st.dataframe(df)
