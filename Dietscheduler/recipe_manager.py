import os
import tkinter as tk
import json

def send_message_to_comm(comm_var,message):
    comm_var.set(message)


def delete_listbox_entry(listbox, list, reversed_dict, database, comm_var):
    listbox_index = listbox.curselection()[0]
    value = listbox.get(listbox_index)
    selected_ingredient_index = reversed_dict[value]
    database.pop(selected_ingredient_index)
    list.remove(value)
    reversed_dict.pop(value)
    refresh_listbox(listbox, list)
    send_message_to_comm(comm_var = comm_var,message=f"deleted {value} at index {selected_ingredient_index} from database.")

def refresh_listbox(listbox,list):
    listbox.delete(0, "end")
    for elem in sorted(list,key=str.casefold):
        listbox.insert("end", elem)

def make_new_index(id_list):
    new_index = 0
    while new_index in id_list:
        new_index += 1
    return new_index

def entry_callback(database, selected_r, selected_i, value, entry_type, key):

    if entry_type == 'qty':
        database['recipes'][selected_r]['ingredient'][selected_i][key] = value.get()
    if entry_type == 'constraint':
        database['recipes'][selected_r]['ingredient'][selected_i]['constraints'][key] = value.get()
    if entry_type == 'ingredient_property':
        database['ingredients'][selected_i][key] = value.get()

