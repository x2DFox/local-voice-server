from tkinter import Tk, PhotoImage, ttk, Menu, filedialog, BooleanVar, Toplevel, messagebox, Text, END
from datetime import datetime
import configparser
import webbrowser
import threading
import socket
import secrets
import random
import string

############################################################

CONFIG_PATH = "config.ini"
config = configparser.ConfigParser()

DEFAULTS = {
    "show_warning": "True",
}


def load_config():
    config.read(CONFIG_PATH, encoding="UTF-8")
    if config.has_option("main", "show_warning"):
        return
    config["main"] = DEFAULTS.copy()
    save_config()


def save_config():
    with open(CONFIG_PATH, "w", encoding="UTF-8") as f:
        config.write(f)


def warning_window():
    window = Toplevel(root)
    window.title("Шифрование не реализовано")
    window.geometry("400x200")
    window.resizable(width=False, height=False)
    window.grab_set()
    window.focus_force()

    txt = ("Пароль и аудио передаются в открытом виде независимо от того,\nлокальная это сеть или публичный адрес.\n"
           "Если сервер доступен из интернета - любой сможет подслушать\nразговор и узнать пароль.\n")
    ttk.Label(window, text=txt).place(x=10, y=10)

    understand = BooleanVar(value=False)
    dont_show = BooleanVar(value=False)

    def toggle_continue():
        status = "normal" if understand.get() else "disabled"
        continue_button.config(state=status)
        dont_show_check.config(state=status)

    def close_window():
        if dont_show.get():
            config["main"]["show_warning"] = "False"
            save_config()
        window.destroy()
        root.deiconify()

    def close_app():
        window.destroy()
        root.destroy()

    ttk.Checkbutton(window, text="Я понимаю и хочу продолжить",
                    variable=understand, command=toggle_continue).place(x=10, y=95)
    dont_show_check = ttk.Checkbutton(window, text="Больше не показывать", variable=dont_show, state="disabled")
    dont_show_check.place(x=10, y=115)

    continue_button = ttk.Button(window, text="Продолжить", state="disabled", command=close_window)
    continue_button.place(x=10, y=165, width=185)
    ttk.Button(window, text="Закрыть", command=close_app).place(x=205, y=165, width=185)

    window.protocol("WM_DELETE_WINDOW", close_app)

############################################################


# Перехватываем комбинации CTRL+A/C/V/X в полях ввода
def block_input(event, is_entry=False):
    if event.state & 0x0004 and event.keycode == 65:
        event.widget.event_generate("<<SelectAll>>")
        return "break"
    if event.state & 0x0004 and event.keycode == 67:
        event.widget.event_generate("<<Copy>>")
        return "break"
    if event.state & 0x0004 and event.keycode == 86:
        if is_entry:
            event.widget.event_generate("<<Paste>>")
            return "break"
        return "break"
    if event.state & 0x0004 and event.keycode == 88:
        if is_entry:
            event.widget.event_generate("<<Cut>>")
            return "break"
        return "break"
    if is_entry:
        return None
    return "break"


# Открываем дочернее окно один раз, повторный вызов поднимает уже открытое
def custom_window(name, title, dev=False):
    if hasattr(root, name) and getattr(root, name) is not None:
        getattr(root, name).lift()
        getattr(root, name).focus()
        return

    window = Toplevel(root)
    window.title(title)
    window.resizable(width=False, height=False)
    window.focus()

    if dev:
        ttk.Label(window, image=IMAGE).pack(padx=10, pady=10)
    else:
        txt = Text(window, relief="solid", font=("TkDefaultFont"), wrap="word", width=83, height=26)
        with open("LICENSE.txt", "r", encoding="UTF-8") as f:
            content = f.read()
        txt.insert("1.0", content)
        txt.config(state="disabled")
        txt.bind("<Key>", block_input)
        txt.pack(padx=10, pady=10)

    def close_window():
        window.destroy()
        setattr(root, name, None)

    window.protocol("WM_DELETE_WINDOW", close_window)
    setattr(root, name, window)


def version():
    messagebox.showinfo(title="Версия", message="v0.2.0 [BETA]\n\n"
                                                "- Интерфейс переделан в графический\n"
                                                "- Добавлен файл конфигурации\n"
                                                "- Логика сервера обернута в своем потоке\n"
                                                "- Сервер теперь получает IP-адрес клиента\n"
                                                "- Добавлена проверка порта и пароля при запуске\n"
                                                "- Добавлена возможность сохранить журнал\n"
                                                "- Установлен лимит символов для пароля\n"
                                                "- Добавлена возможность копировать пароль")


def developer(x2dfox=False, git=False):
    if x2dfox:
        custom_window(name="image_window", title="x2DFox", dev=True)
    elif git:
        choice = messagebox.askyesno(title="GitHub", message="Перейти на страницу разработчика?")
        if choice:
            webbrowser.open("https://github.com/x2DFox")
    else:
        choice = messagebox.askyesno(title="Telegram", message="Перейти в канал разработчика?")
        if choice:
            webbrowser.open("https://t.me/x2DFox")


