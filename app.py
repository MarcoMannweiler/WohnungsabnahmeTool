import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image
import time

# Base directory for projects
PROJECTS_DIR = "Projekte"

# Function to create a new project
def create_new_project(project_name):
    project_path = os.path.join(PROJECTS_DIR, project_name)

    if not os.path.exists(project_path):
        os.makedirs(project_path)
        os.makedirs(os.path.join(project_path, "Fotos"))

        csv_path = os.path.join(project_path, "mangelmanagement.csv")
        pd.DataFrame(columns=[
            "ID", "Erfassungsdatum", "Unternehmer", "Gewerk", "Mangelname",
            "Mangelbeschreibung", "Wohnung", "Zimmer", "Ort", "Fotos", "Bemerkung", "Zu erledigen bis"
        ]).to_csv(csv_path, index=False)

        st.success(f"Neues Projekt '{project_name}' wurde erstellt!")
        time.sleep(1)
        st.rerun()
    else:
        st.warning(f"Projekt '{project_name}' existiert bereits!")

# Load or create project CSV file
def load_project_data(project_name):
    csv_path = os.path.join(PROJECTS_DIR, project_name, "mangelmanagement.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path), csv_path
    else:
        return pd.DataFrame(columns=[
            "ID", "Erfassungsdatum", "Unternehmer", "Gewerk", "Mangelname",
            "Mangelbeschreibung", "Wohnung", "Zimmer", "Ort", "Fotos", "Bemerkung", "Zu erledigen bis"
        ]), csv_path

# Function to generate a new ID
def generate_new_id(df):
    if df.empty:
        return 1000
    else:
        max_id = df["ID"].max()
        return max_id + 1

# Function to save photos with the right filenames and return the filenames
def save_photos(images, id_, date, company, apartment, room, project_name):
    photo_filenames = []
    photo_dir = os.path.join(PROJECTS_DIR, project_name, "Fotos")
    for idx, image in enumerate(images):
        filename = f"{id_}-{date}-{company}-{apartment}-{room}-{idx + 1}.jpg"
        file_path = os.path.join(photo_dir, filename)
        image.save(file_path)
        photo_filenames.append(filename)
    return photo_filenames

# Function to add a new record
def add_record(data, csv_path):
    df = pd.read_csv(csv_path)
    new_df = pd.DataFrame([data])
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv(csv_path, index=False)
    return df

# Ensure base projects directory exists
if not os.path.exists(PROJECTS_DIR):
    os.makedirs(PROJECTS_DIR)

# Streamlit app
st.title("Bau- und Wohnungsabnahmen")
st.write("Eingabemaske für Mängel des ausgewählten Projekts")

# Sidebar for project management
with st.sidebar:
    st.header("Projekte")

    with st.form(key="new_project_form"):
        new_project_name = st.text_input("Neues Projekt / Neue Abnahme erstellen")
        create_project_button = st.form_submit_button("Projekt erstellen")

        if create_project_button and new_project_name:
            create_new_project(new_project_name)

    projects = [p for p in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, p))]
    selected_project = st.selectbox("Projekt auswählen", options=projects)

# Load the selected project data
if selected_project:
    df, csv_path = load_project_data(selected_project)

    st.header(f"Projekt / Abnahme: {selected_project}")

    # Create a container for the form
    with st.form(key='mangel_form', clear_on_submit=True):
        id_ = generate_new_id(df)

        erfassungsdatum = st.date_input("Erfassungsdatum", datetime.today(), key='date_input')
        unternehmer = st.text_input("Unternehmer", key='unternehmer_input')
        gewerk = st.text_input("Gewerk", key='gewerk_input')
        mangelname = st.text_input("Mangelname", key='mangelname_input')
        mangelbeschreibung = st.text_area("Mangelbeschreibung", key='beschreibung_input')
        apartment = st.text_input("Wohnung", key='apartment_input')
        room = st.text_input("Zimmer", key='room_input')
        location = st.text_input("Ort", key='location_input')

        st.write("Fotos aufnehmen (mindestens eines)")
        photos = []
        for i in range(3):
            photo = st.camera_input(f"Foto {i + 1} (Optional)", key=f"photo_{i}")
            if photo:
                image = Image.open(photo)
                photos.append(image)

        remarks = st.text_area("Bemerkung", key='remarks_input')
        zu_erledigen_bis = st.date_input("Zu erledigen bis", key='due_date_input')

        submit_button = st.form_submit_button("Absenden")

        if submit_button:
            if len(photos) > 0:
                photo_filenames = save_photos(photos, id_, erfassungsdatum.strftime("%Y-%m-%d"), unternehmer, apartment, room, selected_project)
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
                "Fotos": ";".join(photo_filenames),
                "Bemerkung": remarks,
                "Zu erledigen bis": zu_erledigen_bis
            }

            df = add_record(data, csv_path)
            st.success(f"Mangel erfolgreich hinzugefügt! ID: {id_}")

            # Rerun the page to immediately reflect the change in the table
            st.rerun()

    st.subheader(f"Bestehende Mängel für Projekt: {selected_project}")
    st.dataframe(df)




