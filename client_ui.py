import tkinter as tk
from tkinter import messagebox
import re
import pymysql

from client import Client

CLIENT_COMMAND = "\n**** Invalid syntax ****\nFormat of client's commands\n1. publish lname fname\n2. fetch fname\n\n"

SERVER_IP = 'localhost' 

PUBLISH_PATTERN = r"^publish\s[A-Z]:(/(\w)+)*(/\w+.[A-Za-z])\s\w+.[A-Za-z]$"
FETCH_PATTERN = r"^fetch\s(\w+.[A-Za-z]+)$"

class Client_App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Some declarations
        self.username, self.password = None, None
        self.client = None

        self.title("File Sharing Application")
        self.minsize(600, 400)

        # Used for manage the current page
        self.current_page_frame = None

        self.current_page_frame = self.main_page()
        self.current_page_frame.pack()

    def trigger(self, frame):
        self.current_page_frame.pack_forget()
        self.current_page_frame = frame()
        self.current_page_frame.pack()

    def submit(self, username_entry, password_entry):
        username = username_entry.get()
        password = password_entry.get()

        if username == "" or password == "":
            messagebox.showerror("Lỗi đăng kí", "Vui lòng điền đầy đủ thông tin.")
            return

        # Send username and password to server step
        self.client = Client(SERVER_IP, 5000, username, password)
        self.client.register()
        del self.client
        
        messagebox.showinfo("Đăng kí thành công", "Đăng kí thành công! Vui lòng đăng nhập để sử dụng dịch vụ.")

        self.current_page_frame.pack_forget()
        self.current_page_frame = self.sign_in()
        self.current_page_frame.pack()

    
    def sign_up(self):
        sign_up_frame = tk.Frame(borderwidth = 70)

        sign_up_label = tk.Label(sign_up_frame, text="SIGN UP", font=("San Serif", 24, "bold"), borderwidth = 10)
        sign_up_label.grid(row = 0, column = 0, columnspan = 10)

        sign_up_username_label = tk.Label(sign_up_frame, text="Username", font=("San Serif", 12, "bold"))
        sign_up_username_label.grid(row=1, column=0, sticky="we", padx = 10, pady=10)
        sign_up_username_entry = tk.Entry(sign_up_frame, width = 50)
        sign_up_username_entry.grid(row=1, column=1, columnspan = 9, sticky = "we", padx = 10, pady = 10)
        sign_up_username_entry.bind('<Return>', lambda event: self.submit(sign_up_username_entry, sign_up_password_entry))

        sign_up_password_label = tk.Label(sign_up_frame, text="Password", font=("San Serif", 12, "bold"))
        sign_up_password_label.grid(row=2, column=0, sticky="we", padx = 10, pady=10)
        sign_up_password_entry = tk.Entry(sign_up_frame, show="*", width = 50)
        sign_up_password_entry.grid(row=2, column=1, columnspan= 9, sticky = "we", padx = 10, pady = 10)
        sign_up_password_entry.bind('<Return>', lambda event: self.submit(sign_up_username_entry, sign_up_password_entry))

        sign_up_button = tk.Button(sign_up_frame, text="Sign Up", font=("San Serif", 12), command = lambda: self.submit(sign_up_username_entry, sign_up_password_entry))
        sign_up_button.grid(row = 3, column = 1)
        return_button = tk.Button(sign_up_frame, text = "Main Page", font=("San Serif", 12), command = lambda: self.trigger(self.main_page))
        return_button.grid(row = 3, column = 6)

        return sign_up_frame

    def check_login(self, username_entry, password_entry):
        username = username_entry.get()
        password = password_entry.get()

        self.client = Client(SERVER_IP, 5000, username, password)
        
        if username == "" or password == "":
            messagebox.showerror("Lỗi đăng nhập", "Vui lòng điền đầy đủ thông tin.")
            return
        
        ####### Use for testing, remove later ######
        if username == "phuchuynh" and password == "phuchuynh":
            self.username = username
            self.password = password

            messagebox.showinfo("Đăng nhập thành công", "Chào mừng, " + username + "!")
            
            self.current_page_frame.pack_forget()
            self.current_page_frame = self.terminal()
            self.current_page_frame.pack()
            return     
        ############################################

        if not self.client.is_login():
            del self.client
            messagebox.showerror("Lỗi đăng nhập", "Sai tên đăng nhập hoặc mật khẩu.")
        else:
            self.username = username
            self.password = password

            messagebox.showinfo("Đăng nhập thành công", "Chào mừng, " + username + "!")

            self.current_page_frame.pack_forget()
            self.current_page_frame = self.terminal()
            self.current_page_frame.pack()

    def sign_in(self):
        sign_in_frame = tk.Frame(borderwidth = 70)

        sign_in_label = tk.Label(sign_in_frame, text="SIGN IN", font=("San Serif", 24, "bold"), borderwidth = 10)
        sign_in_label.grid(row = 0, column = 0, columnspan = 10)

        sign_in_username_label = tk.Label(sign_in_frame, text="Username", font=("San Serif", 12, "bold"))
        sign_in_username_label.grid(row=1, column=0, sticky="we", padx = 10, pady=10)
        sign_in_username_entry = tk.Entry(sign_in_frame, width = 50)
        sign_in_username_entry.grid(row=1, column=1, columnspan = 9, sticky = "we", padx = 10, pady = 10)
        sign_in_username_entry.bind('<Return>', lambda event: self.check_login(sign_in_username_entry, sign_in_password_entry))

        sign_in_password_label = tk.Label(sign_in_frame, text="Password", font=("San Serif", 12, "bold"))
        sign_in_password_label.grid(row=2, column=0, sticky="we", padx = 10, pady=10)
        sign_in_password_entry = tk.Entry(sign_in_frame, show="*", width = 50)
        sign_in_password_entry.grid(row=2, column=1, columnspan= 9, sticky = "we", padx = 10, pady = 10)
        sign_in_password_entry.bind('<Return>', lambda event: self.check_login(sign_in_username_entry, sign_in_password_entry))

        sign_in_button = tk.Button(sign_in_frame, text="Sign In", font=("San Serif", 12), command = lambda: self.check_login(sign_in_username_entry, sign_in_password_entry))
        sign_in_button.grid(row = 3, column = 1)
        return_button = tk.Button(sign_in_frame, text = "Main Page", font=("San Serif", 12), command = lambda: self.trigger(self.main_page))
        return_button.grid(row = 3, column = 6)

        return sign_in_frame

    def main_page(self):
        main_page_frame = tk.Frame(borderwidth = 50)

        main_page_label = tk.Label(main_page_frame, text="FILE SHARING APPLICATION", font=("San Serif", 30, "bold"), borderwidth = 50)
        main_page_label.grid(row = 0, column = 0)

        b1 = tk.Button(main_page_frame, text = "Sign In", font=("San Serif", 14) , command = lambda: self.trigger(self.sign_in))
        b1.grid(row = 1, column = 0, pady = 5)

        
        b2 = tk.Button(main_page_frame, text = "Sign Up", font=("San Serif", 14), command = lambda: self.trigger(self.sign_up))
        b2.grid(row = 3, column = 0, pady = 5)

        return main_page_frame

    def command_processing(self, command):
        """
        Return True when the command is in the correct format
        """
        if re.search(FETCH_PATTERN, command) or re.search(PUBLISH_PATTERN, command):
            return True
        return False

    def get_response(self, command):
        """
        Use for get response for each command and show it for user

        Return:
        response (String): The result when execute the command
        """
        if re.search(FETCH_PATTERN, command):
            ### Handle fetch command code ###
            ...
            return "Result\n\n"
        else:
            ### Handle publish command code ####
            ...
            return "Result\n\n"

    # Trigger for excute command
    def execute_command(self, input_field, output_field):
        command = input_field.get()
        output_field.config(state=tk.NORMAL)
        output_field.insert(tk.END, f"{self.username}$ " + command + "\n", "color")
        input_field.delete(0, tk.END)

        if not self.command_processing(command):
            output_field.insert(tk.END, CLIENT_COMMAND, "color")
        else:
            result = self.get_response(command)
            output_field.insert(tk.END, result, "color")

        output_field.config(state=tk.DISABLED)

    def auto_scroll(self, frame):
        frame.see('end')
    
    def terminal(self):
        terminal_frame = tk.Frame()

        header = tk.Label(terminal_frame, text = f"Hello, {self.username}", font=("San Serif", 11, "bold"))
        header.grid(row = 0, column = 0, padx = 5, pady = 5)

        log_out_button = tk.Button(terminal_frame, text = "Log Out", command = lambda: self.trigger(self.main_page))
        log_out_button.grid(row = 0, column = 89, padx = 5, pady = 5)
        

        terminal_output = tk.Text(terminal_frame, background = "black")
        terminal_output.tag_configure("color", foreground="white")
        terminal_output.bind('<<TextInsert>>', lambda event, text_widget=terminal_output: self.auto_scroll(text_widget))
        terminal_output.insert(tk.END, "Terminal [Version 1.0.0]\nCopyright (C) phuchuynh. All right reserved.\n\n", "color")
        terminal_output.config(state = tk.DISABLED)
        

        terminal_output.grid(row = 1, column = 0, columnspan = 70)

        list_files = tk.Text(terminal_frame, background = "white", width = 25)
        list_files.grid(row = 1, column = 70, columnspan = 20)
        list_files.config(state = tk.DISABLED)

        input_header = tk.Label(terminal_frame, text = ">")
        input_header.grid(row = 2, column = 0, sticky="e")

        input_field = tk.Entry(terminal_frame)
        input_field.grid(row = 2, column = 1, columnspan = 89, sticky="we", padx = 5, pady = 10)

        input_field.bind('<Return>', lambda event: self.execute_command(input_field, terminal_output))
        
        return terminal_frame


if __name__ == "__main__":
    app = Client_App()
    app.mainloop()