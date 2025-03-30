import tkinter as tk
from tkinter import font, Menu, messagebox, Scrollbar, simpledialog
import os
import shutil
import time
import sqlite3
from datetime import datetime, timedelta
import threading

# =============================================
# CONFIGURATION INITIALE ET BASE DE DONNÉES
# =============================================

# Initialisation de la fenêtre principale
root = tk.Tk()
root.title("Gestionnaire de fichiers")
root.geometry("1100x700")
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

# Configuration de la base de données
conn = sqlite3.connect("explorer.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        path TEXT PRIMARY KEY NOT NULL,
        filename TEXT NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS recents (
        path TEXT PRIMARY KEY NOT NULL,
        filename TEXT NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.commit()
conn.close()

# =============================================
# VARIABLES GLOBALES
# =============================================

main_path = os.getcwd()
root_directory = os.path.splitdrive(os.path.abspath(__file__))[0] + "\\"
previous_path = None
clipboard_action = None
clipboard_path = None
section = None
status_var = None
status_frame = None
filter_var = tk.StringVar(value="Tous les fichiers")

# Configuration de la police
font_path = "otfs/Font Awesome 6 Free-Solid-900.ttf"
if "FA" not in font.names():
    custom_font1 = font.Font(family="FontAwesomeSolid", name="FA", size=10)
else:
    custom_font1 = font.nametofont("FA")

# Définition des filtres de fichiers
file_filters = {
    "Tous les fichiers": None,
    "Images (.png, .jpg, .jpeg, .gif)": [".png", ".jpg", ".jpeg", ".gif"],
    "Documents (.txt, .pdf, .docx)": [".txt", ".pdf", ".docx"],
    "Développement (.html, .css, .js, .py, .php)": [".html", ".css", ".js", ".py", ".php"]
}

# =============================================
# FONCTIONS DE NAVIGATION
# =============================================

def go_back():
    global main_path, previous_path
    if main_path != root_directory:
        previous_path = main_path
        parent_dir = os.path.dirname(main_path)
        load_directory(parent_dir)

def go_ahead():
    global main_path, previous_path
    if previous_path:
        load_directory(previous_path)
        previous_path = None

def refresh_directory():
    file_list.selection_clear(0, tk.END)
    global filter_var
    filter_var = None
    load_directory(main_path)

# =============================================
# FONCTIONS D'AFFICHAGE
# =============================================

def load_directory(path):
    global main_path
    main_path = path
    update_path_display()
    file_list.delete(0, tk.END)
    
    try:
        items = os.listdir(path)
        folders = sorted([item for item in items if os.path.isdir(os.path.join(path, item))])
        files = sorted([item for item in items if os.path.isfile(os.path.join(path, item))])
        for folder_name in folders:
            file_list.insert(tk.END, f"\uf07b {folder_name}")
        for file_name in files:
            file_list.insert(tk.END, f"\uf15b {file_name}")
    except PermissionError:
        file_list.insert(tk.END, "[Accès Refusé]")
        messagebox.showerror("Emplacement non disponible", f"{path} n'est pas accessible. \n Accès refusé")
        go_back()
    except Exception as e:
        messagebox.showerror("Erreur", f"{e}")
        go_back()
    update_status_bar()

def update_path_display():
    for widget in path_entry_frame.winfo_children():
        widget.destroy()

    parts = main_path.split(os.sep)

    for i, part in enumerate(parts):
        if not part:
            continue
        current_path = os.path.abspath(os.path.join(root_directory, *parts[:i+1]))
        btn = tk.Button(path_entry_frame, text=part, relief="flat", fg="blue",
                        cursor="hand2", command=lambda p=current_path: load_directory(p))
        btn.pack(side="left", padx=2)

        if i < len(parts) - 1:
            separator = tk.Label(path_entry_frame, text=">", fg="gray")
            separator.pack(side="left")

def switch_to_entry(event=None):
    for widget in path_entry_frame.winfo_children():
        widget.destroy()

    entry = tk.Entry(path_entry_frame)
    entry.pack(fill="both", expand=True)
    entry.insert(0, main_path)
    entry.focus()
    entry.bind("<Return>", lambda e: load_directory(entry.get()))
    entry.bind("<FocusOut>", lambda e: update_path_display())

# =============================================
# FONCTIONS DE FILTRAGE ET RECHERCHE
# =============================================

def show_filter_menu(event):
    filter_menu.post(event.x_root, event.y_root)

def apply_filter(filter_type):
    file_list.delete(0, tk.END)
    selected_filter = file_filters[filter_type]

    for item in os.listdir(main_path):
        item_path = os.path.join(main_path, item)

        if selected_filter is not None:
            if os.path.isfile(item_path) and any(item.lower().endswith(ext) for ext in selected_filter):
                file_list.insert(tk.END, f"\uf15b {item}")
        else:
            icon = "\uf07b" if os.path.isdir(item_path) else "\uf15b"
            file_list.insert(tk.END, f"{icon} {item}")

    filter_var.set(filter_type)

def update_search(event):
    query = search_entry.get().lower()
    file_list.delete(0, tk.END)
    items = os.listdir(main_path)
    for item in items:
        if query in item.lower():
            icon = "\uf07b" if os.path.isdir(os.path.join(main_path, item)) else "\uf15b"
            file_list.insert(tk.END, f"{icon} {item}")

# =============================================
# FONCTIONS POUR LES FAVORIS ET RÉCENTS
# =============================================

def is_favorite(path):
    conn = sqlite3.connect("explorer.db")
    cursor = conn.cursor()
    cursor.execute("SELECT path FROM favorites WHERE path = ?", (path,))
    verif = cursor.fetchone()
    conn.close()
    return bool(verif)

def add_to_favorites(path):
    conn = sqlite3.connect("explorer.db")
    cursor = conn.cursor()
    
    if not is_favorite(path):
        cursor.execute("INSERT INTO favorites (path, filename) VALUES (?, ?)", (path, os.path.basename(path)))
        messagebox.showinfo("Opération reussie", f"{os.path.basename(path)} a été ajouté aux favoris avec succes")
    else:
        messagebox.showinfo("Notification", f"L'élément {os.path.basename(path)} est déja présent dans les favoris")
    
    conn.commit()
    conn.close()

def add_to_recents(path):
    conn = sqlite3.connect("explorer.db")
    cursor = conn.cursor()
    if os.path.isfile(path):
        cursor.execute("SELECT path FROM recents WHERE path = ?", (path,))
        verif = cursor.fetchone()
        
        if not verif:
            cursor.execute("INSERT INTO recents (path, filename) VALUES (?, ?)", (path, os.path.basename(path)))
        else:
            cursor.execute("UPDATE recents SET added_at = CURRENT_TIMESTAMP WHERE path = ?", (path,))
        
        conn.commit()
    conn.close()

def clean_recents():
    conn = sqlite3.connect("explorer.db")
    cursor = conn.cursor()
    period = datetime.now() - timedelta(days=1)
    cursor.execute("DELETE FROM recents WHERE added_at < ?", (period,))
    conn.commit()
    conn.close()

def delete_favorites(path):
    conn = sqlite3.connect("explorer.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE path = ?", (path,))
    messagebox.showinfo("Opération terminée", "Elément retiré avec succes")
    conn.commit()
    conn.close()

def delete_recents(path):
    conn = sqlite3.connect("explorer.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recents WHERE path = ?", (path,))
    messagebox.showinfo("Opération terminée", "Elément retiré avec succes")
    conn.commit()
    conn.close()

def show_favorites():
    file_list.delete(0, tk.END)
    conn = sqlite3.connect("explorer.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM favorites")
    favorites = cursor.fetchall()
    
    if favorites:
        for favorite in favorites:
            if os.path.exists(favorite[0]):  # Vérifier si le fichier/dossier existe
                file_name = favorite[1]
                icon = "\uf07b" if os.path.isdir(favorite[0]) else "\uf15b"
                file_list.insert(tk.END, f"{icon} {file_name}")
            else:
                # Supprimer de la base si n'existe plus
                cursor.execute("DELETE FROM favorites WHERE path = ?", (favorite[0],))
        conn.commit()
    else:
        file_list.insert(tk.END, "Aucun favori trouvé.")
    conn.close()

def show_recents():
    file_list.delete(0, tk.END)
    conn = sqlite3.connect("explorer.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recents ORDER BY added_at DESC")
    recents = cursor.fetchall()
    
    if recents:
        for recent in recents:
            if os.path.exists(recent[0]):  # Vérifier si le fichier/dossier existe
                file_name = recent[1]
                icon = "\uf07b" if os.path.isdir(recent[0]) else "\uf15b"
                file_list.insert(tk.END, f"{icon} {file_name}")
            else:
                # Supprimer de la base si n'existe plus
                cursor.execute("DELETE FROM recents WHERE path = ?", (recent[0],))
        conn.commit()
    else:
        file_list.insert(tk.END, "Aucun élément récent.")
    conn.close()

def on_menu_item_select(event):
    global section
    selection = menu_list.curselection()
    if not selection:
        return
    selected_section = menu_list.get(selection)
    section = selected_section
    if selected_section == "Favorites":
        show_favorites()
    elif selected_section == "Recents":
        show_recents()
    elif selected_section == "computer":
        load_directory(root_directory)

# =============================================
# FONCTIONS DE GESTION DES ÉVÉNEMENTS
# =============================================

def item_select(event=None):
    global section, main_path
    
    if not file_list.curselection():  # Si aucun élément n'est sélectionné
        return
        
    try:
        selected_index = file_list.curselection()[0]
        selected = file_list.get(selected_index)[2:].strip()
        
        if section == "Favorites":
            conn = sqlite3.connect("explorer.db")
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM favorites WHERE filename = ?", (selected,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return
                
            selected_path = result[0]
            
            if os.path.isdir(selected_path):
                # Pour les dossiers favoris: naviguer dedans
                main_path = selected_path  # Mettre à jour le chemin principal
                load_directory(selected_path)
                section = None  # Quitter le mode favoris pour naviguer normalement
            else:
                # Pour les fichiers favoris: les ouvrir
                os.startfile(selected_path)
                add_to_recents(selected_path)
                
        elif section == "Recents":
            conn = sqlite3.connect("explorer.db")
            cursor = conn.cursor()
            cursor.execute("SELECT path FROM recents WHERE filename = ?", (selected,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                selected_path = result[0]
                if os.path.isdir(selected_path):
                    main_path = selected_path
                    load_directory(selected_path)
                    section = None  # Quitter le mode recents
                else:
                    os.startfile(selected_path)
                    add_to_recents(selected_path)
                    
        else:  # Mode navigation normale
            selected_path = os.path.join(main_path, selected)
            if os.path.isdir(selected_path):
                load_directory(selected_path)
                add_to_recents(selected_path)
            else:
                os.startfile(selected_path)
                add_to_recents(selected_path)
                
    except Exception as e:
        print(f"Erreur dans item_select: {e}")

def get_selected_paths():
    selected_paths = []
    for index in file_list.curselection():
        item = file_list.get(index)[2:].strip()
        selected_paths.append(os.path.join(main_path, item))
    return selected_paths

def show_item_menu(event):
    try:
        selected_indices = file_list.curselection()
        if not selected_indices:
            return
            
        context_menu = Menu(root, tearoff=0)
        
        if len(selected_indices) == 1:
            index = selected_indices[0]
            selected_item = file_list.get(index)[2:].strip()
            selected_path = os.path.join(main_path, selected_item)
            
            context_menu.add_command(label="Ouvrir", command=lambda: open_item(selected_path))
            context_menu.add_command(label="Renommer", command=lambda: rename_item(selected_path))
            context_menu.add_separator()
            
            if not is_favorite(selected_path):
                context_menu.add_command(label="Ajouter aux favoris", command=lambda: add_to_favorites(selected_path))
            else:
                context_menu.add_command(label="Retirer des favoris", command=lambda: delete_favorites(selected_path))
        else:
            context_menu.add_command(label="Ouvrir", state="disabled")
            context_menu.add_command(label="Renommer", state="disabled")
            context_menu.add_separator()
            context_menu.add_command(label="Ajouter aux favoris", state="disabled")
        
        context_menu.add_command(label="Copier", command=copy_selected_items)
        context_menu.add_command(label="Couper", command=cut_selected_items)
        context_menu.add_command(label="Supprimer", command=delete_selected_items)
        context_menu.add_separator()
        
        if len(selected_indices) == 1:
            context_menu.add_command(label="Propriétés", command=lambda: show_properties(os.path.join(main_path, file_list.get(selected_indices[0])[2:].strip())))
        else:
            context_menu.add_command(label="Propriétés", command=show_selected_properties)
        
        context_menu.tk_popup(event.x_root, event.y_root)
    except Exception as e:
        print(f"Erreur menu contextuel: {e}")

def show_space_menu(event):
    empty_menu = Menu(root, tearoff=0)
    new_menu = Menu(empty_menu, tearoff=0)
    new_menu.add_command(label="Dossier", command=lambda: create_new("folder"))
    new_menu.add_command(label="Fichier .txt", command=lambda: create_new("txt"))
    new_menu.add_command(label="Fichier .html", command=lambda: create_new("html"))
    new_menu.add_command(label="Fichier .js", command=lambda: create_new("js"))
    new_menu.add_command(label="Fichier .php", command=lambda: create_new("php"))
    new_menu.add_command(label="Autre fichier", command=lambda: create_new("custom"))
    empty_menu.add_cascade(label="Nouveau", menu=new_menu)

    if clipboard_path:
        empty_menu.add_command(label="Coller", command=paste_item)
    else:
        empty_menu.add_command(label="Coller", state="disabled")

    empty_menu.post(event.x_root, event.y_root)

def right_click(event):
    index = file_list.nearest(event.y)
    bbox = file_list.bbox(index)
    ctrl_pressed = event.state & 0x0004
    shift_pressed = event.state & 0x0001
    current_selection = file_list.curselection()
    
    if bbox:
        x_min, y_min, width, height = bbox
        if (y_min <= event.y < y_min + height and 
            x_min <= event.x < x_min + width):
            if not (ctrl_pressed or shift_pressed) and index not in current_selection:
                file_list.selection_clear(0, tk.END)
                file_list.selection_set(index)
            show_item_menu(event)
        else:
            file_list.selection_clear(0, tk.END)
            show_space_menu(event)
    else:
        file_list.selection_clear(0, tk.END)
        show_space_menu(event)

# =============================================
# FONCTIONS DE GESTION DES FICHIERS
# =============================================

def select_all_files(event=None):
    file_list.selection_set(0, tk.END)
    update_status_bar()
    return "break"

def copy_selected_items():
    global clipboard_path, clipboard_action
    selected_paths = get_selected_paths()
    if selected_paths:
        clipboard_path = selected_paths
        clipboard_action = "copy"

def cut_selected_items():
    global clipboard_path, clipboard_action
    selected_paths = get_selected_paths()
    if selected_paths:
        clipboard_path = selected_paths
        clipboard_action = "cut"

def delete_selected_items():
    selected_paths = get_selected_paths()
    if not selected_paths or not messagebox.askyesno("Confirmation", 
           f"Voulez-vous vraiment supprimer ces {len(selected_paths)} éléments ?"):
        return
    
    progress_top, progress_var = show_progress_window(root, "Suppression")
    success_count = 0
    
    try:
        conn = sqlite3.connect("explorer.db")
        cursor = conn.cursor()
        
        for i, path in enumerate(selected_paths):
            progress_var.set(f"Suppression de {os.path.basename(path)}...")
            progress_top.update()
            
            try:
                # Supprimer de la base de données si présent
                cursor.execute("DELETE FROM favorites WHERE path = ?", (path,))
                cursor.execute("DELETE FROM recents WHERE path = ?", (path,))
                conn.commit()
                
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                success_count += 1
            except Exception as e:
                print(f"Erreur suppression {path}: {e}")
                
        msg = f"Terminé ! {success_count}/{len(selected_paths)} éléments supprimés"
        update_progress(progress_top, progress_var, msg, success_count>0)
        
    except Exception as e:
        update_progress(progress_top, progress_var, f"Échec : {str(e)}", False)
    finally:
        conn.close()
        load_directory(main_path)

def show_selected_properties():
    selected_paths = get_selected_paths()
    if not selected_paths:
        return
        
    if len(selected_paths) == 1:
        show_properties(selected_paths[0])
    else:
        total_size = 0
        file_count = 0
        dir_count = 0
        
        for path in selected_paths:
            if os.path.isfile(path):
                total_size += os.path.getsize(path)
                file_count += 1
            elif os.path.isdir(path):
                dir_count += 1
        
        prop_window = tk.Toplevel(root)
        prop_window.geometry("300x200")
        prop_window.title("Propriétés des éléments sélectionnés")
        
        tk.Label(prop_window, text=f"Éléments sélectionnés: {len(selected_paths)}").pack(pady=5)
        tk.Label(prop_window, text=f"Fichiers: {file_count}").pack(pady=2)
        tk.Label(prop_window, text=f"Dossiers: {dir_count}").pack(pady=2)
        
        if total_size < 1024:
            size_text = f"{total_size} octets"
        elif total_size < 1024*1024:
            size_text = f"{total_size/1024:.2f} Ko"
        else:
            size_text = f"{total_size/(1024*1024):.2f} Mo"
        
        tk.Label(prop_window, text=f"Taille totale: {size_text}").pack(pady=5)
        tk.Button(prop_window, text="OK", width=10, command=prop_window.destroy).pack(pady=10)

def update_status_bar(event=None):
    try:
        file_list.unbind("<<ListboxSelect>>")
        
        try:
            items = os.listdir(main_path)
            total_items = len(items)
        except:
            total_items = 0
        
        selected_count = len(file_list.curselection())
        
        if selected_count > 0:
            total_size = 0
            for index in file_list.curselection():
                try:
                    item = file_list.get(index)[2:].strip()
                    item_path = os.path.join(main_path, item)
                    if os.path.isfile(item_path):
                        total_size += os.path.getsize(item_path)
                except:
                    continue
            
            if total_size == 0:
                size_text = "-"
            elif total_size < 1024:
                size_text = f"{total_size} octets"
            elif total_size < 1024*1024:
                size_text = f"{total_size/1024:.2f} Ko"
            else:
                size_text = f"{total_size/(1024*1024):.2f} Mo"
            
            status_text = f"Total: {total_items} éléments | {selected_count} sélectionné(s) | Taille fichiers: {size_text}"
        else:
            status_text = f"Total: {total_items} éléments"
        
        status_var.set(status_text)
        
    except Exception as e:
        status_var.set("Statut: erreur")
        print(f"Erreur barre statut: {e}")
        
    finally:
        file_list.bind("<<ListboxSelect>>", update_status_bar)

def create_new(item_type):
    name = simpledialog.askstring("Nouveau", "Nom du fichier/dossier :")
    if not name:
        return
    
    if replace_item(name, main_path):
        try:
            if item_type == "folder":
                os.makedirs(os.path.join(main_path, name), exist_ok=True)
            elif item_type == "txt":
                open(os.path.join(main_path, name + ".txt"), "w").close()
            elif item_type == "html":
                open(os.path.join(main_path, name + ".html"), "w").close()
            elif item_type == "js":
                open(os.path.join(main_path, name + ".js"), "w").close()
            elif item_type == "php":
                open(os.path.join(main_path, name + ".php"), "w").close()
            else:
                extension = simpledialog.askstring("Extension", "Entrez l'extension du fichier (ex: .txt, .html, .py) :")
                if extension:
                    if not extension.startswith("."):
                        extension = "." + extension
                    open(os.path.join(main_path, name + extension), "w").close()
                else:
                    messagebox.showinfo("Info", "Aucune extension fournie.")
        
            load_directory(main_path)
        except PermissionError:
            messagebox.showerror("Erreur", "Vous n'avez pas l'autorisation de créer cet élément ici.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")

def replace_item(name, destination_path):
    item_path = os.path.join(destination_path, name)
    if os.path.exists(item_path):
        response = messagebox.askyesno("Confirmation", f"L'élément '{name}' existe déjà. Voulez-vous le remplacer ?")
        if not response:
            return False
    return True

def open_item(selected_path):
    if os.path.isdir(selected_path):
        load_directory(selected_path)
    else:
        os.startfile(selected_path)

def rename_item(selected_path):
    main_path, old_name = os.path.split(selected_path)
    extension = os.path.splitext(old_name)[1]

    new_name = simpledialog.askstring("Renommer", "Nouveau nom :", initialvalue=os.path.splitext(old_name)[0])

    if new_name:
        if extension:
            new_name += extension
        new_path = os.path.join(main_path, new_name)

        try:
            os.rename(selected_path, new_path)
            load_directory(main_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de renommer : {e}")

def paste_item():
    global clipboard_path, clipboard_action, main_path
    
    if not clipboard_path:
        return
        
    operation = "Copie" if clipboard_action == "copy" else "Déplacement"
    progress_top, progress_var = show_progress_window(root, operation)
    
    try:
        success_count = 0
        total = len(clipboard_path)
        
        for i, path in enumerate(clipboard_path):
            if not os.path.exists(path):
                continue
                
            name = os.path.basename(path)
            dest_path = os.path.join(main_path, name)
            
            # Mise à jour progression
            progress_var.set(f"{operation} de {name} ({i+1}/{total})...")
            progress_top.update()
            
            try:
                if clipboard_action == "copy":
                    if os.path.isdir(path):
                        shutil.copytree(path, dest_path)
                    else:
                        shutil.copy2(path, dest_path)
                else:  # cut
                    shutil.move(path, dest_path)
                    
                success_count += 1
            except Exception as e:
                print(f"Erreur {operation.lower()} {path}: {e}")
                
        # Résultat final
        msg = f"Terminé ! {success_count}/{total} éléments {operation.lower()}s avec succès"
        update_progress(progress_top, progress_var, msg, success_count>0)
        
    except Exception as e:
        update_progress(progress_top, progress_var, f"Échec : {str(e)}", False)
    finally:
        clipboard_path = None
        load_directory(main_path)  # Rafraîchir l'affichage



def get_folder_size(path, progress_queue=None, cancel_event=None):
    """Calcule récursivement la taille d'un dossier (avec gestion d'annulation)"""
    total_size = 0
    if cancel_event and cancel_event.is_set():
        return 0
        
    try:
        for entry in os.scandir(path):
            if cancel_event and cancel_event.is_set():
                return 0
                
            if entry.is_file():
                total_size += entry.stat().st_size
            elif entry.is_dir():
                total_size += get_folder_size(entry.path, progress_queue, cancel_event)
                
            if progress_queue:
                progress_queue.put(total_size)
    except PermissionError:
        pass
        
    return total_size

def format_size(size_bytes):
    """Convertit les octets en unités lisible (Ko, Mo, Go)"""
    if size_bytes < 1024:
        return f"{size_bytes} octets"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.2f} Ko"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.2f} Mo"
    else:
        return f"{size_bytes/(1024**3):.2f} Go"


def show_properties(selected_path):
    """Affiche une fenêtre de propriétés avec calcul asynchrone simplifié"""
    if not os.path.exists(selected_path):
        return

    # Création de la fenêtre
    prop_window = tk.Toplevel(root)
    prop_window.title("Propriétés")
    prop_window.geometry("350x200")
    
    # Variables de contrôle
    cancel_event = threading.Event()
    calculation_done = False

    # Widgets
    tk.Label(prop_window, text=f"Nom : {os.path.basename(selected_path)}").pack(pady=5)
    file_type = "Dossier" if os.path.isdir(selected_path) else "Fichier"
    tk.Label(prop_window, text=f"Type : {file_type}").pack(pady=5)
    
    size_label = tk.Label(prop_window, text="Taille : Calcul...")
    size_label.pack(pady=5)
    
    mod_time = time.strftime('%d/%m/%Y %H:%M', time.localtime(os.path.getmtime(selected_path)))
    tk.Label(prop_window, text=f"Modifié le : {mod_time}").pack(pady=5)

    # Boutons
    button_frame = tk.Frame(prop_window)
    button_frame.pack(pady=10)
    
    ok_button = tk.Button(button_frame, text="OK", state=tk.DISABLED, command=prop_window.destroy)
    ok_button.pack(side=tk.LEFT, padx=10)
    
    cancel_button = tk.Button(button_frame, text="Annuler", command=lambda: on_cancel())
    cancel_button.pack(side=tk.LEFT)
    
    

    def calculate_size():
        """Effectue le calcul de taille et met à jour l'interface"""
        nonlocal calculation_done
        try:
            if os.path.isdir(selected_path):
                total_size = get_folder_size(selected_path, cancel_event=cancel_event)
                if not cancel_event.is_set():
                    prop_window.after(0, lambda: update_display(total_size))
            else:
                total_size = os.path.getsize(selected_path)
                prop_window.after(0, lambda: update_display(total_size))
        except Exception :
            prop_window.after(0, lambda: size_label.config(text=f"Erreur : {str(Exception)}"))
        finally:
            calculation_done = True
            prop_window.after(0, lambda: ok_button.config(state=tk.NORMAL))

    def update_display(size_bytes):
        """Met à jour l'affichage avec la taille calculée"""
        size_label.config(text=f"Taille : {format_size(size_bytes)}")

    def on_cancel():
        """Annule le calcul et ferme la fenêtre"""
        cancel_event.set()
        prop_window.destroy()

    # Démarrer le calcul dans un thread séparé
    if os.path.isdir(selected_path):
        threading.Thread(target=calculate_size, daemon=True).start()
    else:
        calculate_size()  # Calcul direct pour les fichiers

    # Gestion fermeture fenêtre
    prop_window.protocol("WM_DELETE_WINDOW", on_cancel)
    prop_window.focus_force()
    
    
def show_progress_window(parent, operation_type):
    """Affiche une fenêtre de progression"""
    progress_top = tk.Toplevel(parent)
    progress_top.title(f"{operation_type} en cours")
    progress_top.geometry("300x120")
    progress_top.resizable(False, False)
    
    tk.Label(progress_top, text=f"{operation_type} en cours...").pack(pady=10)
    
    progress_var = tk.StringVar()
    progress_var.set("Démarrage...")
    progress_label = tk.Label(progress_top, textvariable=progress_var)
    progress_label.pack()
    
    # Empêche l'interaction avec la fenêtre principale
    progress_top.grab_set()
    
    return progress_top, progress_var

def update_progress(progress_top, progress_var, message, success=None):
    """Met à jour puis ferme la fenêtre de progression"""
    progress_var.set(message)
    
    if success is not None:
        # Ajoute un bouton OK à la fin
        btn_frame = tk.Frame(progress_top)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="OK", command=progress_top.destroy).pack()
        
        # Change la couleur selon le résultat
        color = "green" if success else "red"
        progress_label = progress_top.winfo_children()[1]
        progress_label.config(fg=color)
    else:
        progress_top.update()  # Force la mise à jour

# =============================================
# INTERFACE UTILISATEUR
# =============================================

# Frame des chemins d'accès et options
path_frame = tk.Frame(root, borderwidth=1, relief="solid")
path_frame.grid(column=0, row=0, padx=10, pady=5, columnspan=2, sticky="ew")
path_frame.grid_columnconfigure(1, weight=1)

# Frame pour les boutons de navigation
button_frame = tk.Frame(path_frame)
button_frame.grid(column=0, row=0, sticky="w", padx=5)

back_button = tk.Button(button_frame, text="\uf104 Retour", font="FA", fg="white", bg="black", command=go_back)
back_button.grid(column=0, row=0, padx=2, pady=10)

next_button = tk.Button(button_frame, text="Suivant \uf105", font="FA", fg="white", bg="black", command=go_ahead)
next_button.grid(row=0, column=1, padx=2, pady=10)

refresh_button = tk.Button(button_frame, text="\uf01e", font="FA", fg="white", bg="black", command=refresh_directory)
refresh_button.grid(row=0, column=2, padx=2, pady=10)

# Frame pour la barre de chemin
path_entry_frame = tk.Frame(path_frame, borderwidth=1, relief="solid")
path_entry_frame.grid(row=0, column=1, sticky="ew")
path_entry_frame.bind("<Button-1>", switch_to_entry)

# Barre de recherche
search_entry = tk.Entry(path_frame, borderwidth=1, relief="solid")
search_entry.grid(row=0, column=2, padx=5)
search_entry.bind("<KeyRelease>", update_search)

# Frame pour les options
options_frame = tk.Frame(path_frame)
options_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

# Bouton et menu de filtrage
filter_button = tk.Button(options_frame, text="\uf03a Filtrer", font="FA", padx=10)
filter_button.grid(row=0, column=4, padx=5)
filter_button.bind("<Button-1>", show_filter_menu)

filter_menu = Menu(root, tearoff=0)
for label in file_filters.keys():
    filter_menu.add_command(label=label, command=lambda l=label: apply_filter(l))

# Bouton Nouveau avec menu déroulant
new_button = tk.Button(options_frame, text="\uf067 Nouveau", font="FA", padx=10)
new_button.grid(row=0, column=0, padx=5)

new_menu = Menu(root, tearoff=0)
new_menu.add_command(label="Dossier", command=lambda: create_new("folder"))
new_menu.add_command(label="Fichier .txt", command=lambda: create_new("txt"))
new_menu.add_command(label="Fichier .html", command=lambda: create_new("html"))
new_menu.add_command(label="Fichier .js", command=lambda: create_new("js"))
new_menu.add_command(label="Fichier .php", command=lambda: create_new("php"))
new_menu.add_command(label="Autre fichier...", command=lambda: create_new("custom"))
new_button.bind("<Button-1>", lambda e: new_menu.post(e.x_root, e.y_root))

# Conteneur principal
bottom_frame = tk.Frame(root)
bottom_frame.grid(column=0, row=1, padx=10, sticky="nsew", columnspan=2)
bottom_frame.grid_columnconfigure(1, weight=3)
bottom_frame.grid_rowconfigure(0, weight=1)

# Frame pour la liste des fichiers
main_frame = tk.Frame(bottom_frame, borderwidth=1, relief="solid")
main_frame.grid(column=1, row=0, pady=5, sticky="nsew")
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

list_frame = tk.Frame(main_frame)
list_frame.grid(row=0, column=0, sticky="nsew")

scrollbar = Scrollbar(list_frame)
scrollbar.pack(side="right", fill="y")

file_list = tk.Listbox(list_frame, font=("Arial", 15), yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED)
file_list.pack(fill="both", expand=True, padx=5)
file_list.bind("<Double-Button-1>", item_select)
file_list.bind("<Button-3>", right_click)
file_list.bind("<<ListboxSelect>>", update_status_bar)
file_list.bind("<Control-Alt-Button-1>", lambda e: None)
file_list.bind("<Control-a>", lambda e: select_all_files())
file_list.bind("<Control-A>", lambda e: select_all_files())
scrollbar.config(command=file_list.yview)

# Barre de statut
status_frame = tk.Frame(main_frame, borderwidth=1, relief="sunken", height=22)
status_frame.grid(row=1, column=0, sticky="ew")
status_frame.grid_propagate(False)

status_var = tk.StringVar()
status_var.set("Prêt")
status_label = tk.Label(status_frame, textvariable=status_var, anchor="w")
status_label.pack(fill="x", padx=5)

# Frame pour le menu latéral
global_frame = tk.Frame(bottom_frame, borderwidth=1, relief="solid")
global_frame.grid(column=0, row=0, pady=5, sticky="nsw")
global_frame.config(width=int(1100*0.25))

menu_list = tk.Listbox(global_frame, selectmode=tk.SINGLE, font=("Arial", 15))
menu_list.pack(fill=tk.BOTH, expand=True)
sections = ["Recents", "Favorites", "computer"]
for section in sections:
    menu_list.insert(tk.END, section)
menu_list.bind("<<ListboxSelect>>", on_menu_item_select)

# =============================================
# LANCEMENT DE L'APPLICATION
# =============================================

load_directory(root_directory)
root.mainloop()