def license():
    custom_window(name="license_window", title="BSD 3-Clause License")


############################################################


def random_port():
    port_entry.delete(0, END)
    port_entry.insert(0, random.randint(49152, 65535))


def generate():
    char = []
    char.extend(string.ascii_letters)
    char.extend(string.digits)
    char.extend(string.punctuation)

    genpass = []
    for _ in range(16):
        genpass.append(secrets.choice(char))
    password_entry.delete(0, END)
    password_entry.insert(0, ''.join(genpass))


def copy():
    if not password_entry.get():
        messagebox.showerror(title="Ошибка", message="Нечего копировать")
    else:
        root.clipboard_clear()
        root.clipboard_append(password_entry.get())


def save():
    log_content = log.get("1.0", END).strip()
    if not log_content:
        messagebox.showerror(title="Ошибка", message="Журнал пустой")
        return

    template = (f"local_voice_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_log.txt")
    filename = filedialog.asksaveasfilename(title="Сохранить журнал",
                                            defaultextension=".txt",
                                            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
                                            initialfile=template)
    if not filename:
        return

    try:
        with open(filename, "w", encoding="UTF-8") as f:
            f.write(log_content)
        messagebox.showinfo(title="Успех", message=f'''Журнал сохранен по пути:\n"{filename}"''')
    except Exception as e:
        messagebox.showerror(title="Ошибка", message=f"Не удалось сохранить журнал:\n{e}")


def log_message(message):
    log.config(state="normal")
    log.insert(END, message)
    log.see(END)
    log.config(state="disabled")


############################################################

# Параметры сети
CHUNK = 1024            # Размер аудио-пакета

# Глобальные переменные
clients = []            # Список подключенных клиентов
nicknames = {}          # Словарь {сокет: (никнейм, ip-адрес)}
server_running = False  # Статус сервера

############################################################


# Отправляет аудио данные всем кроме отправителя
def broadcast(data, sender):
    for client in clients[:]:       # Перебираем всех клиентов
        if client == sender:        # Пропускаем отправителя, чтобы он не слышал себя
            continue
        try:
            client.send(data)       # Отправляем аудио клиенту
        except (BrokenPipeError, ConnectionResetError):
            clients.remove(client)  # Если клиент отвалился - удаляем его


# Принимает аудио от клиента и рассылает остальным
def handle_client(client):
    while True:
        try:
            data = client.recv(CHUNK)      # Получаем аудио-пакет от клиента
            if not data:                   # Если данных нет - клиент отключился
                break
            broadcast(data, client)        # Рассылаем аудио всем остальным клиентам
        except (ConnectionResetError, BrokenPipeError):
            break                          # Если ошибка - выходим из цикла

    # Удаляем отключившегося клиента
    if client in clients:
        name, client_ip = nicknames.get(client, ("Unknown", "0.0.0.0"))  # Получаем ник клиента
        clients.remove(client)                                           # Удаляем клиента из списка
        if client in nicknames:                                          # Удаляем ник из словаря
            del nicknames[client]
        client.close()                                                   # Закрываем соединение
        log_message(f"❌ {name} ({client_ip}) отключился\n")


############################################################

