import tkinter as tk
from tkinter import ttk, messagebox
import psycopg2
from psycopg2 import OperationalError
from datetime import datetime

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "EndJAic43BOI15J1",
    "host": "horribly-golden-sandgrouse.data-1.use1.tembo.io"
}

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        # Ustawienie schematu na 'vind' po połączeniu
        with conn.cursor() as cur:
            cur.execute("SET search_path TO vind;")
        return conn
    except OperationalError as e:
        messagebox.showerror("Błąd Bazy Danych", f"Nie można połączyć się z bazą danych: {e}")
        return None

def execute_query(query, params=None, fetch=True, commit=False):
    conn = connect_db()
    if not conn:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if commit:
                conn.commit()
            if fetch:
                return cur.fetchall()
            else:
                return True  # Zwróć True, jeśli operacja (insert, update, delete) powiodła się
    except Exception as e:
        messagebox.showerror("Błąd Bazy Danych", f"Błąd wykonania zapytania: {e}")
        return None
    finally:
        if conn:
           conn.close()

def fetch_data(table):
    query = f"SELECT * FROM {table}"
    return execute_query(query)

def insert_data(table, data):
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s'] * len(data))
    values = list(data.values())
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    return execute_query(query, params=values, fetch=False, commit=True)

def update_data(table, data, id_column, id_value):
    set_clause = ', '.join([f"{key}=%s" for key in data.keys()])
    values = list(data.values())
    values.append(id_value)
    query = f"UPDATE {table} SET {set_clause} WHERE {id_column}=%s"
    return execute_query(query, params=values, fetch=False, commit=True)


def delete_data(table, id_column, id_value):
    query = f"DELETE FROM {table} WHERE {id_column} = %s"
    return execute_query(query, params=(id_value,), fetch=False, commit=True)

# --- Obsługa tabeli Klienci ---
def load_clients_table():
    data = fetch_data('Klienci')
    clear_treeview(clients_tree)
    if data:
        for row in data:
            clients_tree.insert('', 'end', values=row)

def open_client_form(mode='add', client_data=None):
    client_form = tk.Toplevel(root)
    client_form.title("Formularz Klienta")

    labels = ["Imię", "Nazwisko", "PESEL", "Adres", "Telefon", "Email"]
    entries = {}
    db_labels = ["imie", "nazwisko", "pesel", "adres", "telefon", "email"]

    for i, label in enumerate(labels):
        tk.Label(client_form, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='w')
        entry = tk.Entry(client_form)
        if client_data and client_data[i+1]:  # +1 bo id_klienta nie ma być wypełniane
            entry.insert(0, client_data[i+1])
        entry.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
        entries[db_labels[i]] = entry

    def submit_client():
        data = {label: entry.get() for label, entry in entries.items()}
        if mode == 'add':
             if insert_data('Klienci', data):
                messagebox.showinfo("Sukces", "Klient dodany pomyślnie")
                load_clients_table()
                client_form.destroy()
        elif mode == 'edit':
             if update_data('Klienci', data, 'id_klienta', client_data[0]):
                 messagebox.showinfo("Sukces", "Klient zaktualizowany pomyślnie")
                 load_clients_table()
                 client_form.destroy()

    tk.Button(client_form, text="Zatwierdź", command=submit_client).grid(row=len(labels), column=0, columnspan=2, padx=5, pady=10)
    if mode == 'edit':
       tk.Button(client_form, text="Usuń", command=lambda: delete_client(client_data[0], client_form)).grid(row=len(labels)+1, column=0, columnspan=2, padx=5, pady=10)


def delete_client(client_id, form):
    if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć tego klienta?"):
        if delete_data('Klienci', 'id_klienta', client_id):
           messagebox.showinfo("Sukces", "Klient usunięty pomyślnie")
           load_clients_table()
           form.destroy()

def edit_client():
    selected_item = clients_tree.selection()
    if selected_item:
        client_data = clients_tree.item(selected_item)['values']
        open_client_form('edit', client_data)
    else:
        messagebox.showinfo("Informacja", "Zaznacz klienta do edycji")

# --- Obsługa tabeli Pożyczki ---
def load_loans_table():
    data = fetch_data('Pożyczki')
    clear_treeview(loans_tree)
    if data:
         for row in data:
             loans_tree.insert('', 'end', values=row)

