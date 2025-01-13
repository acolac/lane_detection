import cv2
import numpy as np
import datetime
import tkinter as tk
from tkinter import filedialog
 

root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename(title="Select file", filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*")))

if not file_path:
    raise Exception("No file selected")
print(f"Selected file: {file_path}")
 
cap = cv2.VideoCapture(file_path)

# dimensions
new_width, new_height = 400, 600
frame_index = 0

# fps + frame skip
fps = cap.get(cv2.CAP_PROP_FPS)
frame_skip = int(fps * 15) 

# var total lines
total_lines_spotted = 0

# total video time
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
video_duration = total_frames / fps

# time
current_day = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# img + buttons settings
pause_button = cv2.imread('pause.png')
quit_button = cv2.imread('quit.png')
left_button = cv2.imread('left.png')
right_button = cv2.imread('right.png')

button_size = (50, 50) 
pause_button = cv2.resize(pause_button, button_size)
quit_button = cv2.resize(quit_button, button_size)
left_button = cv2.resize(left_button, button_size)
right_button = cv2.resize(right_button, button_size)

button_y_offset = new_height - button_size[1] - 10  
button_x_offset = new_width - 4 * button_size[0] - 40 

paused = False

def mouse_callback(event, x, y, flags, param):
    global frame_index, paused
    if event == cv2.EVENT_LBUTTONDOWN:
        # pause
        if (x > button_x_offset and x < button_x_offset + button_size[0]) and \
           (y > button_y_offset and y < button_y_offset + button_size[1]):
            print("Pause button clicked!")
            paused = not paused

        # quit
        elif (x > button_x_offset + button_size[0] + 10 and x < button_x_offset + 2 * button_size[0] + 10) and \
             (y > button_y_offset and y < button_y_offset + button_size[1]):
            print("Quit button clicked!")
            cap.release()
            cv2.destroyAllWindows()
            exit()

        # back
        elif (x > button_x_offset + 2 * button_size[0] + 20 and x < button_x_offset + 3 * button_size[0] + 20) and \
             (y > button_y_offset and y < button_y_offset + button_size[1]):
            print("Left button clicked!")
            frame_index -= frame_skip
            if frame_index < 0:
                frame_index = 0 
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        # forward
        elif (x > button_x_offset + 3 * button_size[0] + 30 and x < button_x_offset + 4 * button_size[0] + 30) and \
             (y > button_y_offset and y < button_y_offset + button_size[1]):
            print("Right button clicked!")
            frame_index += frame_skip
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

# set up mouse callback
cv2.namedWindow('Lane Detection')
cv2.setMouseCallback('Lane Detection', mouse_callback)

while True:
    if not paused:
        ret, frame = cap.read()

        if not ret:
            print("Frame not available")
            break

        # resize frames
        frame = cv2.resize(frame, (new_width, new_height))

        # convert to black & white
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)

        # mask road
        mask = np.zeros_like(edges)
        height, width = edges.shape
        polygon = np.array([[
            (100, height),  # img stanga
            (width - 100, height),  # img dreapta
            (width // 2, height // 2),  # mijloc
        ]], np.int32)

        cv2.fillPoly(mask, polygon, 255)
        masked_edges = cv2.bitwise_and(edges, mask)

        lines = cv2.HoughLinesP(masked_edges, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=150)

        frame_with_lines = frame.copy()
        lines_in_frame = 0
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(frame_with_lines, (x1, y1), (x2, y2), (0, 255, 0), 3)
                lines_in_frame += 1

        # black & white (black background white yellow lines)
        inverted_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        inverted_frame = cv2.cvtColor(inverted_frame, cv2.COLOR_GRAY2BGR)

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(inverted_frame, (x1, y1), (x2, y2), (0, 255, 255), 3)

        # black background only for lines
        black_frame = np.zeros_like(frame)

        # draw lines on black
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                cv2.line(black_frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

        concatenated_image = np.concatenate((frame_with_lines, inverted_frame, black_frame), axis=1)

        # calculated time
        current_time = cap.get(cv2.CAP_PROP_POS_FRAMES) / fps
        current_time_str = str(datetime.timedelta(seconds=int(current_time)))

        # calculated total time
        total_time_str = str(datetime.timedelta(seconds=int(video_duration)))

        # text 
        text = f"Time: {current_time_str} / {total_time_str} | Day: {current_day} | Lines in Frame: {lines_in_frame} | Total Lines: {total_lines_spotted}"

        # total lines
        total_lines_spotted += lines_in_frame

        # text up right
        cv2.putText(concatenated_image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # buttons
        concatenated_image[button_y_offset:button_y_offset + button_size[1], button_x_offset:button_x_offset + button_size[0]] = pause_button
        concatenated_image[button_y_offset:button_y_offset + button_size[1], button_x_offset + button_size[0] + 10:button_x_offset + 2 * button_size[0] + 10] = quit_button
        concatenated_image[button_y_offset:button_y_offset + button_size[1], button_x_offset + 2 * button_size[0] + 20:button_x_offset + 3 * button_size[0] + 20] = left_button
        concatenated_image[button_y_offset:button_y_offset + button_size[1], button_x_offset + 3 * button_size[0] + 30:button_x_offset + 4 * button_size[0] + 30] = right_button

        # show buttons
        cv2.imshow('Lane Detection', concatenated_image)

    # control video
    key = cv2.waitKey(int(1000 / fps)) & 0xFF
    if key == ord('q'):  
        break

cap.release()
cv2.destroyAllWindows()