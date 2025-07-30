import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from app.utils.json_manager import JSONStore
from app.logic.search_manager import SearchManager

# --- Base Application Window ---
class FamilyTreeKioskApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Family Tree Kiosk")
        self.geometry("800x600")

        # Set up tab control
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # Add Main App and Admin tabs
        self.main_tab = MainAppTab(self.notebook)
        self.admin_tab = AdminControlsTab(self.notebook)


        self.notebook.add(self.main_tab, text="Main App")
        self.notebook.add(self.admin_tab, text="Admin Controls")


# --- Placeholder for main app tab ---
class MainAppTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        label = ttk.Label(self, text="Main Application (to be implemented)")
        label.pack(padx=10, pady=10)


# --- Admin Controls Tab with Add/Modify and Categories ---
class AdminControlsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # Add Add/Modify radio buttons at the top
        self.action_var = tk.StringVar(value="add")
        action_frame = ttk.Frame(self)
        action_frame.pack(fill='x', pady=8)

        ttk.Label(action_frame, text="Action:").pack(side='left', padx=(5, 10))
        ttk.Radiobutton(action_frame, text="Add", variable=self.action_var, value="add", command=self.update_category_panel).pack(side='left')
        ttk.Radiobutton(action_frame, text="Modify", variable=self.action_var, value="modify", command=self.update_category_panel).pack(side='left')

        # Category tabs (Person, Photo, Pet, Story, Quiz)
        self.category_notebook = ttk.Notebook(self)
        self.category_notebook.pack(expand=True, fill="both", padx=8, pady=8)

        self.category_frames = {}
        for category in ["Person", "Photo", "Pet", "Story", "Quiz"]:
            frame = AdminCategoryFrame(self.category_notebook, category, self.action_var)
            self.category_notebook.add(frame, text=category)
            self.category_frames[category] = frame

    def update_category_panel(self):
        # Notify each category frame to update its view (add/modify)
        for frame in self.category_frames.values():
            frame.update_view()


