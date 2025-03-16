import cv2
import face_recognition
import pickle
import numpy as np
import firebase_admin
from firebase_admin import credentials, db
import datetime
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "enter database url"
})

# Load pre-existing encodings
with open("ENcodedFile.p", "rb") as file:
    
    encodeAndIdList = pickle.load(file)
encode, studentIDs = encodeAndIdList

# Function to process the group photo and update attendance
def process_group_photo(group_photo_path):
    # Load the group photo
    img = cv2.imread(group_photo_path)
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Find all faces in the group photo
    face_locations = face_recognition.face_locations(imgS)
    face_encodings = face_recognition.face_encodings(imgS, face_locations)

    # If faces are detected in the group photo
    if face_encodings:
        for encoding, location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(encode, encoding)
            face_distances = face_recognition.face_distance(encode, encoding)

            match_index = np.argmin(face_distances)
            if matches[match_index]:
                # If a match is found, update the attendance
                student_id = studentIDs[match_index]
                print(f"Match found for student ID: {student_id}")

                # Fetch the student info from Firebase
                student_info = db.reference(f"Students/{student_id}").get()
                print(student_info)

                # Get the last attendance date and calculate time difference
                last_attendance = student_info["last_attendence_date"]
                last_attendance_dt = datetime.datetime.strptime(last_attendance, "%Y-%m-%d %H:%M:%S")
                time_diff = (datetime.datetime.now() - last_attendance_dt).total_seconds()

                # Update the attendance if more than 10 seconds have passed since the last attendance
                if time_diff > 10:
                    student_info["total_attendence"] += 1
                    student_info["last_attendence_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db.reference(f"Students/{student_id}").set(student_info)
                    print(f"Attendance updated for {student_info['name']}. Total attendance: {student_info['total_attendence']}")
                else:
                    print(f"Already marked attendance recently for {student_info['name']}. Skipping update.")
    else:
        print("No faces detected in the group photo.")

# Main flow
if __name__ == "__main__":
    # Provide the path to the saved group photo
    group_photo_path = "group_photo_sample.jpg"  # Replace with the actual file path of the saved group photo
    
    # Process the group photo and update attendance
    process_group_photo(group_photo_path)