#####
#####
#####
#####
#####

#alter Code ohne Projekterstellung und Projektauswahlmöglichkeiten

# import streamlit as st
# import pandas as pd
# import os
# from datetime import datetime
# from PIL import Image
#
# # Define the directory to save the photos
# PHOTO_DIR = "Mängel"
#
# # Ensure the directory exists
# if not os.path.exists(PHOTO_DIR):
#     os.makedirs(PHOTO_DIR)
#
# # Initialize the DataFrame or load it if it already exists
# if os.path.exists("mangelmanagement.csv"):
#     df = pd.read_csv("mangelmanagement.csv")
# else:
#     df = pd.DataFrame(columns=[
#         "ID", "Erfassungsdatum", "Unternehmer", "Gewerk", "Mangelname",
#         "Mangelbeschreibung", "Wohnung", "Zimmer", "Ort", "Fotos", "Bemerkung", "Zu erledigen bis"
#     ])
#
#
# # Function to generate a new ID
# def generate_new_id(df):
#     if df.empty:
#         return 1000  # Start with 1000 if no data exists
#     else:
#         max_id = df["ID"].max()  # Find the current maximum ID
#         return max_id + 1  # Increment by 1
#
#
# # Function to save photos with the right filenames and return the filenames
# def save_photos(images, id_, date, company, apartment, room):
#     photo_filenames = []
#     for idx, image in enumerate(images):
#         filename = f"{id_}-{date}-{company}-{apartment}-{room}-{idx + 1}.jpg"  # Add index for multiple photos
#         file_path = os.path.join(PHOTO_DIR, filename)
#         image.save(file_path)
#         photo_filenames.append(filename)
#     return photo_filenames
#
#
# # Function to add a new record
# def add_record(data):
#     global df
#     new_df = pd.DataFrame([data])
#     df = pd.concat([df, new_df], ignore_index=True)
#     df.to_csv("mangelmanagement.csv", index=False)
#
#
# # Streamlit app
# st.title("Mangelmanagement für Bau- und Wohnungsabnahmen")
#
# # Form to collect the data
# with st.form(key='mangel_form'):
#     # Automatically generate the next ID
#     id_ = generate_new_id(df)
#
#     erfassungsdatum = st.date_input("Erfassungsdatum", datetime.today())
#     unternehmer = st.text_input("Unternehmer")
#     gewerk = st.text_input("Gewerk")
#     mangelname = st.text_input("Mangelname")
#     mangelbeschreibung = st.text_area("Mangelbeschreibung")
#     apartment = st.text_input("Wohnung")
#     room = st.text_input("Zimmer")
#     location = st.text_input("Ort")
#
#     # Photo capture using Streamlit's camera_input (multiple times)
#     st.write("Fotos aufnehmen (mindestens eines)")
#     photos = []
#
#     for i in range(3):  # Allow capturing up to 3 photos
#         photo = st.camera_input(f"Foto {i + 1} (Optional)", key=f"photo_{i}")
#         if photo:
#             image = Image.open(photo)
#             photos.append(image)
#
#     remarks = st.text_area("Bemerkung")
#     zu_erledigen_bis = st.date_input("Zu erledigen bis")
#
#     submit_button = st.form_submit_button("Absenden")
#
#     if submit_button:
#         if len(photos) > 0:
#             photo_filenames = save_photos(photos, id_, erfassungsdatum.strftime("%Y-%m-%d"), unternehmer, apartment,
#                                           room)
#         else:
#             photo_filenames = []
#
#         data = {
#             "ID": id_,
#             "Erfassungsdatum": erfassungsdatum,
#             "Unternehmer": unternehmer,
#             "Gewerk": gewerk,
#             "Mangelname": mangelname,
#             "Mangelbeschreibung": mangelbeschreibung,
#             "Wohnung": apartment,
#             "Zimmer": room,
#             "Ort": location,
#             "Fotos": ";".join(photo_filenames),  # Save photo filenames as a semicolon-separated string
#             "Bemerkung": remarks,
#             "Zu erledigen bis": zu_erledigen_bis
#         }
#
#         add_record(data)
#         st.success(f"Mangel erfolgreich hinzugefügt! ID: {id_}")
#
# # Display existing records
# st.subheader("Bestehende Mängel")
# st.dataframe(df)
