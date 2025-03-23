import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
import threading
import time
import csv
import pandas as pd
from tkcalendar import DateEntry


class TaskManager:
    def __init__(self, master):
        self.master = master
        self.master.title("Менеджер задач")
        self.master.geometry("1000x800")
        self.master.configure(bg="#f0f0f0")
        self.center_window()

        self.tasks = []
        self.categories = ["Без категории", "Учеба", "Домашние дела", "Работа"]
        self.load_tasks()
        self.load_categories()
        self.create_widgets()

        # Запуск потока для проверки дедлайнов
        self.notification_thread = threading.Thread(target=self.check_deadlines, daemon=True)
        self.notification_thread.start()

    def center_window(self):
        self.master.update_idletasks()
        width = self.master.winfo_width()
        height = self.master.winfo_height()
        x = (self.master.winfo_screenwidth() // 2) - (width // 2)
        y = (self.master.winfo_screenheight() // 2) - (height // 2)
        self.master.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def create_widgets(self):
        input_frame = ttk.Frame(self.master, padding="10")
        input_frame.pack(fill=tk.X)

        ttk.Label(input_frame, text="Задача:").pack(side=tk.LEFT, padx=(0, 10))
        self.task_entry = ttk.Entry(input_frame, width=30, font=("Arial", 12))
        self.task_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(input_frame, text="Описание:").pack(side=tk.LEFT, padx=(0, 10))
        self.description_entry = ttk.Entry(input_frame, width=30, font=("Arial", 12))
        self.description_entry.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(input_frame, text="Дедлайн:").pack(side=tk.LEFT, padx=(0, 10))
        self.deadline_entry = DateEntry(input_frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.deadline_entry.pack(side=tk.LEFT, padx=(0, 10))

        self.time_var = tk.StringVar()
        self.time_var.set("09:00")
        ttk.Label(input_frame, text="Время:").pack(side=tk.LEFT, padx=(0, 10))
        self.time_entry = ttk.Entry(input_frame, width=8, textvariable=self.time_var)
        self.time_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.time_entry.bind("<FocusOut>", self.validate_time)

        ttk.Label(input_frame, text="Категория:").pack(side=tk.LEFT, padx=(0, 10))
        self.category_var = tk.StringVar(value="Без категории")
        self.category_combobox = ttk.Combobox(input_frame, textvariable=self.category_var, values=self.categories)
        self.category_combobox.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(input_frame, text="Теги:").pack(side=tk.LEFT, padx=(0, 10))
        self.tags_entry = ttk.Entry(input_frame, width=20, font=("Arial", 12))
        self.tags_entry.pack(side=tk.LEFT, padx=(0, 10))

        add_button = ttk.Button(input_frame, text="Добавить задачу", command=self.add_task)
        add_button.pack(side=tk.LEFT)

        # Список задач
        self.task_list = ttk.Treeview(self.master,
                                      columns=("Задача", "Описание", "Категория", "Теги", "Статус", "Дата создания", "Дедлайн"),
                                      show="headings")
        self.task_list.heading("Задача", text="Задача")
        self.task_list.heading("Описание", text="Описание")
        self.task_list.heading("Категория", text="Категория")
        self.task_list.heading("Теги", text="Теги")
        self.task_list.heading("Статус", text="Статус")
        self.task_list.heading("Дата создания", text="Дата создания")
        self.task_list.heading("Дедлайн", text="Дедлайн")
        self.task_list.column("Задача", width=150)
        self.task_list.column("Описание", width=200)
        self.task_list.column("Категория", width=100)
        self.task_list.column("Теги", width=100)
        self.task_list.column("Статус", width=100)
        self.task_list.column("Дата создания", width=150)
        self.task_list.column("Дедлайн", width=150)
        self.task_list.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Кнопки управления
        button_frame = ttk.Frame(self.master, padding="10")
        button_frame.pack(fill=tk.X)

        complete_button = ttk.Button(button_frame, text="Отметить как выполненное", command=self.mark_complete)
        complete_button.pack(side=tk.LEFT, padx=(0, 10))

        delete_button = ttk.Button(button_frame, text="Удалить задачу", command=self.delete_task)
        delete_button.pack(side=tk.LEFT, padx=(0, 10))

        edit_button = ttk.Button(button_frame, text="Редактировать задачу", command=self.edit_task)
        edit_button.pack(side=tk.LEFT, padx=(0, 10))

        edit_categories_button = ttk.Button(button_frame, text="Редактировать категории", command=self.edit_categories)
        edit_categories_button.pack(side=tk.LEFT, padx=(0, 10))

        delete_all_button = ttk.Button(button_frame, text="Удалить все задачи", command=self.delete_all_tasks)
        delete_all_button.pack(side=tk.LEFT)

        # Экспорт задач
        export_frame = ttk.Frame(self.master, padding="10")
        export_frame.pack(fill=tk.X)

        export_csv_button = ttk.Button(export_frame, text="Экспорт в CSV", command=self.export_to_csv)
        export_csv_button.pack(side=tk.LEFT, padx=(0, 10))

        export_excel_button = ttk.Button(export_frame, text="Экспорт в Excel", command=self.export_to_excel)
        export_excel_button.pack(side=tk.LEFT)

        # Фильтрация по тегам
        filter_frame = ttk.Frame(self.master, padding="10")
        filter_frame.pack(fill=tk.X)

        ttk.Label(filter_frame, text="Фильтр по тегам:").pack(side=tk.LEFT, padx=(0, 10))
        self.filter_tag_entry = ttk.Entry(filter_frame, width=20, font=("Arial", 12))
        self.filter_tag_entry.pack(side=tk.LEFT, padx=(0, 10))
        filter_button = ttk.Button(filter_frame, text="Применить фильтр", command=self.filter_by_tag)
        filter_button.pack(side=tk.LEFT)

        self.apply_style()
        self.update_task_list()

    def apply_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#333333")
        style.map("Treeview", background=[("selected", "#4a6984")])

        style.configure("TButton", padding=6, relief="flat", background="#4a6984", foreground="white")
        style.map("TButton", background=[("active", "#5a7994")])

        style.configure("TEntry", padding=6, relief="flat")

    def validate_time(self, event):
        time_str = self.time_var.get()
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите время в формате ЧЧ:ММ")
            self.time_var.set("09:00")

    def add_task(self):
        task = self.task_entry.get().strip()
        description = self.description_entry.get().strip()
        tags = self.tags_entry.get().strip()
        deadline_date = self.deadline_entry.get_date()
        deadline_time = self.time_var.get()
        category = self.category_var.get()
        if task:
            deadline = f"{deadline_date.strftime('%Y-%m-%d')} {deadline_time}"
            self.tasks.append({
                "task": task,
                "description": description,
                "tags": tags,
                "category": category,
                "status": "В процессе",
                "date_created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "deadline": deadline
            })
            self.update_task_list()
            self.task_entry.delete(0, tk.END)
            self.description_entry.delete(0, tk.END)
            self.tags_entry.delete(0, tk.END)
            self.time_var.set("09:00")
            self.category_var.set("Без категории")
            self.save_tasks()
        else:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите задачу.")

    def mark_complete(self):
        selected_item = self.task_list.selection()
        if selected_item:
            index = self.task_list.index(selected_item)
            self.tasks[index]["status"] = "Выполнено"
            self.update_task_list()
            self.save_tasks()
        else:
            messagebox.showinfo("Информация", "Пожалуйста, выберите задачу для отметки.")

    def delete_task(self):
        selected_item = self.task_list.selection()
        if selected_item:
            index = self.task_list.index(selected_item)
            del self.tasks[index]
            self.update_task_list()
            self.save_tasks()
        else:
            messagebox.showinfo("Информация", "Пожалуйста, выберите задачу для удаления.")

    def delete_all_tasks(self):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить все задачи? Это действие нельзя отменить."):
            self.tasks = []
            self.update_task_list()
            self.save_tasks()
            messagebox.showinfo("Информация", "Все задачи были удалены.")

    def edit_task(self):
        selected_item = self.task_list.selection()
        if selected_item:
            index = self.task_list.index(selected_item)
            task = self.tasks[index]

            edit_window = tk.Toplevel(self.master)
            edit_window.title("Редактировать задачу")
            edit_window.geometry("400x400")
            self.center_toplevel(edit_window)

            ttk.Label(edit_window, text="Задача:").pack(pady=(10, 0))
            task_entry = ttk.Entry(edit_window, width=40)
            task_entry.insert(0, task["task"])
            task_entry.pack(pady=(0, 10))

            ttk.Label(edit_window, text="Описание:").pack()
            description_entry = ttk.Entry(edit_window, width=40)
            description_entry.insert(0, task["description"])
            description_entry.pack(pady=(0, 10))

            ttk.Label(edit_window, text="Теги:").pack()
            tags_entry = ttk.Entry(edit_window, width=40)
            tags_entry.insert(0, task["tags"])
            tags_entry.pack(pady=(0, 10))

            ttk.Label(edit_window, text="Категория:").pack()
            category_var = tk.StringVar(value=task["category"])
            category_combobox = ttk.Combobox(edit_window, textvariable=category_var, values=self.categories)
            category_combobox.pack(pady=(0, 10))

            ttk.Label(edit_window, text="Статус:").pack()
            status_var = tk.StringVar(value=task["status"])
            status_combobox = ttk.Combobox(edit_window, textvariable=status_var, values=["В процессе", "Выполнено"])
            status_combobox.pack(pady=(0, 10))

            ttk.Label(edit_window, text="Дедлайн:").pack()
            deadline_frame = ttk.Frame(edit_window)
            deadline_frame.pack(pady=(0, 10))

            deadline_date = datetime.strptime(task["deadline"].split()[0], "%Y-%m-%d").date()
            deadline_entry = DateEntry(deadline_frame, width=12, background='darkblue', foreground='white',
                                       borderwidth=2)
            deadline_entry.set_date(deadline_date)
            deadline_entry.pack(side=tk.LEFT, padx=(0, 10))

            time_var = tk.StringVar(value=task["deadline"].split()[1])
            time_entry = ttk.Entry(deadline_frame, width=8, textvariable=time_var)
            time_entry.pack(side=tk.LEFT)
            time_entry.bind("<FocusOut>", lambda event: self.validate_edit_time(event, time_var))

            def save_changes():
                if self.validate_edit_time(None, time_var):
                    task["task"] = task_entry.get().strip()
                    task["description"] = description_entry.get().strip()
                    task["tags"] = tags_entry.get().strip()
                    task["category"] = category_var.get()
                    task["status"] = status_var.get()
                    new_deadline = f"{deadline_entry.get_date().strftime('%Y-%m-%d')} {time_var.get()}"
                    task["deadline"] = new_deadline
                    self.update_task_list()
                    self.save_tasks()
                    edit_window.destroy()

            save_button = ttk.Button(edit_window, text="Сохранить изменения", command=save_changes)
            save_button.pack(pady=10)
        else:
            messagebox.showinfo("Информация", "Пожалуйста, выберите задачу для редактирования.")

    def validate_edit_time(self, event, time_var):
        time_str = time_var.get()
        try:
            datetime.strptime(time_str, "%H:%M")
            return True
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите время в формате ЧЧ:ММ")
            time_var.set("09:00")
            return False

    def update_task_list(self, tasks=None):
        tasks = tasks or self.tasks
        self.task_list.delete(*self.task_list.get_children())
        today = datetime.now()
        for task in tasks:
            deadline_str = task["deadline"]
            if ' ' not in deadline_str:
                deadline_str += ' 09:00'
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M")
            except ValueError:
                deadline = datetime.strptime(deadline_str.split()[0], "%Y-%m-%d")

            values = (task["task"], task["description"], task["category"], task["tags"], task["status"], task["date_created"], task["deadline"])
            if task["status"] == "Выполнено":
                self.task_list.insert("", tk.END, values=values, tags=("completed",))
            elif deadline < today and task["status"] != "Выполнено":
                self.task_list.insert("", tk.END, values=values, tags=("overdue",))
            else:
                self.task_list.insert("", tk.END, values=values)

        self.task_list.tag_configure("overdue", background="#ffcccc")
        self.task_list.tag_configure("completed", background="#ccffcc")

    def save_tasks(self):
        with open("tasks.json", "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

    def load_tasks(self):
        try:
            with open("tasks.json", "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    self.tasks = json.loads(content)
                else:
                    self.tasks = []
        except FileNotFoundError:
            self.tasks = []
        except json.JSONDecodeError:
            messagebox.showerror("Ошибка",
                                 "Файл tasks.json содержит некорректные данные. Начинаем с пустого списка задач.")
            self.tasks = []

    def edit_categories(self):
        categories_window = tk.Toplevel(self.master)
        categories_window.title("Редактировать категории")
        categories_window.geometry("300x300")
        self.center_toplevel(categories_window)

        categories_listbox = tk.Listbox(categories_window)
        categories_listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        for category in self.categories:
            categories_listbox.insert(tk.END, category)

        add_frame = ttk.Frame(categories_window)
        add_frame.pack(fill=tk.X, padx=10, pady=5)

        new_category_entry = ttk.Entry(add_frame)
        new_category_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        add_button = ttk.Button(add_frame, text="Добавить",
                                command=lambda: self.add_category(new_category_entry, categories_listbox))
        add_button.pack(side=tk.RIGHT)

        delete_button = ttk.Button(categories_window, text="Удалить выбранную категорию",
                                   command=lambda: self.delete_category(categories_listbox))
        delete_button.pack(pady=5)

    def add_category(self, entry, listbox):
        new_category = entry.get().strip()
        if new_category and new_category not in self.categories:
            self.categories.append(new_category)
            listbox.insert(tk.END, new_category)
            entry.delete(0, tk.END)
            self.category_combobox['values'] = self.categories
            self.save_categories()

    def delete_category(self, listbox):
        selected = listbox.curselection()
        if selected:
            category = listbox.get(selected)
            if category != "Без категории":
                self.categories.remove(category)
                listbox.delete(selected)
                self.category_combobox['values'] = self.categories
                self.save_categories()
            else:
                messagebox.showwarning("Предупреждение", "Категорию 'Без категории' нельзя удалить.")

    def save_categories(self):
        with open("categories.json", "w", encoding="utf-8") as f:
            json.dump(self.categories, f, ensure_ascii=False, indent=2)

    def load_categories(self):
        try:
            with open("categories.json", "r", encoding="utf-8") as f:
                self.categories = json.load(f)
            if "Без категории" not in self.categories:
                self.categories.insert(0, "Без категории")
        except FileNotFoundError:
            self.categories = ["Без категории", "Учеба", "Домашние дела", "Работа"]
            self.save_categories()

    def sort_tasks(self, event):
        sort_by = self.sort_var.get()
        if sort_by == "Категории":
            self.tasks.sort(key=lambda x: x["category"])
        elif sort_by == "Дате создания":
            self.tasks.sort(key=lambda x: x["date_created"])
        elif sort_by == "Дедлайну":
            self.tasks.sort(key=lambda x: x["deadline"])
        elif sort_by == "Статусу":
            self.tasks.sort(key=lambda x: x["status"])
        self.update_task_list()

    def center_toplevel(self, toplevel):
        toplevel.update_idletasks()
        width = toplevel.winfo_width()
        height = toplevel.winfo_height()
        x = (toplevel.winfo_screenwidth() // 2) - (width // 2)
        y = (toplevel.winfo_screenheight() // 2) - (height // 2)
        toplevel.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def check_deadlines(self):
        while True:
            time.sleep(60)  # Проверка каждую минуту
            now = datetime.now()
            for task in self.tasks:
                deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")
                if (deadline - now).total_seconds() <= 3600:  # Уведомление за час до дедлайна
                    messagebox.showwarning("Скоро дедлайн", f"Задача '{task['task']}' скоро истекает!")

    def filter_by_tag(self):
        tag = self.filter_tag_entry.get().strip()
        if tag:
            filtered_tasks = [task for task in self.tasks if tag in task.get("tags", "")]
            self.update_task_list(filtered_tasks)
        else:
            self.update_task_list(self.tasks)

    def export_to_csv(self):
        with open("tasks.csv", "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["Задача", "Описание", "Категория", "Теги", "Статус", "Дата создания", "Дедлайн"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for task in self.tasks:
                writer.writerow({
                    "Задача": task["task"],
                    "Описание": task["description"],
                    "Категория": task["category"],
                    "Теги": task["tags"],
                    "Статус": task["status"],
                    "Дата создания": task["date_created"],
                    "Дедлайн": task["deadline"]
                })

    def export_to_excel(self):
        df = pd.DataFrame(self.tasks)
        df.to_excel("tasks.xlsx", index=False)


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManager(root)
    root.mainloop()