def open_loan_form(mode='add', loan_data=None):
    loan_form = tk.Toplevel(root)
    loan_form.title("Formularz Pożyczki")

    # Pobierz listę ID klientów
    clients = fetch_data('Klienci')
    client_ids = [client[0] for client in clients]


    labels = ["ID Klienta", "Kwota", "Ilość Rat", "Kwota Raty", "Data Rozpoczęcia", "Sposób Płatności", "Data Spłaty", "Status"]
    entries = {}
    db_labels = ["id_klienta", "kwota", "ilosc_rat", "kwota_raty", "data_rozpoczecia", "sposob_platnosci", "data_splaty", "status"]

    for i, label in enumerate(labels):
        tk.Label(loan_form, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='w')
        if label == "ID Klienta":
             entry = ttk.Combobox(loan_form, values=client_ids)
             if loan_data and loan_data[i+1]: # +1 bo id_pozyczki nie ma być wypełniane
                 entry.set(loan_data[i+1])
        elif label == "Data Rozpoczęcia" or label == "Data Spłaty":
            entry = tk.Entry(loan_form)
            if loan_data and loan_data[i+1]:
                date_str = loan_data[i+1]
                if isinstance(date_str, datetime):
                    date_str = date_str.strftime("%Y-%m-%d")
                entry.insert(0, date_str)
        elif label == "Status":
            entry = ttk.Combobox(loan_form, values=['Aktywna', 'Spłacona', 'Po Terminie'])
            if loan_data and loan_data[i+1]:
                 entry.set(loan_data[i+1])

        else:
            entry = tk.Entry(loan_form)
            if loan_data and loan_data[i+1]:
                entry.insert(0, loan_data[i+1])
        entry.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
        entries[db_labels[i]] = entry

    def submit_loan():
        data = {label: entry.get() for label, entry in entries.items()}
        # Konwertuj daty do formatu akceptowalnego przez bazę danych
        try:
           data['data_rozpoczecia'] = datetime.strptime(data['data_rozpoczecia'], '%Y-%m-%d').date() if data['data_rozpoczecia'] else None
           data['data_splaty'] = datetime.strptime(data['data_splaty'], '%Y-%m-%d').date() if data['data_splaty'] else None
        except ValueError:
              messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.")
              return
        if mode == 'add':
           if insert_data('Pożyczki', data):
                 messagebox.showinfo("Sukces", "Pożyczka dodana pomyślnie")
                 load_loans_table()
                 loan_form.destroy()
        elif mode == 'edit':
            if update_data('Pożyczki', data, 'id_pozyczki', loan_data[0]):
                 messagebox.showinfo("Sukces", "Pożyczka zaktualizowana pomyślnie")
                 load_loans_table()
                 loan_form.destroy()

    tk.Button(loan_form, text="Zatwierdź", command=submit_loan).grid(row=len(labels), column=0, columnspan=2, padx=5, pady=10)

    if mode == 'edit':
        tk.Button(loan_form, text="Usuń", command=lambda: delete_loan(loan_data[0], loan_form)).grid(row=len(labels)+1, column=0, columnspan=2, padx=5, pady=10)

def delete_loan(loan_id, form):
    if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć tę pożyczkę?"):
        if delete_data('Pożyczki', 'id_pozyczki', loan_id):
            messagebox.showinfo("Sukces", "Pożyczka usunięta pomyślnie")
            load_loans_table()
            form.destroy()
def edit_loan():
    selected_item = loans_tree.selection()
    if selected_item:
       loan_data = loans_tree.item(selected_item)['values']
       open_loan_form('edit', loan_data)
    else:
         messagebox.showinfo("Informacja", "Zaznacz pożyczkę do edycji")
# --- Obsługa tabeli Wpłaty ---
def load_payments_table():
    data = fetch_data('Wpłaty')
    clear_treeview(payments_tree)
    if data:
        for row in data:
           payments_tree.insert('', 'end', values=row)

def open_payment_form(mode='add', payment_data=None):
    payment_form = tk.Toplevel(root)
    payment_form.title("Formularz Wpłaty")
    # Pobierz listę ID pożyczek
    loans = fetch_data('Pożyczki')
    loan_ids = [loan[0] for loan in loans]

    labels = ["ID Pożyczki", "Data Wpłaty", "Kwota Wpłaty"]
    entries = {}
    db_labels = ["id_pozyczki", "data_wplaty", "kwota_wplaty"]

    for i, label in enumerate(labels):
        tk.Label(payment_form, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='w')

        if label == "ID Pożyczki":
            entry = ttk.Combobox(payment_form, values=loan_ids)
            if payment_data and payment_data[i+1]:
                entry.set(payment_data[i+1])
        elif label == "Data Wpłaty":
           entry = tk.Entry(payment_form)
           if payment_data and payment_data[i+1]:
              date_str = payment_data[i+1]
              if isinstance(date_str, datetime):
                  date_str = date_str.strftime("%Y-%m-%d")
              entry.insert(0, date_str)

        else:
            entry = tk.Entry(payment_form)
            if payment_data and payment_data[i+1]:
                 entry.insert(0, payment_data[i+1])

        entry.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
        entries[db_labels[i]] = entry

    def submit_payment():
        data = {label: entry.get() for label, entry in entries.items()}
        # Konwertuj datę do formatu akceptowalnego przez bazę danych
        try:
              data['data_wplaty'] = datetime.strptime(data['data_wplaty'], '%Y-%m-%d').date() if data['data_wplaty'] else None
        except ValueError:
             messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.")
             return

        if mode == 'add':
           if insert_data('Wpłaty', data):
                 messagebox.showinfo("Sukces", "Wpłata dodana pomyślnie")
                 load_payments_table()
                 payment_form.destroy()
        elif mode == 'edit':
            if update_data('Wpłaty', data, 'id_wplaty', payment_data[0]):
                 messagebox.showinfo("Sukces", "Wpłata zaktualizowana pomyślnie")
                 load_payments_table()
                 payment_form.destroy()

    tk.Button(payment_form, text="Zatwierdź", command=submit_payment).grid(row=len(labels), column=0, columnspan=2, padx=5, pady=10)
    if mode == 'edit':
       tk.Button(payment_form, text="Usuń", command=lambda: delete_payment(payment_data[0], payment_form)).grid(row=len(labels)+1, column=0, columnspan=2, padx=5, pady=10)

