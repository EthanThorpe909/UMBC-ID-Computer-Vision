import cv2
import easyocr
import face_recognition
import re 

print("Booting up EasyOCR...")
reader = easyocr.Reader(['en'], gpu=True) 

cap = cv2.VideoCapture(0)
print("UMBC ID Scanner started! Hold up your ID. Press 'ctrl - C' to quit.")

frame_skip_rate = 5
frame_count = 0

final_name = ""
final_id = ""

PROXIMITY_THRESHOLD = 110 
#Main box parameters
GUIDE_WIDTH = 1000
GUIDE_HEIGHT = 650 

while True:
    ret, frame = cap.read()
    if not ret: break

    h, w, _ = frame.shape

#Main box where to put ID in
    gx1 = (w - GUIDE_WIDTH) // 2
    gy1 = (h - GUIDE_HEIGHT) // 2
    gx2 = gx1 + GUIDE_WIDTH
    gy2 = gy1 + GUIDE_HEIGHT

    cv2.rectangle(frame, (gx1, gy1), (gx2, gy2), (255, 200, 0), 2)
    cv2.rectangle(frame, (gx1, gy1 - 30), (gx2, gy1), (255, 200, 0), -1)
    cv2.putText(frame, "ALIGN ID WITHIN THIS BOX", (gx1 + 10, gy1 - 8), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    # ---------------------------------------------------------
    # STEP 2: Find the Face (High-Speed Trigger)
    # ---------------------------------------------------------
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    
    face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")

    if len(face_locations) > 0:
        top, right, bottom, left = face_locations[0]
        top *= 4; right *= 4; bottom *= 4; left *= 4
        face_width = right - left

        # Draw the face anchor
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
# Checks if ID is within Bounding box
        if face_width < PROXIMITY_THRESHOLD:
            cv2.putText(frame, "MOVE ID CLOSER!", (left - 50, top - 20), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
            final_name = ""
            final_id = ""
        else:
            cv2.putText(frame, "DISTANCE: GOOD", (left, top - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

#  checks bounding box for Name  
            name_left = gx1 + 350       
            name_right = gx2 - 250       
            name_top = gy1 + 455        
            name_bottom = gy1 + 515     
# bounding box for ID
            id_left = name_left         
            id_right = name_right       
            id_top = name_bottom - 10 
            id_bottom = id_top + 50     

#name for ID and Name on screen
            cv2.rectangle(frame, (name_left, name_top), (name_right, name_bottom), (255, 0, 255), 2)
            cv2.rectangle(frame, (id_left, id_top), (id_right, id_bottom), (255, 255, 255), 2)

#OCR image text recognition
            if frame_count % frame_skip_rate == 0:
                name_left_c, name_right_c = max(0, name_left), min(w, name_right)
                name_top_c, name_bottom_c = max(0, name_top), min(h, name_bottom)
                id_left_c, id_right_c = max(0, id_left), min(w, id_right)
                id_top_c, id_bottom_c = max(0, id_top), min(h, id_bottom)

                name_crop = frame[name_top_c:name_bottom_c, name_left_c:name_right_c]
                id_crop = frame[id_top_c:id_bottom_c, id_left_c:id_right_c]

                # Regex for name stripping anything that isnt a Letter
                if name_crop.size > 0:
                    raw_name_list = reader.readtext(name_crop, detail=0)
                    if raw_name_list:
                        temp_name = " ".join(raw_name_list).upper()
                        final_name = re.sub(r'[^A-Z\s]', '', temp_name).strip()

                # Checks for IDs that they start with a Capital Letter and end with 5 letters
                if id_crop.size > 0:
                    raw_id_list = reader.readtext(id_crop, detail=0)
                    if raw_id_list:
                        raw_id_string = "".join(raw_id_list).upper().replace(" ", "")
                        match = re.search(r'[A-Z]{2}\d{5}', raw_id_string)
                        if match:
                            final_id = match.group(0)
                        else:
                            final_id = ""

            # Display cleaned data on screen
            cv2.putText(frame, f"NAME: {final_name}", (name_left, name_bottom + 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
            cv2.putText(frame, f"ID: {final_id}", (id_left, id_bottom + 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            if final_name or final_id:
                print(f"Validated Data -> Name: {final_name} | ID: {final_id}")

    else:
        cv2.putText(frame, "Looking for Face...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        final_name = ""
        final_id = ""

    frame_count += 1
    cv2.imshow('Final UMBC ID Scanner', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()