class RecipeManager:
    def __init__(self, master, database,dirname):
        self.master = master
        self.database = database

        self.reversed_ingredient_dict = {}
        self.reversed_recipe_dict = {}
        self.ingredient_name_list = None
        self.ingredient_id_list = None
        self.recipe_name_list = None
        self.selected_recipe = None
        self.selected_ingredient = None
        self.comm_var = None
        self.legumen_var = None
        self.poultry_var = None
        self.egg_var = None
        self.red_meat_var = None
        self.seafood_var = None
        self.dairy_var = None
        self.soy_var = None
        self.create_gui()
        self.dirname = None
    def create_gui(self):
    # define handler-functions
        def init_new_recipe():
            if new_name_var.get().lower() not in [item.lower() for item in self.recipe_name_list]:
                self.recipe_name_list.append(new_name_var.get())
                index_list = [int(i) for i in self.database['recipes'].keys()]
                new_index = make_new_index(index_list)
                self.reversed_recipe_dict[new_name_var.get()] = new_index
                self.database['recipes'][new_index] =  {
                    "name": new_name_var.get(),
                    "ingredient": {
                    } ,
                    "M1": False,
                    "M2": False,
                    "M3": False,
                    "url": "",
                    "protein_sources": []
                }
                refresh_listbox(recipe_listbox,self.recipe_name_list)
            else:
                send_message_to_comm(comm_var=self.comm_var, message=f"Recipe with name \"{new_name_var.get()}\" already in database!")



        def save_database():
            with open(os.path.join(dirname, "data\\recipe_ingredient_database.json"),'w') as file:
                json.dump(self.database, fp=file)
                file.close()
        def set_protein_source(var, protein_source):
            if var.get() is True and protein_source not in self.database['recipes'][self.selected_recipe]['protein_sources']:
                self.database['recipes'][self.selected_recipe]['protein_sources'].append(protein_source)
            else:
                self.database['recipes'][self.selected_recipe]['protein_sources'].remove(protein_source)

        def set_meal(meal,var):
            self.database['recipes'][self.selected_recipe][meal] = var.get()

        def open_recipe_edit_window():
            RecipeEditWindow(self)

        def create_ingredient_manager():
            IngredientManager(self)

        def recipe_selection(event):
            ''' shows the ingredients for the selected recipe in the ingredient-listbox'''
            # delete the old list of ingredients when a new recipe is chosen
            selection = event.widget.curselection()
            if selection:
                ingredient_listbox.delete(0, tk.END)
                qty_var.set("")
                min_var.set("")
                max_var.set("")
                # fill the list with the ingredients from the new recipe
                index = str(recipe_listbox.curselection()[0])
                recipe_name = recipe_listbox.get(index)
                self.selected_recipe = self.reversed_recipe_dict[recipe_name]
                # set the boolean Variables for the meal-slots
                breakfast_var.set(self.database['recipes'][self.selected_recipe]['M1'])
                lunch_var.set(self.database['recipes'][self.selected_recipe]['M2'])
                dinner_var.set(self.database['recipes'][self.selected_recipe]['M3'])
                # set the boolean Variables for the protein sources
                checkbox_vars = [self.legumen_var, self.poultry_var, self.egg_var, self.red_meat_var,
                                 self.seafood_var, self.dairy_var,self.soy_var]
                protein_sources = ["legumen","poultry","egg","red meat","seafood","dairy","soy"]
                for elem, var in zip(protein_sources,checkbox_vars):
                    if elem in self.database['recipes'][self.selected_recipe]['protein_sources']:
                        var.set(True)
                    else:
                        var.set(False)
                for elem in list(database['recipes'][self.selected_recipe]['ingredient'].keys()):
                    ingredient_listbox.insert("end", database['recipes'][self.selected_recipe]['ingredient'][elem]['name'])

        def ingredient_selection(event):
            ''' show the properties of an ingredient selected in the ingredient-listbox'''
            selection = event.widget.curselection()
            if selection:
                ing_name = ingredient_listbox.curselection()[0]
                self.selected_ingredient = list(database['recipes'][self.selected_recipe]['ingredient'].keys())[ing_name]
                qty = database['recipes'][self.selected_recipe]['ingredient'][self.selected_ingredient]['qty']
                if database['ingredients'][self.selected_ingredient]['optimization_include']:
                    max_entry.config(state='normal')
                    min_entry.config(state='normal')
                    min = database['recipes'][self.selected_recipe]['ingredient'][self.selected_ingredient]['constraints']['min']
                    max = database['recipes'][self.selected_recipe]['ingredient'][self.selected_ingredient]['constraints']['max']
                    min_var.set(min)
                    max_var.set(max)
                else:
                    max_var.set("N/A")
                    min_var.set("N/A")
                    max_entry.config(state='disabled')
                    min_entry.config(state='disabled')
                qty_var.set(qty)

        # define reversed dict for ingredients (with format "name : id")
        for ingredient_id in list(self.database['ingredients'].keys()):
            self.reversed_ingredient_dict[self.database['ingredients'][ingredient_id]['name']] = ingredient_id
        # define reversed dict for recipes (with format "name : id")
        for recipe_id in list(self.database['recipes'].keys()):
            self.reversed_recipe_dict[self.database['recipes'][recipe_id]['name']] = recipe_id
        # list all ingredient-ids and ingredient-names
        self.ingredient_id_list = [int(i) for i in self.database['ingredients'].keys()]
        self.ingredient_name_list = sorted([self.database['ingredients'][i]['name'] for i in self.database['ingredients'].keys()],key=str.casefold)
        # list all recipe-ids and recipe-names
        self.ingredient_id_list = [int(i) for i in self.database['recipes'].keys()]
        self.recipe_name_list = [self.database['recipes'][i]['name'] for i in list(self.database['recipes'].keys())]
        # define frame, variable and widget for communication:
        entry_comm_frame = tk.Frame(self.master)
        entry_comm_frame.configure(width = 700)
        entry_comm_frame.grid(column = 4)
        comm_frame = tk.Frame(self.master)
        self.comm_var = tk.StringVar()
        comm_label = tk.Label(comm_frame, textvariable = self.comm_var)
        comm_label.grid()
        comm_frame.grid(column = 4, row = 1)
        # define and place separating frames on main window
        radio_frame = tk.Frame(entry_comm_frame)
        sep_frame_recipe_ingredient = tk.Frame(self.master, width=5, height=200, bg="green")
        sep_frame_recipe_ingredient.grid(column=1, row=0)
        sep_frame_ingredient_frame = tk.Frame(self.master, width=5, height=200, bg="green")
        sep_frame_ingredient_frame.grid(column=3, row=0)
        sep_frame_radio_entry = tk.Frame(self.master, width=5, height=200, bg="green")
        sep_frame_radio_entry.grid(column=3, row=0)
        sep_frame_radio_protein = tk.Frame(self.master, width=5, height=200, bg="green")
        sep_frame_radio_protein.grid(column = 7, row = 0)
        entry_frame = tk.Frame(entry_comm_frame)
        recipe_listbox_frame = tk.Frame(self.master)
        new_name_frame = tk.Frame(recipe_listbox_frame)
        ingredient_listbox_frame = tk.Frame(self.master)
        add_delete_ingredient_frame = tk.Frame(ingredient_listbox_frame)
        recipe_listbox_frame.grid(column=0, row=0)
        ingredient_listbox_frame.grid(column=2, row=0)
        entry_frame.grid(column=4, row=0)
        radio_frame.grid(column=6, row=0)
        protein_source_frame = tk.Frame(self.master)
        protein_source_frame.grid(column = 8, row = 0)
        add_delete_ingredient_frame.grid(row=1)
        new_name_frame.grid(row =2)

        # recipe and ingredient listbox
        recipe_listbox = tk.Listbox(recipe_listbox_frame,exportselection = False, width = 35)
        recipe_listbox.grid(row = 0)

        # initiate recipe listbox:
        refresh_listbox(listbox = recipe_listbox, list = self.recipe_name_list)

        ingredient_listbox = tk.Listbox(ingredient_listbox_frame,exportselection=False)
        ingredient_listbox.grid(row=0)

        # define label and entry for new name
        new_name_label = tk.Label(new_name_frame,text = "Type in new recipe \n and hit enter!")
        new_name_label.grid(row=1, column = 0)
        new_name_var = tk.StringVar()
        new_name_entry = tk.Entry(new_name_frame, textvariable = new_name_var,width = 17)
        new_name_entry.bind('<Return>',lambda event: init_new_recipe() )
        new_name_entry.grid(row = 1,column = 1)

        # define variables and widgets for quantity and max-/ min-constraints
        qty_var = tk.IntVar()
        min_var = tk.IntVar()
        max_var = tk.IntVar()

        qty_var.trace("w", lambda event, index, mode: entry_callback(database = self.database,
                                                                     selected_r = self.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='qty',
                                                                     key = 'qty',
                                                                     value = qty_var))

        min_var.trace("w", lambda event, index, mode: entry_callback(database = self.database,
                                                                     selected_r = self.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     key = 'min',
                                                                     value = min_var,
                                                                     entry_type= 'constraint'))

        max_var.trace("w",lambda event, index, mode: entry_callback(database=self.database,
                                                                     selected_r=self.selected_recipe,
                                                                     selected_i=self.selected_ingredient,
                                                                     key='max',
                                                                     value=max_var,
                                                                     entry_type='constraint'))

        qty_label = tk.Label(entry_frame, text = "Quantity of ingredient")
        qty_label.grid(column = 0, row = 1)
        qty_entry = tk.Entry(entry_frame, width=7, name="qty_entry", textvariable = qty_var)
        qty_entry.grid(column = 1, row = 1)
        min_label = tk.Label(entry_frame, text = "min. amount of ingredient in recipe")
        min_label.grid(column = 0, row = 2)
        min_entry = tk.Entry(entry_frame, width=7, name="min_entry", textvariable = min_var)
        min_entry.grid(column = 1, row= 2)
        max_label = tk.Label(entry_frame, text = "max. amount of ingredient in recipe")
        max_label.grid(column = 0, row = 3)
        max_entry = tk.Entry(entry_frame, width=7, name="max_entry", textvariable = max_var)
        max_entry.grid(column = 1, row = 3)

        # define variables and widgets for meal-slots
        breakfast_var = tk.BooleanVar()
        lunch_var = tk.BooleanVar()
        dinner_var = tk.BooleanVar()
        breakfast_checkbox = tk.Checkbutton(radio_frame, text = "Recipe is suitable for breakfast", variable = breakfast_var,
                                           command = lambda: set_meal("M1",breakfast_var))
        breakfast_checkbox.grid(row = 0, column = 1)

        lunch_checkbox = tk.Checkbutton(radio_frame, text = "Recipe is suitable for lunch", variable = lunch_var,
                                           command = lambda: set_meal("M2",lunch_var))
        lunch_checkbox.grid(row = 1, column = 1)

        dinner_checkbox = tk.Checkbutton(radio_frame, text = "Recipe is suitable for dinner", variable = dinner_var,
                                           command = lambda: set_meal("M3",dinner_var))
        dinner_checkbox.grid(row = 2, column = 1)

        # define variables and widgets for protein source
        self.legumen_var = tk.BooleanVar()
        self.poultry_var = tk.BooleanVar()
        self.egg_var = tk.BooleanVar()
        self.red_meat_var = tk.BooleanVar()
        self.seafood_var = tk.BooleanVar()
        self.dairy_var = tk.BooleanVar()
        self.soy_var = tk.BooleanVar()

        legumen_checkbox = tk.Checkbutton(protein_source_frame, text = "legumen as protein source", variable = self.legumen_var,
                                               command = lambda: set_protein_source(self.legumen_var, protein_source="legumen"))
        legumen_checkbox.grid()

        poultry_checkbox = tk.Checkbutton(protein_source_frame, text = "poultry as protein source", variable = self.poultry_var,
                                               command = lambda: set_protein_source(self.poultry_var, protein_source="poultry"))
        poultry_checkbox.grid()

        egg_checkbox = tk.Checkbutton(protein_source_frame, text = "egg as protein source", variable = self.egg_var,
                                               command = lambda: set_protein_source(self.egg_var, protein_source="egg"))
        egg_checkbox.grid()

        red_meat_checkbox = tk.Checkbutton(protein_source_frame, text = "red meat as protein source", variable = self.red_meat_var,
                                               command = lambda: set_protein_source(self.red_meat_var, protein_source="red meat"))
        red_meat_checkbox.grid()

        seafood_checkbox = tk.Checkbutton(protein_source_frame, text = "seafood as protein source", variable = self.seafood_var,
                                               command = lambda: set_protein_source(self.seafood_var, protein_source="seafood"))
        seafood_checkbox.grid()

        dairy_checkbox = tk.Checkbutton(protein_source_frame, text = "dairy as protein source", variable = self.dairy_var,
                                               command = lambda: set_protein_source(self.dairy_var, protein_source="dairy"))
        dairy_checkbox.grid()

        soy_checkbox = tk.Checkbutton(protein_source_frame, text = "soy as protein source", variable = self.soy_var,
                                               command = lambda: set_protein_source(self.soy_var, protein_source="soy"))
        soy_checkbox.grid()

        # define bindings for listboxes
        recipe_listbox.bind("<<ListboxSelect>>", recipe_selection)
        ingredient_listbox.bind("<<ListboxSelect>>", ingredient_selection)

        # define buttons for database-manipulation
        delete_recipe_button = tk.Button(self.master,text = "Delete selected recipe",bg = "red",
                                              command = lambda: delete_listbox_entry(listbox = recipe_listbox,
                                                                                     list = self.recipe_name_list,
                                                                                     reversed_dict = self.reversed_recipe_dict,
                                                                                     database= self.database['recipes'],
                                                                                     comm_var = self.comm_var
                                                                                     ))
        edit_ingredients_button = tk.Button(self.master, text="Edit ingredient-database",
                                           command= create_ingredient_manager)
        add_ingredient_button = tk.Button(add_delete_ingredient_frame,text = "Edit chosen recipe ",
                                               bg = "lightgreen", command = open_recipe_edit_window)
        save_database_button = tk.Button(self.master, text = "Save database",
                                  command = save_database)
        delete_recipe_button.grid()
        save_database_button.grid()
        add_ingredient_button.grid()
        edit_ingredients_button.grid()