def delete_payment(payment_id, form):
    if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć tę wpłatę?"):
        if delete_data('Wpłaty', 'id_wplaty', payment_id):
            messagebox.showinfo("Sukces", "Wpłata usunięta pomyślnie")
            load_payments_table()
            form.destroy()
def edit_payment():
    selected_item = payments_tree.selection()
    if selected_item:
        payment_data = payments_tree.item(selected_item)['values']
        open_payment_form('edit', payment_data)
    else:
        messagebox.showinfo("Informacja", "Zaznacz wpłatę do edycji")

# --- Obsługa tabeli Windykacja ---
def load_recovery_table():
    data = fetch_data('Windykacja')
    clear_treeview(recovery_tree)
    if data:
        for row in data:
            recovery_tree.insert('', 'end', values=row)

def open_recovery_form(mode='add', recovery_data=None):
    recovery_form = tk.Toplevel(root)
    recovery_form.title("Formularz Windykacji")
    # Pobierz listę ID pożyczek
    loans = fetch_data('Pożyczki')
    loan_ids = [loan[0] for loan in loans]

    labels = ["ID Pożyczki", "Data Akcji", "Opis", "Status"]
    entries = {}
    db_labels = ["id_pozyczki", "data_akcji", "opis", "status"]

    for i, label in enumerate(labels):
        tk.Label(recovery_form, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='w')
        if label == "ID Pożyczki":
           entry = ttk.Combobox(recovery_form, values=loan_ids)
           if recovery_data and recovery_data[i+1]:
                entry.set(recovery_data[i+1])
        elif label == "Data Akcji":
           entry = tk.Entry(recovery_form)
           if recovery_data and recovery_data[i+1]:
              date_str = recovery_data[i+1]
              if isinstance(date_str, datetime):
                  date_str = date_str.strftime("%Y-%m-%d")
              entry.insert(0, date_str)
        elif label == "Status":
           entry = ttk.Combobox(recovery_form, values=['Oczekująca', 'W Trakcie', 'Zakończona'])
           if recovery_data and recovery_data[i+1]:
               entry.set(recovery_data[i+1])
        else:
           entry = tk.Entry(recovery_form)
           if recovery_data and recovery_data[i+1]:
                entry.insert(0, recovery_data[i+1])
        entry.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
        entries[db_labels[i]] = entry


    def submit_recovery():
        data = {label: entry.get() for label, entry in entries.items()}
        # Konwertuj datę do formatu akceptowalnego przez bazę danych
        try:
              data['data_akcji'] = datetime.strptime(data['data_akcji'], '%Y-%m-%d').date() if data['data_akcji'] else None
        except ValueError:
             messagebox.showerror("Błąd", "Nieprawidłowy format daty. Użyj YYYY-MM-DD.")
             return
        if mode == 'add':
           if insert_data('Windykacja', data):
                messagebox.showinfo("Sukces", "Windykacja dodana pomyślnie")
                load_recovery_table()
                recovery_form.destroy()
        elif mode == 'edit':
           if update_data('Windykacja', data, 'id_windykacji', recovery_data[0]):
                messagebox.showinfo("Sukces", "Windykacja zaktualizowana pomyślnie")
                load_recovery_table()
                recovery_form.destroy()

    tk.Button(recovery_form, text="Zatwierdź", command=submit_recovery).grid(row=len(labels), column=0, columnspan=2, padx=5, pady=10)
    if mode == 'edit':
         tk.Button(recovery_form, text="Usuń", command=lambda: delete_recovery(recovery_data[0], recovery_form)).grid(row=len(labels)+1, column=0, columnspan=2, padx=5, pady=10)