class AdminCategoryFrame(ttk.Frame):
    def __init__(self, parent, category, action_var):
        super().__init__(parent)
        self.category = category
        self.action_var = action_var

        self.form_frame = ttk.Frame(self)
        self.form_frame.pack(fill='both', expand=True, padx=12, pady=12)

        # Storage Objects
        self.store_people = JSONStore('people.json')
        self.store_photo = JSONStore('photos.json')
        self.store_pet = JSONStore('pets.json')
        self.store_story = JSONStore('stories.json')
        self.store_quiz = JSONStore('quizzes.json')

        # Search Class
        self.search_manager = SearchManager(
            people=self.store_people.get_all(),
            photos=self.store_photos.get_all(),
            pets=self.store_pets.get_all(),
            stories=self.store_stories.get_all(),
            quizzes=self.store_quizzes.get_all()
        )


        self.update_view()

    def update_view(self):
        # Clear previous form
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        action = self.action_var.get()
        if action == "add":
            self.render_add_form()
        else:
            self.render_modify_form()

    def render_add_form(self):
        if self.category == "Person":
            self.render_person_add_form()
        elif self.category == "Photo":
            self.render_photo_add_form()
        elif self.category == "Pet":
            self.render_pet_add_form()
        elif self.category == "Story":
            self.render_story_add_form()
        elif self.category == "Quiz":
            self.render_quiz_add_form()

    # ----- PERSON FORM -----
    def render_person_add_form(self):
        ttk.Label(self.form_frame, text="Add New Person", font=("Segoe UI", 14, "bold")).pack(pady=(0, 8))
        # Standard personal info
        self.person_entries = {}
        for label, key in [
            ("Full Name", "name"),
            ("Preferred/Nicknames", "nickname"),
            ("Birth Date (YYYY-MM-DD)", "birth_date"),
            ("Death Date (YYYY-MM-DD, optional)", "death_date"),
            ("Gender", "gender"),
            ("Previous Names (comma separated)", "prev_names"),
            ("Parents (comma separated)", "parents"),
            ("Spouses (comma separated)", "spouses"),
            ("Children (comma separated)", "children"),
            ("Ex-Spouses (comma separated)", "ex_spouses"),
            ("Adopted/Stepchildren (comma separated)", "nonbio_children"),
            ("Stories (comma separated story titles)", "stories"),
            ("Photo tags (comma separated)", "photo_tags"),
        ]:
            ttk.Label(self.form_frame, text=label).pack(anchor="w")
            entry = ttk.Entry(self.form_frame)
            entry.pack(fill="x", pady=(0, 5))
            self.person_entries[key] = entry

        # Living/Deceased toggle
        self.deceased_var = tk.BooleanVar()
        ttk.Checkbutton(self.form_frame, text="Deceased", variable=self.deceased_var).pack(anchor="w", pady=(2, 10))

        ttk.Button(self.form_frame, text="Add Person", command=self.on_add_person).pack(pady=8)

    def on_add_person(self):
        data = {k: e.get() for k, e in self.person_entries.items()}
        data['deceased'] = self.deceased_var.get()

        self.store_people.add(data)

        # Gather referenced people names from fields
        fields_with_people = ['parents', 'spouses', 'children', 'ex_spouses', 'nonbio_children']
        unresolved_names = []
        for field in fields_with_people:
            # Split by comma, strip whitespace, skip empty
            names = [n.strip() for n in data.get(field, '').split(',') if n.strip()]
            for name in names:
                matches = self.search_people.find_people_by_name(name)
                if not matches:
                    unresolved_names.append(name)
                elif len(matches) > 1:
                    chosen = self.prompt_resolve_multiple(name, matches)
                    if not chosen:
                        unresolved_names.append(name)
        if unresolved_names:
            self.prompt_add_missing_people(unresolved_names)


    def prompt_resolve_multiple(self, name, matches):
        """
        If there are multiple people matching a name, prompt the admin to choose.
        """
        choices = [f"{i+1}. {p['name']} ({p.get('birth_date','')})" for i, p in enumerate(matches)]
        prompt = f"Multiple matches found for '{name}':\n" + "\n".join(choices) + "\nEnter number to select or Cancel to add new."
        while True:
            choice = simpledialog.askstring("Resolve Duplicate", prompt)
            if choice is None:
                # Cancel -> treat as unresolved
                return None
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(matches):
                    return matches[idx]
            except Exception:
                pass  # loop again


    def prompt_add_missing_people(self, names):
        """
        Sequentially prompt to add any people not in the system.
        """
        for name in names:
            if messagebox.askyesno("Add Related Person", f"'{name}' is not in the system. Add them now?"):
                # Pop up quick add dialog for that name
                self.quick_add_person(name)


    def quick_add_person(self, name):
        """
        Pop up a minimal dialog to add a missing person.
        """
        win = tk.Toplevel(self)
        win.title(f"Quick Add: {name}")
        win.grab_set()
        ttk.Label(win, text=f"Quick Add: {name}").pack(padx=10, pady=10)
        entries = {}
        for label, key in [
            ("Full Name", "name"),
            ("Birth Date (YYYY-MM-DD)", "birth_date"),
            ("Gender", "gender"),
        ]:
            ttk.Label(win, text=label).pack(anchor="w")
            ent = ttk.Entry(win)
            ent.pack(fill="x", padx=6, pady=2)
            if key == "name":
                ent.insert(0, name)
            entries[key] = ent

        def save_and_close():
            person_data = {k: e.get() for k, e in entries.items()}
            self.store_people.add(person_data)
            win.destroy()

        ttk.Button(win, text="Add", command=save_and_close).pack(pady=10)
        ttk.Button(win, text="Skip", command=win.destroy).pack()

    # ----- PHOTO FORM -----
    def render_photo_add_form(self):
        ttk.Label(self.form_frame, text="Add New Photo", font=("Segoe UI", 14, "bold")).pack(pady=(0, 8))
        self.photo_entries = {}
        # File picker for photo
        ttk.Label(self.form_frame, text="Photo File").pack(anchor="w")
        file_frame = ttk.Frame(self.form_frame)
        file_frame.pack(fill="x", pady=(0, 5))
        self.photo_file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.photo_file_var)
        file_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(file_frame, text="Browse", command=self.browse_photo_file).pack(side="left", padx=4)

        for label, key in [
            ("Date Taken (YYYY-MM-DD)", "date"),
            ("People in Photo (comma separated)", "tags"),
            ("Description/Story", "desc"),
        ]:
            ttk.Label(self.form_frame, text=label).pack(anchor="w")
            entry = ttk.Entry(self.form_frame)
            entry.pack(fill="x", pady=(0, 5))
            self.photo_entries[key] = entry

        ttk.Button(self.form_frame, text="Add Photo", command=self.on_add_photo).pack(pady=8)

    def browse_photo_file(self):
        filename = filedialog.askopenfilename(title="Select Photo", filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if filename:
            self.photo_file_var.set(filename)

    def on_add_photo(self):
        data = {k: e.get() for k, e in self.photo_entries.items()}
        data['file'] = self.photo_file_var.get()

        self.store_photo.add(data)

    # ----- PET FORM -----
    def render_pet_add_form(self):
        ttk.Label(self.form_frame, text="Add New Pet", font=("Segoe UI", 14, "bold")).pack(pady=(0, 8))
        self.pet_entries = {}
        for label, key in [
            ("Pet Name", "name"),
            ("Species", "species"),
            ("Breed/Type", "breed"),
            ("Owner(s) (comma separated)", "owners"),
            ("Birth Date (optional)", "birth_date"),
            ("Notes", "notes"),
        ]:
            ttk.Label(self.form_frame, text=label).pack(anchor="w")
            entry = ttk.Entry(self.form_frame)
            entry.pack(fill="x", pady=(0, 5))
            self.pet_entries[key] = entry

        ttk.Button(self.form_frame, text="Add Pet", command=self.on_add_pet).pack(pady=8)

    def on_add_pet(self):
        data = {k: e.get() for k, e in self.pet_entries.items()}

        self.store_pet.add(data)

    # ----- STORY FORM -----
    def render_story_add_form(self):
        ttk.Label(self.form_frame, text="Add New Story", font=("Segoe UI", 14, "bold")).pack(pady=(0, 8))
        self.story_entries = {}
        for label, key in [
            ("Story Title", "title"),
            ("Who is this about? (comma separated)", "about"),
        ]:
            ttk.Label(self.form_frame, text=label).pack(anchor="w")
            entry = ttk.Entry(self.form_frame)
            entry.pack(fill="x", pady=(0, 5))
            self.story_entries[key] = entry

        ttk.Label(self.form_frame, text="Story Text").pack(anchor="w")
        self.story_text = tk.Text(self.form_frame, height=8, wrap="word")
        self.story_text.pack(fill="both", pady=(0, 10))

        ttk.Button(self.form_frame, text="Add Story", command=self.on_add_story).pack(pady=8)

    def on_add_story(self):
        data = {k: e.get() for k, e in self.story_entries.items()}
        data['text'] = self.story_text.get("1.0", "end-1c")
        
        self.store_story.add(data)

    # ----- QUIZ FORM -----
    def render_quiz_add_form(self):
        ttk.Label(self.form_frame, text="Add New Quiz Question", font=("Segoe UI", 14, "bold")).pack(pady=(0, 8))
        self.quiz_entries = {}
        for label, key in [
            ("Question", "question"),
            ("Answer", "answer"),
            ("Alt Answer (optional)", "alt_answer"),
            ("Who is this about? (optional)", "about"),
        ]:
            ttk.Label(self.form_frame, text=label).pack(anchor="w")
            entry = ttk.Entry(self.form_frame)
            entry.pack(fill="x", pady=(0, 5))
            self.quiz_entries[key] = entry

        ttk.Checkbutton(self.form_frame, text="Is this a joke/humor question?", variable=tk.BooleanVar()).pack(anchor="w", pady=(2, 10))

        ttk.Button(self.form_frame, text="Add Quiz", command=self.on_add_quiz).pack(pady=8)

    def on_add_quiz(self):
        data = {k: e.get() for k, e in self.quiz_entries.items()}
        
        self.store_quiz.add(data)
