import json
import requests
import time
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import socket
from urllib.parse import urlparse
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class ReconLiteApp:
    def __init__(self, master):
        self.master = master
        self.master.title("ReconLite - OSINT Tool")
        self.master.geometry("1000x600")
        
        # Style setup for ttk widgets
        style = ttk.Style(self.master)
        style.configure("TNotebook.Tab", font=('Helvetica', '10', 'bold'))
        style.configure("TButton", background="#add8e6", font=('Helvetica', 10))
        style.configure("TEntry", background="#e0ffff")
        style.configure("TLabel", foreground="#000080", font=('Helvetica', 10))
        
        # Create database if it doesn't exist
        self.create_database()
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Tabs
        self.ip_tab = ttk.Frame(self.notebook)
        self.phone_tab = ttk.Frame(self.notebook)
        self.username_tab = ttk.Frame(self.notebook)
        self.domain_tab = ttk.Frame(self.notebook)
        self.api_tab = ttk.Frame(self.notebook)
        self.help_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.ip_tab, text='IP')
        self.notebook.add(self.phone_tab, text='Phone')
        self.notebook.add(self.username_tab, text='User')
        self.notebook.add(self.domain_tab, text='Domain')
        self.notebook.add(self.api_tab, text='API')
        self.notebook.add(self.help_tab, text='Help')
        
        # Setup each tab with its specific input
        self.setup_ip_tab(self.ip_tab)
        self.setup_phone_tab(self.phone_tab)
        self.setup_username_tab(self.username_tab)
        self.setup_domain_tab(self.domain_tab)
        self.setup_api_tab(self.api_tab)
        self.create_help_tab(self.help_tab)

    def create_database(self):
        conn = sqlite3.connect('reconlite.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS search_results
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     type TEXT,
                     data TEXT,
                     result TEXT,
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS api_keys
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     service TEXT,
                     api_key TEXT)''')
        
        conn.commit()
        conn.close()
        self.load_api_key()

    def load_api_key(self):
        conn = sqlite3.connect('reconlite.db')
        c = conn.cursor()
        c.execute("SELECT api_key FROM api_keys WHERE service='IPWhois'")
        result = c.fetchone()
        conn.close()
        self.api_key = result[0] if result else ""

    def setup_ip_tab(self, frame):
        ip_label = ttk.Label(frame, text="Enter IP Address (e.g., 192.168.1.1):")
        ip_label.pack(pady=(20, 5))
        self.ip_entry = ttk.Entry(frame, width=50)
        self.ip_entry.pack(pady=5)
        ttk.Button(frame, text="Search IP", command=self.search_ip, style="TButton").pack(pady=10)
        self.setup_results_and_logs(frame)

    def setup_phone_tab(self, frame):
        phone_label = ttk.Label(frame, text="Enter Phone Number (e.g., +2547200123456):")
        phone_label.pack(pady=(20, 5))
        self.phone_entry = ttk.Entry(frame, width=50)
        self.phone_entry.pack(pady=5)
        ttk.Button(frame, text="Search Phone", command=self.search_phone, style="TButton").pack(pady=10)
        self.setup_results_and_logs(frame)

    def setup_username_tab(self, frame):
        username_label = ttk.Label(frame, text="Enter Username (e.g., johndoe):")
        username_label.pack(pady=(20, 5))
        self.username_entry = ttk.Entry(frame, width=50)
        self.username_entry.pack(pady=5)
        ttk.Button(frame, text="Search User", command=self.search_username, style="TButton").pack(pady=10)
        self.setup_results_and_logs(frame)

    def setup_domain_tab(self, frame):
        domain_label = ttk.Label(frame, text="Enter Domain Name (e.g., example.com):")
        domain_label.pack(pady=(20, 5))
        self.domain_entry = ttk.Entry(frame, width=50)
        self.domain_entry.pack(pady=5)
        ttk.Button(frame, text="Search Domain", command=self.search_domain, style="TButton").pack(pady=10)
        self.setup_results_and_logs(frame)

    def setup_api_tab(self, frame):
        api_key_label = ttk.Label(frame, text="IPWhois API Key:")
        api_key_label.pack(pady=(20, 5))
        self.api_entry = ttk.Entry(frame, width=50, show="*")
        self.api_entry.pack(pady=5)
        self.api_entry.insert(0, self.api_key)
        
        save_button = ttk.Button(frame, text="Save API Key", command=self.save_api_key, style="TButton")
        save_button.pack(pady=10)
        
        edit_button = ttk.Button(frame, text="Edit API Key", command=self.edit_api_key, style="TButton")
        edit_button.pack(pady=10)

    def setup_results_and_logs(self, frame):
        results_label = ttk.Label(frame, text="Results:", foreground="#000080")
        results_label.pack(pady=(20, 5))
        self.results_area = scrolledtext.ScrolledText(frame, width=80, height=15, wrap=tk.WORD, font=('Helvetica', 10))
        self.results_area.pack(pady=5)
        
        log_label = ttk.Label(frame, text="Logs:", foreground="#000080")
        log_label.pack(pady=(20, 5))
        self.logs_area = scrolledtext.ScrolledText(frame, width=80, height=5, wrap=tk.WORD, font=('Helvetica', 10))
        self.logs_area.pack(pady=5)

    def create_help_tab(self, frame):
        help_text = """
        **IP**:
        - Enter an IP address for geographical and network info.
        - Requires IPWhois API Key for some features.

        **Phone**:
        - Input an international phone number format.

        **User**:
        - Check username availability across social media.

        **Domain**:
        - Search for DNS information.

        **API**:
        - Save and edit API keys for services.

        **General**:
        - Results/logs are organized in separate areas.
        - All searches are saved automatically.
        """
        help_label = tk.Label(frame, text=help_text, justify=tk.LEFT, font=('Helvetica', 10), wraplength=500)
        help_label.pack(padx=20, pady=20)

    def search_ip(self):
        ip = self.ip_entry.get()
        if not ip:
            messagebox.showerror("Error", "Please enter an IP address.")
            return
        response = requests.get(f"http://ipwho.is/{ip}")
        if response.status_code == 200:
            result = response.json()
            self.update_results(json.dumps(result, indent=2))
            self.save_result("ip_search", ip, json.dumps(result))
            self.logs_area.insert(tk.END, f"IP Searched: {ip} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        else:
            self.update_results("IP not found or service unavailable.")
            self.logs_area.insert(tk.END, f"Error searching IP: {ip} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    def search_phone(self):
        phone = self.phone_entry.get()
        if not phone:
            messagebox.showerror("Error", "Please enter a phone number.")
            return
        try:
            parsed_number = phonenumbers.parse(phone, "ID")
            carrier_name = carrier.name_for_number(parsed_number, "en")
            location = geocoder.description_for_number(parsed_number, "id")
            result = f"Location: {location}\nCarrier: {carrier_name}\n"
            self.update_results(result)
            self.save_result("phone_search", phone, result)
            self.logs_area.insert(tk.END, f"Phone Searched: {phone} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        except phonenumbers.phonenumberutil.NumberParseException:
            self.update_results("Invalid phone number.")
            self.logs_area.insert(tk.END, f"Error searching phone: {phone} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    def search_username(self):
        username = self.username_entry.get()
        if not username:
            messagebox.showerror("Error", "Please enter a username.")
            return
        results = {}
        social_media = [
            {"url": "https://www.facebook.com/{}", "name": "Facebook"},
            {"url": "https://www.twitter.com/{}", "name": "Twitter"},
            # Add more social media platforms here
        ]
        for site in social_media:
            url = site['url'].format(username)
            response = requests.get(url)
            if response.status_code == 200:
                results[site['name']] = url
            else:
                results[site['name']] = "Username not found!"
        
        self.update_results(json.dumps(results, indent=2))
        self.save_result("username_search", username, json.dumps(results))
        self.logs_area.insert(tk.END, f"Username Searched: {username} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    def search_domain(self):
        domain = self.domain_entry.get()
        if not domain:
            messagebox.showerror("Error", "Please enter a domain name.")
            return
        try:
            ip = socket.gethostbyname(domain)
            result = f"Domain: {domain}\nIP Address: {ip}\n"
            self.update_results(result)
            self.save_result("domain_search", domain, result)
            self.logs_area.insert(tk.END, f"Domain Searched: {domain} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        except socket.gaierror:
            self.update_results("Domain not found or DNS resolution failed.")
            self.logs_area.insert(tk.END, f"Error searching domain: {domain} at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    def update_results(self, text):
        self.results_area.delete('1.0', tk.END)
        self.results_area.insert(tk.END, text)

    def save_result(self, type, data, result):
        conn = sqlite3.connect('reconlite.db')
        c = conn.cursor()
        c.execute("INSERT INTO search_results (type, data, result) VALUES (?, ?, ?)", (type, data, result))
        conn.commit()
        conn.close()

    def save_api_key(self):
        key = self.api_entry.get()
        if key:
            conn = sqlite3.connect('reconlite.db')
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO api_keys (service, api_key) VALUES (?, ?)", ('IPWhois', key))
            conn.commit()
            conn.close()
            self.api_key = key
            messagebox.showinfo("API Key", "API Key saved successfully!")
        else:
            messagebox.showerror("Error", "Please enter an API Key.")

    def edit_api_key(self):
        self.api_entry.config(state=tk.NORMAL)
        self.api_entry.delete(0, tk.END)
        self.api_entry.insert(0, self.api_key)

if __name__ == "__main__":
    root = tk.Tk()
    app = ReconLiteApp(root)
    root.mainloop()