def delete_recovery(recovery_id, form):
    if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć tę windykację?"):
        if delete_data('Windykacja', 'id_windykacji', recovery_id):
            messagebox.showinfo("Sukces", "Windykacja usunięta pomyślnie")
            load_recovery_table()
            form.destroy()

def edit_recovery():
    selected_item = recovery_tree.selection()
    if selected_item:
        recovery_data = recovery_tree.item(selected_item)['values']
        open_recovery_form('edit', recovery_data)
    else:
        messagebox.showinfo("Informacja", "Zaznacz windykację do edycji")

# --- Obsługa tabeli TypyWindykacji ---
def load_recovery_types_table():
    data = fetch_data('TypyWindykacji')
    clear_treeview(recovery_types_tree)
    if data:
        for row in data:
            recovery_types_tree.insert('', 'end', values=row)

def open_recovery_type_form(mode='add', recovery_type_data=None):
    recovery_type_form = tk.Toplevel(root)
    recovery_type_form.title("Formularz Typu Windykacji")

    labels = ["Nazwa Typu"]
    entries = {}
    db_labels = ["nazwa_typu"]

    for i, label in enumerate(labels):
         tk.Label(recovery_type_form, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='w')
         entry = tk.Entry(recovery_type_form)
         if recovery_type_data and recovery_type_data[i+1]:
            entry.insert(0, recovery_type_data[i+1])
         entry.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
         entries[db_labels[i]] = entry


    def submit_recovery_type():
        data = {label: entry.get() for label, entry in entries.items()}

        if mode == 'add':
             if insert_data('TypyWindykacji', data):
                  messagebox.showinfo("Sukces", "Typ windykacji dodany pomyślnie")
                  load_recovery_types_table()
                  recovery_type_form.destroy()
        elif mode == 'edit':
           if update_data('TypyWindykacji', data, 'id_typu_windykacji', recovery_type_data[0]):
               messagebox.showinfo("Sukces", "Typ windykacji zaktualizowany pomyślnie")
               load_recovery_types_table()
               recovery_type_form.destroy()

    tk.Button(recovery_type_form, text="Zatwierdź", command=submit_recovery_type).grid(row=len(labels), column=0, columnspan=2, padx=5, pady=10)
    if mode == 'edit':
        tk.Button(recovery_type_form, text="Usuń", command=lambda: delete_recovery_type(recovery_type_data[0], recovery_type_form)).grid(row=len(labels)+1, column=0, columnspan=2, padx=5, pady=10)

def delete_recovery_type(recovery_type_id, form):
     if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć ten typ windykacji?"):
         if delete_data('TypyWindykacji', 'id_typu_windykacji', recovery_type_id):
            messagebox.showinfo("Sukces", "Typ windykacji usunięty pomyślnie")
            load_recovery_types_table()
            form.destroy()

def edit_recovery_type():
    selected_item = recovery_types_tree.selection()
    if selected_item:
       recovery_type_data = recovery_types_tree.item(selected_item)['values']
       open_recovery_type_form('edit', recovery_type_data)
    else:
        messagebox.showinfo("Informacja", "Zaznacz typ windykacji do edycji")

# --- Obsługa tabeli Pozyczki_TypyWindykacji ---
def load_loans_recovery_types_table():
   data = fetch_data('Pozyczki_TypyWindykacji')
   clear_treeview(loans_recovery_types_tree)
   if data:
        for row in data:
            loans_recovery_types_tree.insert('', 'end', values=row)

