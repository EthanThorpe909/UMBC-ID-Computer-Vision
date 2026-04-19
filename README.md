This project is for checking in and out of the UMBC campus. It scans IDs to verify information and keeps an active list of who is currently signed in.


# HOW IT WORKS


* **Host and Guest Sequence**: The first ID scanned is the host ID. The second ID scanned is the person who wants to check in.
* **Information Confirmation**: For each ID, you have to confirm that the scanned name and ID are correct before it moves on. 
* **Stability Check**: It only automatically clicks the photo when the name and ID match for 5 frames in a row. 
* **Active Sign-Out**: For the sign out, it checks if the person is already in the csv file and removes them after they are scanned. 
* **ID Validation**: It specifically looks for the 7 character ID for both the person signing in and the person checking in.

# CONTROLS


* **'i'**: Start Sign-In mode.
* **'o'**: Start Sign-Out mode.
* **'y'**: Confirm that the information on screen is correct.
* **'n'**: Reject the scan and rescan.
* **'q'**: Quit the program.

# TECHNICAL SPECS


* **EasyOCR**: Brain of the project that recognizes the text on the ID.
* **Face Detection**: Acts as a trigger so it only starts scanning when someone is actually in front of the camera.
* **Pandas**: Used to manage the database file and remove people when they sign out.
* **Database**: Sign-In_Log.csv stores the name, id number, and timestamp.
