import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pylibdmtx.pylibdmtx as dmtx
from PIL import Image, ImageTk, ImageEnhance
import pymupdf  # Используем pymupdf вместо fitz


def update_line_numbers():
    line_numbers.delete("1.0", tk.END)
    lines = text_input.get("1.0", tk.END).split("\n")
    for i in range(1, len(lines) + 1):
        line_numbers.insert(tk.END, f"{i}\n")


def enable_paste(event=None):
    """Разрешает вставку текста в поле ввода"""
    text_input.event_generate("<<Paste>>")


def enable_copy(event=None):
    """Разрешает копирование текста из поля ввода"""
    text_input.event_generate("<<Copy>>")


def generate_codes():
    codes = text_input.get("1.0", tk.END).strip().split("\n")
    if not codes or codes == ['']:
        messagebox.showwarning("Ошибка", "Введите хотя бы один код")
        return

    global images, current_image_index
    images = []
    for idx, code in enumerate(codes):
        if code.strip():
            img = dmtx.encode(code.encode('utf-8'))
            img = Image.frombytes('RGB', (img.width, img.height), img.pixels)
            images.append((idx + 1, code, img))

    current_image_index = 0
    display_image()


def truncate_codes():
    codes = text_input.get("1.0", tk.END).strip().split("\n")
    truncated_codes = [code[:31] for code in codes]
    text_input.delete("1.0", tk.END)
    text_input.insert("1.0", "\n".join(truncated_codes))
    update_line_numbers()


def display_image():
    for widget in images_frame.winfo_children():
        widget.destroy()

    if images:
        idx, code, img = images[current_image_index]
        img = img.resize((100, 100), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        lbl = tk.Label(images_frame, image=img_tk, bg="#DDEBF7")
        lbl.image = img_tk
        lbl.pack()
        lbl_text = tk.Label(images_frame, text=f"Строка {idx}", bg="#DDEBF7", font=("Calibri", 12))
        lbl_text.pack()


def next_image():
    global current_image_index
    if images:
        current_image_index = (current_image_index + 1) % len(images)
        display_image()


def prev_image():
    global current_image_index
    if images:
        current_image_index = (current_image_index - 1) % len(images)
        display_image()


def save_images():
    if not images:
        messagebox.showwarning("Ошибка", "Сначала сгенерируйте коды")
        return

    folder_selected = filedialog.askdirectory()
    if not folder_selected:
        return

    for idx, (line_number, code, img) in enumerate(images):
        img_path = f"{folder_selected}/datamatrix_{line_number}.png"
        img.save(img_path)

    messagebox.showinfo("Готово", "Изображения сохранены")


def clear_input():
    text_input.delete("1.0", tk.END)
    line_numbers.delete("1.0", tk.END)
    for widget in images_frame.winfo_children():
        widget.destroy()
    global images, current_image_index
    images = []
    current_image_index = 0

def preprocess_image(img):
    """Увеличение контраста и масштабирование для лучшего распознавания"""
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)  # Повышаем контраст
    img = img.convert('L')  # Переводим в черно-белый
    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)  # Увеличиваем размер
    return img

def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("Supported Files", "*.png;*.jpg;*.jpeg;*.bmp;*.pdf")])
    if not file_path:
        return

    progress_bar.start()
    root.update()

    if file_path.lower().endswith(".pdf"):
        doc = pymupdf.open(file_path)
        total_pages = len(doc)
        for i, page in enumerate(doc):
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = preprocess_image(img)
            decoded = dmtx.decode(img)
            if decoded:
                for code in decoded:
                    text_input.insert(tk.END, code.data.decode("utf-8") + "\n")
                    update_line_numbers()
            else:
                messagebox.showwarning("Ошибка", f"На странице {i + 1} не найден DataMatrix код")
            progress_bar['value'] = ((i + 1) / total_pages) * 100
            root.update()
    else:
        img = Image.open(file_path)
        decoded = dmtx.decode(img)
        if decoded:
            for code in decoded:
                text_input.insert(tk.END, code.data.decode("utf-8") + "\n")
                update_line_numbers()
        else:
            messagebox.showwarning("Ошибка", "Не удалось распознать DataMatrix код")

    progress_bar.stop()
    progress_bar['value'] = 0
    root.update()


root = tk.Tk()
root.title("Генератор DataMatrix")
root.geometry("600x550")
root.configure(bg="#DDEBF7")

text_frame = tk.Frame(root, bg="#DDEBF7")
text_frame.pack(pady=10, fill=tk.BOTH, expand=True)

line_numbers = tk.Text(text_frame, width=3, state=tk.NORMAL, wrap="none", bg="#B4C6E7", font=("Calibri", 12))
line_numbers.pack(side=tk.LEFT, fill=tk.Y)

text_input = tk.Text(text_frame, height=5, font=("Calibri", 12))
text_input.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
text_input.bind("<KeyRelease>", lambda event: update_line_numbers())
text_input.bind("<Control-v>", enable_paste)
text_input.bind("<Shift-Insert>", enable_paste)
text_input.bind("<Control-c>", enable_copy)
text_input.bind("<Control-Insert>", enable_copy)

images_frame = tk.Frame(root, bg="#DDEBF7")
images_frame.pack(pady=10)

buttons_frame = tk.Frame(root, bg="#DDEBF7")
buttons_frame.pack(pady=5)

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode='determinate')
progress_bar.pack(pady=5)

button_style = {"bg": "#A9D08E", "font": ("Calibri", 12), "relief": "flat", "bd": 5, "highlightthickness": 0}

btn_truncate = tk.Button(buttons_frame, text="Обрезать до 31 символа", command=truncate_codes, **button_style)
btn_truncate.grid(row=0, column=0, padx=5, pady=5)

btn_generate = tk.Button(buttons_frame, text="Сгенерировать", command=generate_codes, **button_style)
btn_generate.grid(row=0, column=1, padx=5, pady=5)

btn_save = tk.Button(buttons_frame, text="Сохранить", command=save_images, **button_style)
btn_save.grid(row=0, column=2, padx=5, pady=5)

btn_clear = tk.Button(buttons_frame, text="Очистить", command=clear_input, **button_style)
btn_clear.grid(row=0, column=3, padx=5, pady=5)

btn_load = tk.Button(buttons_frame, text="Загрузить файл", command=load_file, **button_style)
btn_load.grid(row=0, column=4, padx=5, pady=5)

images_frame = tk.Frame(root, bg="#DDEBF7")
images_frame.pack(pady=10)

nav_buttons_frame = tk.Frame(root, bg="#DDEBF7")
nav_buttons_frame.pack()

btn_prev = tk.Button(nav_buttons_frame, text="⬅", command=prev_image, **button_style)
btn_prev.pack(side=tk.LEFT, padx=10, pady=5)
btn_next = tk.Button(nav_buttons_frame, text="➡", command=next_image, **button_style)
btn_next.pack(side=tk.RIGHT, padx=10, pady=5)

images = []
current_image_index = 0

update_line_numbers()
root.mainloop()