def open_loans_recovery_type_form(mode='add', loans_recovery_type_data=None):
    loans_recovery_type_form = tk.Toplevel(root)
    loans_recovery_type_form.title("Formularz Pożyczki - Typ Windykacji")
    # Pobierz listę ID pożyczek i typów windykacji
    loans = fetch_data('Pożyczki')
    loan_ids = [loan[0] for loan in loans]
    recovery_types = fetch_data('TypyWindykacji')
    recovery_type_ids = [recovery_type[0] for recovery_type in recovery_types]

    labels = ["ID Pożyczki", "ID Typu Windykacji"]
    entries = {}
    db_labels = ["id_pozyczki", "id_typu_windykacji"]
    for i, label in enumerate(labels):
        tk.Label(loans_recovery_type_form, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='w')
        if label == "ID Pożyczki":
              entry = ttk.Combobox(loans_recovery_type_form, values=loan_ids)
              if loans_recovery_type_data and loans_recovery_type_data[i]:
                   entry.set(loans_recovery_type_data[i])
        elif label == "ID Typu Windykacji":
              entry = ttk.Combobox(loans_recovery_type_form, values=recovery_type_ids)
              if loans_recovery_type_data and loans_recovery_type_data[i]:
                 entry.set(loans_recovery_type_data[i])
        entry.grid(row=i, column=1, padx=5, pady=5, sticky='ew')
        entries[db_labels[i]] = entry

    def submit_loans_recovery_type():
        data = {label: entry.get() for label, entry in entries.items()}

        if mode == 'add':
             if insert_data('Pozyczki_TypyWindykacji', data):
                   messagebox.showinfo("Sukces", "Powiązanie dodane pomyślnie")
                   load_loans_recovery_types_table()
                   loans_recovery_type_form.destroy()
        elif mode == 'edit':
           # W tym przypadku edycja jest trudna, bo to klucz złożony. Najlepiej usunąć i dodać nowe
           if messagebox.askyesno("Potwierdzenie", "Edycja nie jest możliwa, usunąć powiązanie i dodać nowe?"):
               if delete_data('Pozyczki_TypyWindykacji', 'id_pozyczki', loans_recovery_type_data[0]):
                  if delete_data('Pozyczki_TypyWindykacji', 'id_typu_windykacji', loans_recovery_type_data[1]):
                      if insert_data('Pozyczki_TypyWindykacji', data):
                           messagebox.showinfo("Sukces", "Powiązanie zaktualizowane pomyślnie")
                           load_loans_recovery_types_table()
                           loans_recovery_type_form.destroy()
    tk.Button(loans_recovery_type_form, text="Zatwierdź", command=submit_loans_recovery_type).grid(row=len(labels), column=0, columnspan=2, padx=5, pady=10)
    if mode == 'edit':
         tk.Button(loans_recovery_type_form, text="Usuń", command=lambda: delete_loans_recovery_type(loans_recovery_type_data, loans_recovery_type_form)).grid(row=len(labels)+1, column=0, columnspan=2, padx=5, pady=10)

def delete_loans_recovery_type(loans_recovery_type_id, form):
      if messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz usunąć to powiązanie?"):
           if delete_data('Pozyczki_TypyWindykacji', 'id_pozyczki', loans_recovery_type_id[0]):
               if delete_data('Pozyczki_TypyWindykacji', 'id_typu_windykacji', loans_recovery_type_id[1]):
                  messagebox.showinfo("Sukces", "Powiązanie usunięte pomyślnie")
                  load_loans_recovery_types_table()
                  form.destroy()

def edit_loans_recovery_type():
    selected_item = loans_recovery_types_tree.selection()
    if selected_item:
        loans_recovery_type_data = loans_recovery_types_tree.item(selected_item)['values']
        open_loans_recovery_type_form('edit', loans_recovery_type_data)
    else:
       messagebox.showinfo("Informacja", "Zaznacz powiązanie do edycji")

# --- Funkcje widoków ---
def load_loans_view():
    query = "SELECT * FROM WidokPozyczek"
    data = execute_query(query)
    clear_treeview(view_loans_tree)
    if data:
       for row in data:
          view_loans_tree.insert('', 'end', values=row)
def load_clients_view():
    query = "SELECT * FROM WidokKlientow"
    data = execute_query(query)
    clear_treeview(view_clients_tree)
    if data:
        for row in data:
             view_clients_tree.insert('', 'end', values=row)
# --- Funkcje raportów ---
def generate_report_loans():
    query = "SELECT id_pozyczki, imie, nazwisko, kwota, kwota_pozostala FROM WidokPozyczek"
    data = execute_query(query)
    if data:
        report_window = tk.Toplevel(root)
        report_window.title("Raport Pożyczek")
        text_area = tk.Text(report_window, wrap="word", width=100)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        headers = ["ID Pożyczki", "Imię", "Nazwisko", "Kwota", "Kwota Pozostała"]
        text_area.insert(tk.END, "\t".join(headers) + "\n")
        text_area.insert(tk.END, "-" * 100 + "\n")

        for row in data:
           text_area.insert(tk.END, "\t".join(str(x) for x in row) + "\n")
        text_area.config(state=tk.DISABLED)  # Ustawienie text area jako tylko do odczytu
    else:
        messagebox.showinfo("Informacja", "Brak danych do wygenerowania raportu")


def generate_report_clients():
   query = "SELECT id_klienta, imie, nazwisko, pesel, kwota_pozyczki, suma_wplat, kwota_pozostala FROM WidokKlientow where kwota_pozyczki is not NULL"
   data = execute_query(query)

   if data:
        report_window = tk.Toplevel(root)
        report_window.title("Raport Klientów i Ich Pożyczek")
        text_area = tk.Text(report_window, wrap="word", width=100)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        headers = ["ID Klienta", "Imię", "Nazwisko", "PESEL", "Kwota Pożyczki", "Suma Wpłat", "Kwota Pozostała"]
        text_area.insert(tk.END, "\t".join(headers) + "\n")
        text_area.insert(tk.END, "-" * 100 + "\n")

        for row in data:
            text_area.insert(tk.END, "\t".join(str(x) for x in row) + "\n")
        text_area.config(state=tk.DISABLED)
   else:
        messagebox.showinfo("Informacja", "Brak danych do wygenerowania raportu")

