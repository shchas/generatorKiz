import tkinter as tk
from tkinter import filedialog, messagebox
import pylibdmtx.pylibdmtx as dmtx
from PIL import Image, ImageTk


def update_line_numbers():
    line_numbers.delete("1.0", tk.END)
    lines = text_input.get("1.0", tk.END).split("\n")
    for i in range(1, len(lines) + 1):
        line_numbers.insert(tk.END, f"{i}\n")


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
        lbl = tk.Label(images_frame, image=img_tk)
        lbl.image = img_tk
        lbl.pack()
        lbl_text = tk.Label(images_frame, text=f"Строка {idx}")
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


root = tk.Tk()
root.title("Генератор DataMatrix")
root.geometry("500x500")

text_frame = tk.Frame(root)
text_frame.pack(pady=10, fill=tk.BOTH, expand=True)

line_numbers = tk.Text(text_frame, width=3, state=tk.NORMAL, wrap="none")
line_numbers.pack(side=tk.LEFT, fill=tk.Y)

text_input = tk.Text(text_frame, height=5)
text_input.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
text_input.bind("<KeyRelease>", lambda event: update_line_numbers())

buttons_frame = tk.Frame(root)
buttons_frame.pack(pady=5)

btn_truncate = tk.Button(buttons_frame, text="Обрезать до 31 символа", command=truncate_codes)
btn_truncate.grid(row=0, column=0, padx=5)

btn_generate = tk.Button(buttons_frame, text="Сгенерировать", command=generate_codes)
btn_generate.grid(row=0, column=1, padx=5)

btn_save = tk.Button(buttons_frame, text="Сохранить", command=save_images)
btn_save.grid(row=0, column=2, padx=5)

btn_clear = tk.Button(buttons_frame, text="Очистить", command=clear_input)
btn_clear.grid(row=0, column=3, padx=5)

images_frame = tk.Frame(root)
images_frame.pack(pady=10)

nav_buttons_frame = tk.Frame(root)
nav_buttons_frame.pack()

btn_prev = tk.Button(nav_buttons_frame, text="⬅", command=prev_image)
btn_prev.pack(side=tk.LEFT, padx=10)
btn_next = tk.Button(nav_buttons_frame, text="➡", command=next_image)
btn_next.pack(side=tk.RIGHT, padx=10)

images = []
current_image_index = 0

update_line_numbers()
root.mainloop()