# Проверяем настройки, блокируем интерфейс и запускаем поток сервера
def run_server():
    global server_running

    port_str = port_entry.get().strip()
    try:
        port = int(port_str)
        if not (49152 <= port <= 65535):
            messagebox.showerror(title="Ошибка", message="Порт: неверный диапазон")
            return
    except ValueError:
        messagebox.showerror(title="Ошибка", message="Порт: нечисловое значение")
        return

    password = password_entry.get()
    if len(password) < 8 or len(password) > 32:
        messagebox.showerror(title="Ошибка", message="Пароль должен быть от 8-и до 32-х символов")
        return
    if " " in password:
        messagebox.showerror(title="Ошибка", message="Пароль не должен содержать пробелы")
        return

    # Блокируем интерфейс
    port_entry.config(state="disabled")
    password_entry.config(state="disabled")
    random_button.config(state="disabled")
    generate_button.config(state="disabled")
    start_button.config(text="ОСТАНОВИТЬ", command=stop_server)

    # Очищаем журнал
    log.config(state="normal")
    log.delete(1.0, END)
    log.config(state="disabled")

    server_running = True

    def server_work():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Создаем серверный сокет (IPv4, TCP)
        sock.bind(("0.0.0.0", port))                              # Привязываем к порту (0.0.0.0 - все IP-интерфейсы)
        sock.listen(5)                                            # Размер очереди ожидающих подключений (backlog)
        sock.settimeout(0.5)                                      # Таймаут для accept для проверки server_running

        log_message(f"✅ Сервер запущен на порту: {port}\n")
        log_message(f"🔑 Пароль: {password}\n\n")
        log_message("⏳ Ожидание подключений...\n")

        # Подключаем клиентов
        while server_running:
            try:
                client = None                     # Обнуляем переменную
                try:
                    client, _ = sock.accept()     # Ждем подключения клиента, адрес не нужен
                except socket.timeout:            # Если таймаут, продолжаем цикл
                    continue
                if client is None:                # Проверяем, что клиент есть
                    continue

                # Проверка пароля
                client.settimeout(5)                      # Таймаут 5 сек на ввод пароля
                client_pass = client.recv(1024).decode()  # Получаем пароль от клиента
                client_ip = client.getpeername()[0]       # Получаем IP клиента
                if client_pass != password:               # Если пароль не совпадает, отправляем отказ
                    client.send("BAD".encode())
                    client.close()                        # Закрываем соединение
                    log_message(f"❌ Клиент ({client_ip}) недопущен: неверный пароль\n")
                    continue                              # Переходим к следующему клиенту
                client.send("OK".encode())                # Если пароль совпадает, отправляем "OK"
                client.settimeout(None)                   # Сбросим таймаут после проверки пароля

                # Получаем никнейм
                nickname = client.recv(1024).decode()
                clients.append(client)                     # Добавляем в список
                nicknames[client] = (nickname, client_ip)  # Сохраняем ник и IP-адрес в словарь
                log_message(f"✅ {nickname} ({client_ip}) подключился\n")

                # Создаем поток для обработки текущего клиента
                threading.Thread(target=handle_client, args=(client,), daemon=True).start()

            except Exception as e:
                if server_running:
                    log_message("\n" + f"⚠️ Ошибка: {e}")
                break

        # Закрываем все ресурсы
        for client in clients:  # Перебираем всех клиентов
            try:
                client.close()  # Закрываем соединение
            except OSError:
                pass            # Если ошибка, то игнорируем
        sock.close()            # Закрываем серверный сокет
        log_message("\n❌ Сервер остановлен")

        # Разблокируем интерфейс
        port_entry.config(state="normal")
        password_entry.config(state="normal")
        random_button.config(state="normal")
        generate_button.config(state="normal")
        start_button.config(text="ЗАПУСТИТЬ", command=run_server)

    # Запускаем поток сервера
    threading.Thread(target=server_work, daemon=True).start()


def stop_server():
    global server_running
    server_running = False


############################################################

root = Tk()
root.withdraw()
root.title("Local Voice [SERVER]")
icon = PhotoImage(file="resources/16x16.png")
root.iconphoto(True, icon)
root.geometry("600x400")
root.resizable(width=False, height=False)

main_menu = Menu(tearoff=0)
file_menu = Menu(tearoff=0)
developer_menu = Menu(tearoff=0)

file_menu.add_command(label="Версия", command=version)
file_menu.add_cascade(label="Разработчик", menu=developer_menu)
file_menu.add_command(label="Лицензия", command=license)

developer_menu.add_command(label="x2DFox", command=lambda: developer(x2dfox=True))
IMAGE = PhotoImage(file="resources/developer.png")
developer_menu.add_command(label="GitHub", command=lambda: developer(git=True))
developer_menu.add_command(label="Telegram", command=lambda: developer())

main_menu.add_cascade(label="Информация", menu=file_menu)
root.config(menu=main_menu)

ttk.Frame(relief="solid").place(x=10, y=10, width=580, height=56)

ttk.Label(text="Порт").place(x=15, y=15)
ttk.Label(text="(49152 - 65535)").place(x=65, y=15)
port_entry = ttk.Entry()
port_entry.bind("<Key>", lambda e: block_input(e, is_entry=True))
port_entry.place(x=155, y=15, width=240)
random_button = ttk.Button(text="Случайный", command=random_port)
random_button.place(x=400, y=13, width=180)

ttk.Label(text="Пароль").place(x=15, y=40)
ttk.Label(text="(от 8-и до 32-х)").place(x=65, y=40)
password_entry = ttk.Entry()
password_entry.bind("<Key>", lambda e: block_input(e, is_entry=True))
password_entry.place(x=155, y=40, width=240)
generate_button = ttk.Button(text="Генерировать", command=generate)
generate_button.place(x=400, y=38, width=90)
copy_button = ttk.Button(text="Копировать", command=copy)
copy_button.place(x=490, y=38, width=90)

ttk.Label(text="Журнал текущей сессии").place(x=10, y=80)
log_button = ttk.Button(text="Сохранить", command=save)
log_button.place(x=155, y=73, width=435)
log = Text(relief="solid", font=("TkDefaultFont"), wrap="word", width=93, height=17)
log.bind("<Key>", block_input)
log.config(state="disabled")
log.place(x=10, y=101)
log_scrollbar = ttk.Scrollbar(orient="vertical", command=log.yview)
log_scrollbar.place(x=573, y=100, height=260)
log["yscrollcommand"] = log_scrollbar.set

start_button = ttk.Button(text="ЗАПУСТИТЬ", command=run_server)
start_button.place(x=10, y=365, width=580)

load_config()
if config.getboolean("main", "show_warning", fallback=True):
    warning_window()
else:
    root.deiconify()

root.mainloop()