def generate_report_payments():
    query = "SELECT k.imie, k.nazwisko, p.kwota AS kwota_pozyczki, w.data_wplaty, w.kwota_wplaty FROM Wpłaty w JOIN Pożyczki p ON w.id_pozyczki = p.id_pozyczki JOIN Klienci k ON p.id_klienta = k.id_klienta"
    data = execute_query(query)

    if data:
        report_window = tk.Toplevel(root)
        report_window.title("Raport Wpłat Klientów")
        text_area = tk.Text(report_window, wrap="word", width=100)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        headers = ["Imię Klienta", "Nazwisko Klienta", "Kwota Pożyczki", "Data Wpłaty", "Kwota Wpłaty"]
        text_area.insert(tk.END, "\t".join(headers) + "\n")
        text_area.insert(tk.END, "-" * 100 + "\n")

        for row in data:
            text_area.insert(tk.END, "\t".join(str(x) for x in row) + "\n")
        text_area.config(state=tk.DISABLED)

    else:
        messagebox.showinfo("Informacja", "Brak danych do wygenerowania raportu")


# --- Funkcja pomocnicza do czyszczenia Treeview ---
def clear_treeview(tree):
    for item in tree.get_children():
        tree.delete(item)

# --- Interfejs graficzny ---
root = tk.Tk()
root.title("Aplikacja Zarządzania Pożyczkami")

# --- Tworzenie zakładek ---
tabControl = ttk.Notebook(root)
tab_klienci = ttk.Frame(tabControl)
tab_pozyczki = ttk.Frame(tabControl)
tab_wplaty = ttk.Frame(tabControl)
tab_windykacja = ttk.Frame(tabControl)
tab_typy_windykacji = ttk.Frame(tabControl)
tab_pozyczki_typy_windykacji = ttk.Frame(tabControl)
tab_widok_pozyczki = ttk.Frame(tabControl)
tab_widok_klienci = ttk.Frame(tabControl)
tab_raporty = ttk.Frame(tabControl)

tabControl.add(tab_klienci, text='Klienci')
tabControl.add(tab_pozyczki, text='Pożyczki')
tabControl.add(tab_wplaty, text='Wpłaty')
tabControl.add(tab_windykacja, text='Windykacja')
tabControl.add(tab_typy_windykacji, text='Typy Windykacji')
tabControl.add(tab_pozyczki_typy_windykacji, text='Pożyczki - Typy Windykacji')
tabControl.add(tab_widok_pozyczki, text='Widok Pożyczek')
tabControl.add(tab_widok_klienci, text='Widok Klientów')
tabControl.add(tab_raporty, text='Raporty')
tabControl.pack(expand=1, fill="both")

# --- TAB KLIENCI ---
clients_tree = ttk.Treeview(tab_klienci, columns=("id_klienta", "imie", "nazwisko", "pesel", "adres", "telefon", "email"), show="headings")
clients_tree.heading("id_klienta", text="ID")
clients_tree.heading("imie", text="Imię")
clients_tree.heading("nazwisko", text="Nazwisko")
clients_tree.heading("pesel", text="PESEL")
clients_tree.heading("adres", text="Adres")
clients_tree.heading("telefon", text="Telefon")
clients_tree.heading("email", text="Email")
clients_tree.column("id_klienta", width=30)
clients_tree.column("imie", width=80)
clients_tree.column("nazwisko", width=100)
clients_tree.column("pesel", width=100)
clients_tree.column("adres", width=150)
clients_tree.column("telefon", width=80)
clients_tree.column("email", width=150)
clients_tree.pack(expand=1, fill="both")
tk.Button(tab_klienci, text="Dodaj klienta", command=lambda: open_client_form('add')).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_klienci, text="Edytuj klienta", command=edit_client).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_klienci, text="Odśwież", command=load_clients_table).pack(side=tk.LEFT, padx=5, pady=5)

# --- TAB POŻYCZKI ---
loans_tree = ttk.Treeview(tab_pozyczki, columns=("id_pozyczki", "id_klienta", "kwota", "ilosc_rat", "kwota_raty", "data_rozpoczecia", "sposob_platnosci", "data_splaty", "status"), show="headings")
loans_tree.heading("id_pozyczki", text="ID")
loans_tree.heading("id_klienta", text="ID Klienta")
loans_tree.heading("kwota", text="Kwota")
loans_tree.heading("ilosc_rat", text="Ilość Rat")
loans_tree.heading("kwota_raty", text="Kwota Raty")
loans_tree.heading("data_rozpoczecia", text="Data Rozpoczęcia")
loans_tree.heading("sposob_platnosci", text="Sposób Płatności")
loans_tree.heading("data_splaty", text="Data Spłaty")
loans_tree.heading("status", text="Status")
loans_tree.column("id_pozyczki", width=30)
loans_tree.column("id_klienta", width=60)
loans_tree.column("kwota", width=80)
loans_tree.column("ilosc_rat", width=60)
loans_tree.column("kwota_raty", width=80)
loans_tree.column("data_rozpoczecia", width=100)
loans_tree.column("sposob_platnosci", width=100)
loans_tree.column("data_splaty", width=100)
loans_tree.column("status", width=80)
loans_tree.pack(expand=1, fill="both")
tk.Button(tab_pozyczki, text="Dodaj pożyczkę", command=lambda: open_loan_form('add')).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_pozyczki, text="Edytuj pożyczkę", command=edit_loan).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_pozyczki, text="Odśwież", command=load_loans_table).pack(side=tk.LEFT, padx=5, pady=5)

