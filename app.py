import pandas as pd
from datetime import datetime
import time
import streamlit as st
from PIL import Image, ImageDraw
import os
from streamlit_drawable_canvas import st_canvas

# Base directory for projects
PROJECTS_DIR = "Projekte"

# Function to create a new project
def create_new_project(project_name):
    project_path = os.path.join(PROJECTS_DIR, project_name)

    if not os.path.exists(project_path):
        os.makedirs(project_path)
        os.makedirs(os.path.join(project_path, "Fotos"))
        os.makedirs(os.path.join(project_path, "Pläne"))  # Create folder for plans

        csv_path = os.path.join(project_path, "mangelmanagement.csv")
        pd.DataFrame(columns=[
            "ID", "Erfassungsdatum", "Unternehmer", "Gewerk", "Mangelname",
            "Mangelbeschreibung", "Wohnung", "Zimmer", "Ort", "Fotos", "Plan", "Bemerkung", "Zu erledigen bis"
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
            "Mangelbeschreibung", "Wohnung", "Zimmer", "Ort", "Fotos", "Plan", "Bemerkung", "Zu erledigen bis"
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

# Function to save the plan image with annotations
def save_plan_image(image, canvas_result, id_, project_name):
    photo_dir = os.path.join(PROJECTS_DIR, project_name, "Fotos")
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)

    drawing = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
    drawing = drawing.resize(image.size)
    combined_image = Image.alpha_composite(image.convert("RGBA"), drawing)
    plan_filename = f"{id_}-Plan.jpg"
    photo_path = os.path.join(photo_dir, plan_filename)
    combined_image.convert("RGB").save(photo_path, format="JPEG")

    return plan_filename

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

    if selected_project:
        st.subheader("Neue Pläne hochladen")
        uploaded_plan = st.file_uploader("Plan hochladen", type=["jpg", "jpeg", "png"])

        if uploaded_plan:
            plan_dir = os.path.join(PROJECTS_DIR, selected_project, "Pläne")
            if not os.path.exists(plan_dir):
                os.makedirs(plan_dir)

            plan_path = os.path.join(plan_dir, uploaded_plan.name)
            with open(plan_path, "wb") as f:
                f.write(uploaded_plan.getbuffer())
            st.success(f"Plan '{uploaded_plan.name}' erfolgreich hochgeladen!")

# Load the selected project data
if selected_project:
    df, csv_path = load_project_data(selected_project)

    st.header(f"Projekt / Abnahme: {selected_project}")

    # Liste der verfügbaren Pläne anzeigen
    plan_dir = os.path.join(PROJECTS_DIR, selected_project, "Pläne")
    available_plans = os.listdir(plan_dir) if os.path.exists(plan_dir) else []
    selected_plan = st.selectbox("Plan auswählen für Markierungen", options=available_plans)

    # Bild Plan laden und Zeichnen
    if selected_plan:
        plan_path = os.path.join(plan_dir, selected_plan)
        if os.path.exists(plan_path):
            image = Image.open(plan_path)

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
            # Speichere alle Fotos, die aufgenommen wurden
            if len(photos) > 0:
                photo_filenames = save_photos(photos, id_, erfassungsdatum.strftime("%Y-%m-%d"), unternehmer, apartment, room, selected_project)
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

            # Rerun the page to immediately reflect the change in the table
            st.rerun()

    st.subheader(f"Bestehende Mängel für Projekt: {selected_project}")
    st.dataframe(df)