class IngredientManager(tk.Toplevel):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.create_gui()

    def ingredient_selection(self,event):
        selection = event.widget.curselection()

        if selection:

            listbox_index = self.ingredient_listbox.curselection()[0]
            value = self.ingredient_listbox.get(listbox_index)
            self.selected_ingredient = self.parent.reversed_ingredient_dict[value]
            self.standard_unit_var.set(database['ingredients'][self.selected_ingredient]['unit'])
            self.standard_qty_var.set(database['ingredients'][self.selected_ingredient]['standard_qty'])
            self.calorie_var.set(database['ingredients'][self.selected_ingredient]['calorie'])
            self.carb_var.set(database['ingredients'][self.selected_ingredient]['carb'])
            self.protein_var.set(database['ingredients'][self.selected_ingredient]['protein'])
            self.fat_var.set(database['ingredients'][self.selected_ingredient]['fat'])
            self.price_var.set(database['ingredients'][self.selected_ingredient]['price'])
            self.opti_include_var.set(database['ingredients'][self.selected_ingredient]['optimization_include'])
            self.price_include_var.set(database['ingredients'][self.selected_ingredient]['count_price'])
            self.distinct_include_var.set(database['ingredients'][self.selected_ingredient]['distinct_ingredient'])
            self.old_name_var.set(database['ingredients'][self.selected_ingredient]['name'])

    def populate_ingredient_listbox(self, listbox):
        for elem in sorted(self.parent.ingredient_name_list,key=str.casefold):
            listbox.insert("end", elem)

    def send_new_ingredient(self):
        if self.new_name_var.get().lower() in [item.lower() for item in self.parent.ingredient_name_list]:
            send_message_to_comm(comm_var= self.comm_message, message=f"'{self.new_name_var.get()}' already in database!")

        else:
            index_list = [int(i) for i in self.parent.database['ingredients'].keys()]
            new_index = make_new_index(index_list)
            self.parent.database['ingredients'][new_index] = {}
            self.parent.database['ingredients'][new_index]['name'] = self.new_name_var.get()
            self.parent.database['ingredients'][new_index]['unit'] = self.standard_unit_var.get() #
            self.parent.database['ingredients'][new_index]['standard_qty'] = self.standard_qty_var.get()
            self.parent.database['ingredients'][new_index]['calorie'] = self.calorie_var.get()
            self.parent.database['ingredients'][new_index]['protein'] = self.protein_var.get()
            self.parent.database['ingredients'][new_index]['fat'] = self.fat_var.get()
            self.parent.database['ingredients'][new_index]['carb'] = self.carb_var.get()
            self.parent.database['ingredients'][new_index]['price'] = self.price_var.get()
            self.parent.database['ingredients'][new_index]['optimization_include'] = self.opti_include_var.get()
            self.parent.database['ingredients'][new_index]['count_price'] = self.price_include_var.get()
            self.parent.database['ingredients'][new_index]['distinct_ingredient'] = self.distinct_include_var.get()
            self.parent.ingredient_name_list.append(self.new_name_var.get())
            self.parent.ingredient_name_list.sort()

            self.parent.reversed_ingredient_dict[self.new_name_var.get()] = new_index
            send_message_to_comm(comm_var=self.comm_message,
                                 message=f"added '{self.new_name_var.get()}' to database at index {new_index}.")

        refresh_listbox(listbox = self.ingredient_listbox, list = self.parent.ingredient_name_list)

    def create_gui(self):
        radio_frame = tk.Frame(self)

        sep_frame_radio_entry = tk.Frame(self, width=5, height=200, bg="green")
        sep_frame_radio_entry.grid(column=3, row=0)
        sep_frame_listbox_entry = tk.Frame(self, width=5, height=200, bg="green")
        sep_frame_listbox_entry.grid(column=1, row=0)
        entry_frame = tk.Frame(self)
        listbox_frame = tk.Frame(self)
        comm_frame = tk.Frame(self)

        listbox_frame.grid(column=0, row=0)
        entry_frame.grid(column=2, row=0)
        radio_frame.grid(column=4, row=0)
        comm_frame.grid(column = 0, row = 1, columnspan = 3)

        standard_unit_label = tk.Label(entry_frame, text="standard unit of ingredient")
        standard_unit_label.grid(column=0, row=0)
        self.standard_unit_var = tk.StringVar()
        self.standard_unit_var.trace("w", lambda event, index, mode: entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'unit',
                                                                     value = self.standard_unit_var))
        standard_unit_var_entry = tk.Entry(entry_frame, width=7, name="new_unit_entry", textvariable=self.standard_unit_var)
        standard_unit_var_entry.grid(column=1, row=0)

        standard_qty_label = tk.Label(entry_frame, text="standard quantity of ingredient")
        standard_qty_label.grid(column=0, row=1)
        self.standard_qty_var = tk.StringVar()
        self.standard_qty_var.trace("w", lambda event, index, mode: entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'standard_qty',
                                                                     value = self.standard_qty_var))
        standard_qty_var_entry = tk.Entry(entry_frame, width=7, name="new_qty_entry", textvariable=self.standard_qty_var)
        standard_qty_var_entry.grid(column=1, row=1)
        calorie_var_label = tk.Label(entry_frame, text= "Calories per 1 unit of ingredient")
        calorie_var_label.grid(column=0, row=2)
        self.calorie_var = tk.StringVar()
        self.calorie_var.trace("w", lambda event, index, mode: entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'calorie',
                                                                     value = self.calorie_var))
        calorie_var_entry = tk.Entry(entry_frame, width=7, name="new_calorie_entry", textvariable=self.calorie_var)
        calorie_var_entry.grid(column=1, row=2)

        protein_var_label = tk.Label(entry_frame, text="Grams of protein per 1 unit of ingredient")
        protein_var_label.grid(column=0, row=3)
        self.protein_var = tk.StringVar()
        self.protein_var.trace("w", lambda event, index, mode: entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'protein',
                                                                     value = self.protein_var))
        protein_var_entry = tk.Entry(entry_frame, width=7, name="new_protein_entry", textvariable=self.protein_var)
        protein_var_entry.grid(column=1, row=3)

        fat_var_label = tk.Label(entry_frame, text="Grams of fat per 1 unit of ingredient")
        fat_var_label.grid(column=0, row=4)
        self.fat_var = tk.StringVar()
        self.fat_var.trace("w", lambda event, index, mode: entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'fat',
                                                                     value = self.fat_var))
        fat_var_entry = tk.Entry(entry_frame, width=7, name="new_fat_entry", textvariable=self.fat_var)
        fat_var_entry.grid(column=1, row=4)

        carb_var_label = tk.Label(entry_frame, text="Grams of carbs per 1 unit of ingredient")
        carb_var_label.grid(column=0, row=5)
        self.carb_var = tk.StringVar()
        self.carb_var.trace("w", lambda event, index, mode: entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'carb',
                                                                     value = self.carb_var))
        carb_var_entry = tk.Entry(entry_frame, width=7, name="new_carb_entry", textvariable=self.carb_var)
        carb_var_entry.grid(column=1, row=5)

        price_var_label = tk.Label(entry_frame, text="Price per 1 unit of ingredient")
        price_var_label.grid(column=0, row=6)
        self.price_var = tk.StringVar()
        self.price_var.trace("w", lambda event, index, mode: entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'price',
                                                                     value = self.price_var))
        price_var_entry = tk.Entry(entry_frame, width=7, name="new_price_entry", textvariable=self.price_var)
        price_var_entry.grid(column=1, row=6)

        old_name_label = tk.Label(entry_frame, text = "Name of ingredient")
        old_name_label.grid(column = 0, row= 7)
        self.old_name_var = tk.StringVar()
        self.old_name_var.trace("w", lambda event, index, mode: entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'name',
                                                                     value = self.old_name_var))
        old_name_entry = tk.Entry(entry_frame, width=10, name="old_name_entry", textvariable=self.old_name_var)
        old_name_entry.grid(column = 1, row = 7)

        opti_include_label = tk.Label(radio_frame, text="include ingredient into optimization?")
        opti_include_label.grid(row=0, column=0)
        self.opti_include_var = tk.BooleanVar()
        opti_include_label = tk.Label(radio_frame, text="distinct ingredient?")
        opti_include_label.grid(row=2, column=0)
        opti_include_checkbox = tk.Checkbutton(radio_frame,variable = self.opti_include_var,
                                               command = lambda : entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'optimization_include',
                                                                     value = self.opti_include_var))
        opti_include_checkbox.grid(row = 0, column = 1)

        price_include_label = tk.Label(radio_frame, text="include price into optimization?")
        price_include_label.grid(row=1, column=0)
        self.price_include_var = tk.BooleanVar()
        price_include_checkbox = tk.Checkbutton(radio_frame,variable = self.price_include_var,
                                               command = lambda : entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'count_price',
                                                                     value = self.price_include_var))
        price_include_checkbox.grid(row = 1, column = 1)

        self.distinct_include_var = tk.BooleanVar()
        distinct_include_label = tk.Label(radio_frame, text="distinct ingredient?")
        distinct_include_label.grid(row=2, column=0)
        distinct_include_checkbox = tk.Checkbutton(radio_frame,variable = self.distinct_include_var,
                                               command = lambda : entry_callback(database = self.parent.database,
                                                                     selected_r = self.parent.selected_recipe,
                                                                     selected_i = self.selected_ingredient,
                                                                     entry_type='ingredient_property',
                                                                     key = 'distinct_ingredient',
                                                                     value = self.distinct_include_var))
        distinct_include_checkbox.grid(row = 2, column = 1)

        self.ingredient_listbox = tk.Listbox(listbox_frame, selectmode="single", exportselection=False)
        self.ingredient_listbox.grid()

        self.comm_message = tk.StringVar()
        comm_label = tk.Label(comm_frame, textvariable = self.comm_message)
        comm_label.grid(column = 2)

        self.ingredient_listbox.bind("<<ListboxSelect>>", self.ingredient_selection)
        self.populate_ingredient_listbox(self.ingredient_listbox)

        self.new_name_var = tk.StringVar()
        new_name_entry = tk.Entry(self, width=10, name="new_name_entry", textvariable=self.new_name_var)
        new_name_entry.bind("<Return>", lambda event: self.send_new_ingredient())
        new_name_entry.grid()
        send_button = tk.Button(self, text="Add ingredient to database",
                                command=self.send_new_ingredient)
        send_button.grid()
        self.delete_button = tk.Button(self, text = "Delete selected ingredient \n from database",
                                  command = lambda : delete_listbox_entry(listbox= self.ingredient_listbox,
                                                                 reversed_dict=self.parent.reversed_ingredient_dict,
                                                                 list = self.parent.ingredient_name_list,
                                                                 database = self.parent.database['ingredients'],
                                                                 comm_var = self.comm_message))
        self.delete_button.grid()