# --- TAB WPŁATY ---
payments_tree = ttk.Treeview(tab_wplaty, columns=("id_wplaty", "id_pozyczki", "data_wplaty", "kwota_wplaty"), show="headings")
payments_tree.heading("id_wplaty", text="ID")
payments_tree.heading("id_pozyczki", text="ID Pożyczki")
payments_tree.heading("data_wplaty", text="Data Wpłaty")
payments_tree.heading("kwota_wplaty", text="Kwota Wpłaty")
payments_tree.pack(expand=1, fill="both")
tk.Button(tab_wplaty, text="Dodaj wpłatę", command=lambda: open_payment_form('add')).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_wplaty, text="Edytuj wpłatę", command=edit_payment).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_wplaty, text="Odśwież", command=load_payments_table).pack(side=tk.LEFT, padx=5, pady=5)

# --- TAB WINDYKACJA ---
recovery_tree = ttk.Treeview(tab_windykacja, columns=("id_windykacji", "id_pozyczki", "data_akcji", "opis", "status"), show="headings")
recovery_tree.heading("id_windykacji", text="ID")
recovery_tree.heading("id_pozyczki", text="ID Pożyczki")
recovery_tree.heading("data_akcji", text="Data Akcji")
recovery_tree.heading("opis", text="Opis")
recovery_tree.heading("status", text="Status")
recovery_tree.pack(expand=1, fill="both")
tk.Button(tab_windykacja, text="Dodaj windykację", command=lambda: open_recovery_form('add')).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_windykacja, text="Edytuj windykację", command=edit_recovery).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_windykacja, text="Odśwież", command=load_recovery_table).pack(side=tk.LEFT, padx=5, pady=5)

# --- TAB TYPY WINDYKACJI ---
recovery_types_tree = ttk.Treeview(tab_typy_windykacji, columns=("id_typu_windykacji", "nazwa_typu"), show="headings")
recovery_types_tree.heading("id_typu_windykacji", text="ID")
recovery_types_tree.heading("nazwa_typu", text="Nazwa Typu")
recovery_types_tree.pack(expand=1, fill="both")
tk.Button(tab_typy_windykacji, text="Dodaj typ windykacji", command=lambda: open_recovery_type_form('add')).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_typy_windykacji, text="Edytuj typ windykacji", command=edit_recovery_type).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_typy_windykacji, text="Odśwież", command=load_recovery_types_table).pack(side=tk.LEFT, padx=5, pady=5)

# --- TAB POŻYCZKI - TYPY WINDYKACJI ---
loans_recovery_types_tree = ttk.Treeview(tab_pozyczki_typy_windykacji, columns=("id_pozyczki", "id_typu_windykacji"), show="headings")
loans_recovery_types_tree.heading("id_pozyczki", text="ID Pożyczki")
loans_recovery_types_tree.heading("id_typu_windykacji", text="ID Typu Windykacji")
loans_recovery_types_tree.pack(expand=1, fill="both")
tk.Button(tab_pozyczki_typy_windykacji, text="Dodaj powiązanie", command=lambda: open_loans_recovery_type_form('add')).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_pozyczki_typy_windykacji, text="Edytuj powiązanie", command=edit_loans_recovery_type).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_pozyczki_typy_windykacji, text="Odśwież", command=load_loans_recovery_types_table).pack(side=tk.LEFT, padx=5, pady=5)

