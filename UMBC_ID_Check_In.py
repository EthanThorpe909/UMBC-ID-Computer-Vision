import cv2
import easyocr
import face_recognition
import re 
import os
import pandas as pd
import warnings
from datetime import datetime

# Suppress Mac-specific Torch warnings for a cleaner terminal
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

# Database setup using the 6-column format
LOG_FILE = "Sign-In_Log.csv"
HEADERS = ["Mode", "Host_Name", "Host_ID", "Guest_Name", "Guest_ID", "Timestamp"]

if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=HEADERS).to_csv(LOG_FILE, index=False)

print("Booting up EasyOCR...")
reader = easyocr.Reader(['en'], gpu=True) 

cap = cv2.VideoCapture(0)
print("UMBC ID Manager Started! Keys: 'i'=Sign In, 'o'=Sign Out, 'q'=Quit")

# State and stability variables
mode, step, frame_count = "", 0, 0
frame_skip_rate = 2 
stability_counter = 0
last_name_seen = ""

host_data = {"name": "", "id": ""}
current_scanned = {"name": "", "id": ""}

# UI and OCR coordinates from Source 1
PROXIMITY_THRESHOLD = 110 
GW, GH = 1000, 650 

while True:
    ret, frame = cap.read()
    if not ret: break

    h, w, _ = frame.shape
    gx1, gy1 = (w - GW) // 2, (h - GH) // 2
    gx2, gy2 = gx1 + GW, gy1 + GH

    # Dynamic status prompt based on step
    status_color = (255, 200, 0)
    prompt = "Select Mode: 'i'  Sign in or 'o' Sign out"
    
    if step == 1: prompt = f"Scan Host ({stability_counter}/5)"
    elif step == 2: prompt = f"Confirm Host: {current_scanned['name']}? (y/n)"
    elif step == 3: prompt = f"Scan Guest ({stability_counter}/5)"
    elif step == 4: prompt = f"Confirm Guest: {current_scanned['name']}? (y/n)"
    elif step == 5: prompt = f"Scan Sign-Out ({stability_counter}/5)"; status_color = (0, 0, 255)
    elif step == 6: prompt = f"Confirm Sign-Out: {current_scanned['name']}? (y/n)"

    # Draw UI guide
    cv2.rectangle(frame, (gx1, gy1), (gx2, gy2), status_color, 2)
    cv2.putText(frame, prompt, (gx1 + 10, gy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

    # Active scanning for steps 1, 3, and 5
    if step in [1, 3, 5]:
        small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb_small, model="hog")

        if len(faces) > 0:
            top, right, bottom, left = [v * 4 for v in faces[0]]
            if (right - left) >= PROXIMITY_THRESHOLD:
                # OCR field coordinates
                nt, nb = gy1 + 455, gy1 + 515
                it, ib = nb - 10, nb + 40
                nl, nr = gx1 + 350, gx2 - 250
                
                if frame_count % frame_skip_rate == 0:
                    n_crop, i_crop = frame[nt:nb, nl:nr], frame[it:ib, nl:nr]
                    tn, ti = "", ""
                    
                    if n_crop.size > 0:
                        res = reader.readtext(n_crop, detail=0)
                        if res: tn = re.sub(r'[^A-Z\s]', '', " ".join(res).upper()).strip()
                    
                    if i_crop.size > 0:
                        res = reader.readtext(i_crop, detail=0)
                        if res:
                            match = re.search(r'[A-Z]{2}\d{5}', "".join(res).upper().replace(" ",""))
                            if match: ti = match.group(0)

                    # Update stability if name and ID match previous frame
                    if tn and tn == last_name_seen and ti:
                        stability_counter += 1
                    else:
                        last_name_seen, stability_counter = tn, 0

                    if stability_counter >= 5:
                        current_scanned = {"name": tn, "id": ti}
                        stability_counter, step = 0, step + 1

    # Key inputs for navigation
    key = cv2.waitKey(1) & 0xFF
    if step == 0:
        if key == ord('i'): mode, step = "SIGN_IN", 1
        elif key == ord('o'): mode, step = "SIGN_OUT", 5
    elif key == ord('y'):
        if step == 2:
            host_data, step = current_scanned.copy(), 3
        elif step == 4:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_FILE, "a") as f:
                f.write(f"SIGN_IN,{host_data['name']},{host_data['id']},{current_scanned['name']},{current_scanned['id']},{ts}\n")
            step = 0
        elif step == 6:
            # Sign-Out: Find and remove the person from the CSV
            df = pd.read_csv(LOG_FILE)
            if current_scanned['id'] in df['Guest_ID'].values:
                df = df[df['Guest_ID'] != current_scanned['id']]
                df.to_csv(LOG_FILE, index=False)
                print(f"Removed: {current_scanned['name']}")
            else:
                print(f"Error: {current_scanned['id']} not found in active list.")
            step = 0
    elif key == ord('n'):
        step, stability_counter = step - 1, 0
    elif key == ord('q'):
        break

    frame_count += 1
    cv2.imshow('UMBC Logger', frame)

cap.release()
cv2.destroyAllWindows()