class RecipeEditWindow(tk.Toplevel):

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.create_gui()
        self.recipe_ingredient_list = []
        self.database_ingredient_list = []

    def remove_ingredient_from_recipe(self):
        index = self.recipe_ingredient_listbox.curselection()[0]
        ingredient_name = self.recipe_ingredient_listbox.get(index)
        ingredient_id = self.parent.reversed_ingredient_dict[ingredient_name]
        self.parent.database['recipes'][self.parent.selected_recipe]['ingredient'].pop(ingredient_id)

        self.recipe_ingredient_list = [self.parent.database['ingredients'][ingredient]['name'] for ingredient
                                       in self.parent.database['recipes'][self.parent.selected_recipe]['ingredient'].keys()]

        self.database_ingredient_list = [self.parent.database['ingredients'][ingredient]['name'] for ingredient
                                         in self.parent.database['ingredients'].keys()
                                         if self.parent.database['ingredients'][ingredient]['name'] not in self.recipe_ingredient_list]

        refresh_listbox(self.recipe_ingredient_listbox, self.recipe_ingredient_list)
        refresh_listbox(self.database_ingredient_listbox, self.database_ingredient_list)

    def add_ingredient_to_recipe(self):
        index = self.database_ingredient_listbox.curselection()[0]
        ingredient_name = self.database_ingredient_listbox.get(index)
        ingredient_id = self.parent.reversed_ingredient_dict[ingredient_name]

        if ingredient_id not in self.parent.database['recipes'][self.parent.selected_recipe]['ingredient'].keys():
            self.parent.database['recipes'][self.parent.selected_recipe]['ingredient'][ingredient_id] = {}
            self.parent.database['recipes'][self.parent.selected_recipe]['ingredient'][ingredient_id] = {
                "qty": 00,
                "constraints": {
                    "min": 00,
                    "max": 00
                },
                "name": ingredient_name
            }

        self.recipe_ingredient_list = [self.parent.database['ingredients'][ingredient]['name'] for ingredient
                                       in self.parent.database['recipes'][self.parent.selected_recipe]['ingredient'].keys()]

        self.database_ingredient_list = [self.parent.database['ingredients'][ingredient]['name'] for ingredient
                                         in self.parent.database['ingredients'].keys()
                                         if self.parent.database['ingredients'][ingredient]['name'] not in self.recipe_ingredient_list]


        refresh_listbox(self.recipe_ingredient_listbox, self.recipe_ingredient_list)
        refresh_listbox(self.database_ingredient_listbox, self.database_ingredient_list)


    def create_gui(self):
        self.recipe_ingredient_list = [self.parent.database['ingredients'][ingredient]['name'] for ingredient
                                       in self.parent.database['recipes'][self.parent.selected_recipe]['ingredient'].keys()]

        self.database_ingredient_list = [self.parent.database['ingredients'][ingredient]['name'] for ingredient
                                         in self.parent.database['ingredients'].keys()
                                         if self.parent.database['ingredients'][ingredient]['name'] not in self.recipe_ingredient_list]
        button_frame = tk.Frame(self)
        button_frame.grid(row = 0, column = 1)
        self.recipe_ingredient_listbox = tk.Listbox(self)
        self.recipe_ingredient_listbox.grid(row = 0, column = 0)
        refresh_listbox(self.recipe_ingredient_listbox, self.recipe_ingredient_list)
        self.database_ingredient_listbox = tk.Listbox(self)
        self.database_ingredient_listbox.grid(row = 0, column = 2)
        refresh_listbox(self.database_ingredient_listbox, self.database_ingredient_list)

        delete_from_recipe_button = tk.Button(button_frame, text = " > ", bg = "red",
                                                   command = lambda : self.remove_ingredient_from_recipe())

        move_into_recipe_button = tk.Button(button_frame, text = " < ", bg = "green",
                                                   command = lambda : self.add_ingredient_to_recipe())
        delete_from_recipe_button.grid(row = 1)
        move_into_recipe_button.grid(row = 0)



dirname = os.path.dirname(__file__)
with open(os.path.join(dirname, "data\\recipe_ingredient_database.json")) as file:
    database = json.load(file)
    file.close()

root = tk.Tk()
manager_gui = RecipeManager(root,database,dirname)
root.mainloop()