# --- TAB WIDOK POŻYCZEK ---
view_loans_tree = ttk.Treeview(tab_widok_pozyczki, columns=("id_pozyczki", "imie", "nazwisko", "kwota", "ilosc_rat", "kwota_raty", "data_rozpoczecia", "data_splaty","sposob_platnosci", "suma_wplat", "kwota_pozostala", "status"), show="headings")
view_loans_tree.heading("id_pozyczki", text="ID Pożyczki")
view_loans_tree.heading("imie", text="Imię Klienta")
view_loans_tree.heading("nazwisko", text="Nazwisko Klienta")
view_loans_tree.heading("kwota", text="Kwota Pożyczki")
view_loans_tree.heading("ilosc_rat", text="Ilość Rat")
view_loans_tree.heading("kwota_raty", text="Kwota Raty")
view_loans_tree.heading("data_rozpoczecia", text="Data Rozpoczęcia")
view_loans_tree.heading("data_splaty", text="Data Spłaty")
view_loans_tree.heading("sposob_platnosci", text="Sposób Płatności")
view_loans_tree.heading("suma_wplat", text="Suma Wpłat")
view_loans_tree.heading("kwota_pozostala", text="Kwota Pozostała")
view_loans_tree.heading("status", text="Status")
view_loans_tree.column("id_pozyczki", width=30)
view_loans_tree.column("imie", width=80)
view_loans_tree.column("nazwisko", width=100)
view_loans_tree.column("kwota", width=80)
view_loans_tree.column("ilosc_rat", width=60)
view_loans_tree.column("kwota_raty", width=80)
view_loans_tree.column("data_rozpoczecia", width=100)
view_loans_tree.column("data_splaty", width=100)
view_loans_tree.column("sposob_platnosci", width=100)
view_loans_tree.column("suma_wplat", width=80)
view_loans_tree.column("kwota_pozostala", width=80)
view_loans_tree.column("status", width=80)
view_loans_tree.pack(expand=1, fill="both")
tk.Button(tab_widok_pozyczki, text="Odśwież", command=load_loans_view).pack(side=tk.LEFT, padx=5, pady=5)

# --- TAB WIDOK KLIENTÓW ---
view_clients_tree = ttk.Treeview(tab_widok_klienci, columns=("id_klienta", "imie", "nazwisko", "pesel", "adres", "telefon", "email", "id_pozyczki", "kwota_pozyczki", "ilosc_rat", "kwota_raty", "data_rozpoczecia", "data_splaty", "sposob_platnosci", "suma_wplat", "kwota_pozostala","status"), show="headings")
view_clients_tree.heading("id_klienta", text="ID Klienta")
view_clients_tree.heading("imie", text="Imię")
view_clients_tree.heading("nazwisko", text="Nazwisko")
view_clients_tree.heading("pesel", text="PESEL")
view_clients_tree.heading("adres", text="Adres")
view_clients_tree.heading("telefon", text="Telefon")
view_clients_tree.heading("email", text="Email")
view_clients_tree.heading("id_pozyczki", text="ID Pożyczki")
view_clients_tree.heading("kwota_pozyczki", text="Kwota Pożyczki")
view_clients_tree.heading("ilosc_rat", text="Ilość Rat")
view_clients_tree.heading("kwota_raty", text="Kwota Raty")
view_clients_tree.heading("data_rozpoczecia", text="Data Rozpoczęcia")
view_clients_tree.heading("data_splaty", text="Data Spłaty")
view_clients_tree.heading("sposob_platnosci", text="Sposób Płatności")
view_clients_tree.heading("suma_wplat", text="Suma Wpłat")
view_clients_tree.heading("kwota_pozostala", text="Kwota Pozostała")
view_clients_tree.heading("status", text="Status")
view_clients_tree.column("id_klienta", width=30)
view_clients_tree.column("imie", width=80)
view_clients_tree.column("nazwisko", width=100)
view_clients_tree.column("pesel", width=100)
view_clients_tree.column("adres", width=150)
view_clients_tree.column("telefon", width=80)
view_clients_tree.column("email", width=150)
view_clients_tree.column("id_pozyczki", width=60)
view_clients_tree.column("kwota_pozyczki", width=80)
view_clients_tree.column("ilosc_rat", width=60)
view_clients_tree.column("kwota_raty", width=80)
view_clients_tree.column("data_rozpoczecia", width=100)
view_clients_tree.column("data_splaty", width=100)
view_clients_tree.column("sposob_platnosci", width=100)
view_clients_tree.column("suma_wplat", width=80)
view_clients_tree.column("kwota_pozostala", width=80)
view_clients_tree.column("status", width=80)
view_clients_tree.pack(expand=1, fill="both")
tk.Button(tab_widok_klienci, text="Odśwież", command=load_clients_view).pack(side=tk.LEFT, padx=5, pady=5)

# --- TAB RAPORTY ---
tk.Button(tab_raporty, text="Raport Pożyczek", command=generate_report_loans).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_raporty, text="Raport Klientów i Pożyczek", command=generate_report_clients).pack(side=tk.LEFT, padx=5, pady=5)
tk.Button(tab_raporty, text="Raport Wpłat", command=generate_report_payments).pack(side=tk.LEFT, padx=5, pady=5)

# --- Inicjalizacja danych ---
load_clients_table()
load_loans_table()
load_payments_table()
load_recovery_table()
load_recovery_types_table()
load_loans_recovery_types_table()
load_loans_view()
load_clients_view()

root.mainloop()