import tkinter as tk
from tkinter import messagebox
import re
import pymysql
from threading import Thread, Lock
import time

from server import Server

SERVER_COMMAND = "**** Invalid syntax ****\nFormat of server's commands\n1. ping hostname\n2. discover hostname\n\n"

SERVER_USERNAME = 'admin'
SERVER_PASSWORD = 'admin'

PING_PATTERN = r"^ping\s[\w]+$"
DISCOVER_PATTERN = r"^discover\s[\w]+$"

class Server_App(tk.Tk):
    def __init__(self):
        super().__init__()

        # Some declarations
        self.username, self.password = None, None
        self.server = Server(5000)

        self.title("File Sharing Application")
        self.minsize(600, 400)

        # Used for manage the current page
        self.current_page_frame = None

        self.current_page_frame = self.main_page()
        self.current_page_frame.pack()

        self.closing = False
        self.thread1 = None
        self.mutex = Lock()

    def trigger(self, frame):
        self.current_page_frame.pack_forget()
        self.current_page_frame = frame()
        self.current_page_frame.pack()

    def check_login(self, username_entry, password_entry):
        username = username_entry.get()
        password = password_entry.get()
        
        if username == "" or password == "":
            messagebox.showerror("Lỗi đăng nhập", "Vui lòng điền đầy đủ thông tin.")
            return

        # Checking database step
        ####### Fix later, used for testing ######
        if username == SERVER_USERNAME and password == SERVER_PASSWORD:
            self.username = username
            self.password = password
            self.server.start()
            messagebox.showinfo("Đăng nhập thành công", "Chào mừng, " + self.username + "!")
        else:
            messagebox.showerror("Lỗi đăng nhập", "Sai tên đăng nhập hoặc mật khẩu.")
            return
        ###########################################

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

        return main_page_frame

    def command_processing(self, command):
        """
        Return True when the command is in the correct format
        """
        if re.search(PING_PATTERN, command) or re.search(DISCOVER_PATTERN, command):
            return True
        return False

    def get_response(self, command):
        """
        Use for get response for each command and show it for user

        Return:
        response (String): The result when execute the command
        """
        if re.search(PING_PATTERN, command):
            output = self.server.run('PING', 'abc')
        else:
            output = self.server.run('DISCOVER', 'abc')
        return output + '\n'

    # Trigger for excute command
    def execute_command(self, input_field, output_field):
        command = input_field.get()
        output_field.config(state=tk.NORMAL)
        output_field.insert(tk.END, f"{self.username}$ " + command + "\n", "color")
        input_field.delete(0, tk.END)

        if not self.command_processing(command):
            output_field.insert(tk.END, SERVER_COMMAND, "color")
        
        else:
            result = self.get_response(command)
            output_field.insert(tk.END, result, "color")

        output_field.config(state=tk.DISABLED)
    
    def terminal(self):
        self.closing = False
        terminal_frame = tk.Frame()

        header = tk.Label(terminal_frame, text = f"Hello, {self.username}", font=("San Serif", 16, "bold"))
        header.grid(row = 0, column = 0, padx = 5, pady = 5)

        log_out_button = tk.Button(terminal_frame, text = "Log Out", command = lambda: self.logout())
        log_out_button.grid(row = 0, column = 2, padx = 5, pady = 5, sticky='e')

        terminal_header = tk.Label(terminal_frame, text="Terminal",
                                   font=("San Serif", 9, "italic"))
        terminal_header.grid(row=1, column=0, sticky="n")

        terminal_output = tk.Text(terminal_frame, background = "black", width=50, height=30)
        terminal_output.tag_configure("color", foreground="white")
        terminal_output.insert(tk.END, "Terminal [Version 1.0.0]\nCopyright (C) phuchuynh. All right reserved.\n\n", "color")
        terminal_output.config(state = tk.DISABLED)
        terminal_output.grid(row = 1, column = 1, columnspan = 1)

        input_header = tk.Label(terminal_frame, text = "Command", font=("San Serif", 9, "italic"))
        input_header.grid(row = 2, column = 0, sticky="n")

        input_field = tk.Entry(terminal_frame)
        input_field.grid(row = 2, column = 1, columnspan = 1, sticky="we")
        input_field.bind('<Return>', lambda event: self.execute_command(input_field, terminal_output))

        server_output = tk.Text(terminal_frame, width=50, height=30)
        server_output.grid(row=1, column=2, columnspan=1, padx=5, pady=10)

        output_clear = tk.Button(terminal_frame, text = "Clear",
                                 command = lambda: self.clear_output(server_output), pady=5)
        output_clear.grid(row=2, column=2)

        self.thread1 = Thread(target=self.update_output, args=[server_output])
        self.thread1.start()
        
        return terminal_frame

    def logout(self):
        self.server.close()
        self.trigger(self.main_page)

    def update_output(self, server_output):
        while not self.closing:
            time.sleep(0.5)
            if self.closing:
                break
            self.server.queue_mutex.acquire()
            if not self.server.output_queue.empty():
                output = self.server.output_queue.get()
                server_output.insert(tk.END, output)
            self.server.queue_mutex.release()

    def clear_output(self, server_output):
        server_output.delete(0.1, tk.END)

    def close(self):
        self.closing = True
        if self.thread1:
            self.thread1.join()
        self.destroy()


if __name__ == "__main__":
    app = Server_App()
    app.protocol("WM_DELETE_WINDOW", app.close)
    app.mainloop()