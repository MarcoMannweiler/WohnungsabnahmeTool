import dropbox
import pandas as pd
from datetime import datetime
import time
import streamlit as st
from PIL import Image, ImageDraw
import os
from streamlit_drawable_canvas import st_canvas

# Base directory for projects (optional, local usage)
PROJECTS_DIR = "Projekte"

ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')


def authenticate_dropbox():
    dbx = dropbox.Dropbox(ACCESS_TOKEN)
    return dbx


# Function to create a new project (folder) in Dropbox
def create_new_project(project_name):
    dbx = authenticate_dropbox()
    folder_path = f"/{project_name}"

    try:
        dbx.files_create_folder_v2(folder_path)
        dbx.files_create_folder_v2(f"{folder_path}/Fotos")
        dbx.files_create_folder_v2(f"{folder_path}/Pläne")

        # Create an empty CSV file in Dropbox
        csv_path = f"{folder_path}/mangelmanagement.csv"
        df = pd.DataFrame(columns=[
            "ID", "Erfassungsdatum", "Unternehmer", "Gewerk", "Mangelname",
            "Mangelbeschreibung", "Wohnung", "Zimmer", "Ort", "Fotos", "Plan", "Bemerkung", "Zu erledigen bis"
        ])
        df.to_csv("temp_mangelmanagement.csv", index=False)
        with open("temp_mangelmanagement.csv", "rb") as f:
            dbx.files_upload(f.read(), csv_path)
        os.remove("temp_mangelmanagement.csv")  # Cleanup local temporary file

        st.success(f"Neues Projekt '{project_name}' wurde erstellt!")
        time.sleep(1)
        st.rerun()
    except dropbox.exceptions.ApiError as e:
        st.error(f"Fehler beim Erstellen des Projekts: {e}")


# Load project CSV file from Dropbox
def load_project_data(project_name):
    csv_path = f"/{project_name}/mangelmanagement.csv"
    dbx = authenticate_dropbox()

    try:
        metadata, response = dbx.files_download(csv_path)
        df = pd.read_csv(response.content)
        return df, csv_path
    except dropbox.exceptions.ApiError:
        return pd.DataFrame(columns=[
            "ID", "Erfassungsdatum", "Unternehmer", "Gewerk", "Mangelname",
            "Mangelbeschreibung", "Wohnung", "Zimmer", "Ort", "Fotos", "Plan", "Bemerkung", "Zu erledigen bis"
        ]), csv_path


# Function to save photos to Dropbox
def save_photos(images, id_, date, company, apartment, room, project_name):
    photo_filenames = []
    photo_dir = f"/{project_name}/Fotos"
    dbx = authenticate_dropbox()

    for idx, image in enumerate(images):
        filename = f"{id_}-{date}-{company}-{apartment}-{room}-{idx + 1}.jpg"
        # Save the image to a temporary location first
        image.save(filename)
        with open(filename, "rb") as f:
            dbx.files_upload(f.read(), f"{photo_dir}/{filename}")
        photo_filenames.append(filename)
        os.remove(filename)  # Cleanup local file
    return photo_filenames


# Function to save the plan image to Dropbox
def save_plan_image(image, canvas_result, id_, project_name):
    photo_dir = f"/{project_name}/Fotos"
    drawing = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
    drawing = drawing.resize(image.size)
    combined_image = Image.alpha_composite(image.convert("RGBA"), drawing)
    plan_filename = f"{id_}-Plan.jpg"
    combined_image.convert("RGB").save(plan_filename, format="JPEG")

    dbx = authenticate_dropbox()
    with open(plan_filename, "rb") as f:
        dbx.files_upload(f.read(), f"{photo_dir}/{plan_filename}")

    os.remove(plan_filename)  # Cleanup local file
    return plan_filename


# Function to add a new record
def add_record(data, csv_path):
    df = pd.read_csv(csv_path)
    new_df = pd.DataFrame([data])
    df = pd.concat([df, new_df], ignore_index=True)

    # Save updated DataFrame back to Dropbox
    df.to_csv("temp_mangelmanagement.csv", index=False)
    dbx = authenticate_dropbox()
    with open("temp_mangelmanagement.csv", "rb") as f:
        dbx.files_upload(f.read(), csv_path, mode=dropbox.files.WriteMode("overwrite"))
    os.remove("temp_mangelmanagement.csv")  # Cleanup local temporary file
    return df


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

    projects = [p.name for p in dbx.files_list_folder("").entries if isinstance(p, dropbox.files.FolderMetadata)]
    selected_project = st.selectbox("Projekt auswählen", options=projects)

    if selected_project:
        st.subheader("Neue Pläne hochladen")
        uploaded_plan = st.file_uploader("Plan hochladen", type=["jpg", "jpeg", "png"])

        if uploaded_plan:
            plan_dir = f"/{selected_project}/Pläne"
            with open(uploaded_plan.name, "wb") as f:
                f.write(uploaded_plan.getbuffer())
            with open(uploaded_plan.name, "rb") as f:
                dbx.files_upload(f.read(), f"{plan_dir}/{uploaded_plan.name}")
            os.remove(uploaded_plan.name)  # Cleanup local file
            st.success(f"Plan '{uploaded_plan.name}' erfolgreich hochgeladen!")

# Load the selected project data
if selected_project:
    df, csv_path = load_project_data(selected_project)

    st.header(f"Projekt / Abnahme: {selected_project}")

    # List available plans from Dropbox
    plan_dir = f"/{selected_project}/Pläne"
    available_plans = [p.name for p in dbx.files_list_folder(plan_dir).entries if
                       isinstance(p, dropbox.files.FileMetadata)]
    selected_plan = st.selectbox("Plan auswählen für Markierungen", options=available_plans, index=0,
                                 key="selected_plan")

    # Load selected plan image and draw
    if selected_plan:
        plan_path = f"{plan_dir}/{selected_plan}"
        metadata, response = dbx.files_download(plan_path)
        image = Image.open(response.content)

        stroke_width = st.slider("Stiftbreite auswählen", 1, 25, 3)
        stroke_color = st.color_picker("Stiftfarbe auswählen", "#000000")

        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_image=image,
            update_streamlit=True,
            height=image.height,
            width=image.width,
            drawing_mode="freedraw",
            key="canvas",
        )

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
            # Save all photos taken
            if len(photos) > 0:
                photo_filenames = save_photos(photos, id_, erfassungsdatum.strftime("%Y-%m-%d"), unternehmer, apartment,
                                              room, selected_project)
            else:
                photo_filenames = []

            plan_filename = ""
            if selected_plan:
                plan_filename = save_plan_image(image, canvas_result, id_, selected_project)

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
                "Plan": plan_filename,
                "Bemerkung": remarks,
                "Zu erledigen bis": zu_erledigen_bis
            }

            df = add_record(data, csv_path)
            st.success(f"Mangel erfolgreich hinzugefügt! ID: {id_}")

            # Reset selected plan
            st.session_state.selected_plan = None

            # Rerun the page to immediately reflect the change in the table
            st.rerun()

    st.subheader(f"Bestehende Mängel für Projekt: {selected_project}")
    st.dataframe(df)
