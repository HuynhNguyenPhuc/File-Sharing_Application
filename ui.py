import time
import os.path
import PySimpleGUI as sg

"""-------------------------------------Init important information------------------------------------"""
# Anchor folder
folder_dir = "C:/Users/Admin/Pictures/Screenshots"

"""--------------------------------------------Create window------------------------------------------"""

name_row = [sg.Text("P2P FILE TRANSFERING", background_color='black', size=(100, 5))]  # First name row
console = [
    [sg.Text("Output\nCommand", size=(7, 25), justification='center', background_color='black'), sg.Multiline(key='-OUT-', size=(50, 25))],
    [sg.Text("Command", size=(7, 5), justification='center', background_color='black'), sg.Input(key='-COMMAND-', size=(50, 10))]
]  # Console screen
side = [
    [sg.Listbox(key='-FILES-', values=[], size=(50, 10))],
    [sg.Button(key='-PUBLISH-', button_text="Publish")],
    [sg.Listbox(values=[], size=(50, 10))],
    [sg.Button("Test")]
]  # Side screen
layout = [name_row, [sg.Column(console), sg.Column(side)]]  # Full layout
window = sg.Window("Demo window", layout=layout, finalize=True)  # Create window

"""-----------------------------------------Init event handling---------------------------------------"""

# Init for handling pressing "Enter" to submit command
window['-COMMAND-'].bind('<Return>', 'ENTER')

# Init for handling read-only in output screen
window['-OUT-'].bind("<FocusIn>", 'FOCUS_IN')
window['-OUT-'].bind("<FocusOut>", 'FOCUS_OUT')

# Init file list in anchor folder
file_list = os.listdir(folder_dir)
window['-FILES-'].update(values=file_list)

"""-----------------------------------------Main logic here---------------------------------------"""

while True:
    event, values = window.read()

    # Close the window
    if event == sg.WIN_CLOSED:
        break

    # Submit command
    elif event == "-COMMAND-ENTER":
        window["-OUT-"].print('>> ' + values['-COMMAND-'])
        window["-COMMAND-"].update(disabled=True)
        if values["-COMMAND-"].strip() == 'clear':
            window["-OUT-"].update(value=">> clear\n")
        window["-COMMAND-"].update(value="")
        window["-COMMAND-"].update(disabled=False)

    # Handle read-only in output screen
    elif event == "-OUT-FOCUS_IN":
        window['-OUT-'].update(disabled=True)
    elif event == "-OUT-FOCUS_OUT":
        window['-OUT-'].update(disabled=False)

window.close()
