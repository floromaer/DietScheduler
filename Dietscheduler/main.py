import os
import tkinter as tk
from tkinter import ttk
import itertools
import json
from lib import diet_sched
from datetime import datetime
from datetime import timedelta
from tkinter import ttk
from lib.menu_converter import parse_menu_to_excel
import threading
dirname = os.path.dirname(__file__)
with open(os.path.join(dirname,"data\\recipe_ingredient_database.json")) as file:
    food_database = json.load(file)
    file.close()
with open(os.path.join(dirname,"data\\user_database.json")) as file:
    user_database = json.load(file)
    file.close()

def send_new_user(user_database,new_name,parent):
    if new_name not in user_database.keys():
        user_database[new_name] = {
                  "cals": None,
                  "exclude_list": [],
                  "recipes":{} }
        parent.send_message_to_comm(f"Set new user {new_name}!")
    else:
        parent.send_message_to_comm(f"User {new_name} already in database!")

class NewUserWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.create_gui()

    def create_gui(self):
        self.main_frame = tk.Frame(self)
        self.main_frame.grid()
        self.entry_frame = tk.Frame(self.main_frame)
        self.entry_frame.grid()
        self.new_name_var = tk.StringVar()
        self.name_entry = tk.Entry(self.entry_frame, textvariable = self.new_name_var)
        self.name_entry.grid()
        self.name_entry.bind('<Return>', lambda event: send_new_user(self.parent.user_database, self.new_name_var.get(), self.parent))

class SchedulerWindow:
    def __init__(self, master, user_database, food_database,dirname):
        self.master = master
        self.user_database = user_database
        self.food_database = food_database
        self.comm_var = tk.StringVar()
        self.tile_button_dict = {}
        self.radio_button_dict = {}
        self.group_dict = {}
        self.color_list = ["#73AB73", "#E6ACAC", "#D5AF90", "#AB7493", "#ebf2d7",
                      "#0f5f61", "#cc4576", "#dbceed", "#2fcfef", "#363747", "#073ef4"]
        self.menu = None
        self.groups_set = False
        self.dates_set = False
        self.create_gui()
    def check_dict(self):
        for key in self.group_dict.keys():
            if not len(self.group_dict[key]) == 0:
                self.groups_set = True
            else:
                self.groups_set = False
    def calculate_menu_parse_result(self,kcal, chosen_diet):
        self.check_dict()
        if self.dates_set is False:
            self.send_message_to_comm("Error! Set the dates first!")
            pass

        if self.groups_set is False:
            self.send_message_to_comm("Error! Set the groups first!")
            pass
        if self.groups_set is False and self.dates_set is False:
            self.send_message_to_comm("Error! Set the groups and dates first!")
            pass
        if self.dates_set and self.groups_set:
            self.send_message_to_comm("Calculating your menu - this could take up to 3 minutes!")
            pb = ttk.Progressbar(
                self.comm_frame,
                orient='horizontal',
                mode='indeterminate',
                length=280
            )
            pb.grid(column=0, row=1, columnspan=2, padx=10, pady=20)
            pb.start()
            excel_file = os.path.join(dirname, f"data\\menues\\menu_{self.date_label_var_dict['D1']['date_var'].get()}_to_"
                                                f"{self.date_label_var_dict['D7']['date_var'].get()}.xlsx")
            self.menu.calculate_menu(food_database=self.food_database,
                                     user_database = self.user_database,
                                     user = self.user_name.get(),
                                     start_date = self.date.get(),
                                     groups=list(tuple(self.group_dict[key]) for key in self.group_dict.keys()),
                                     exclude_list=[],
                                     kcal=kcal.get(),
                                     diet=chosen_diet.get())
            pb.stop()
            pb.destroy()
            parse_menu_to_excel(
                filename=excel_file,
                menu_dict=self.menu.menu_dict, days_dict=self.date_label_var_dict,
                results=self.menu.result_dict, goal_dict=self.menu.goal_dict,
                food_database=self.food_database, reversed_ingredient_dict=self.menu.reversed_ingredient_dict,
                grocery_dict=self.menu.grocery_dict)
            if self.menu.status:
                message_to_comm = str()
                for key in self.menu.menu_dict.keys():
                    temp_string = str()
                    for subitem in key:
                        temp_string += str(f'On {subitem[0]} for {subitem[1]} ')
                    message_to_comm += str(f"{temp_string}: {list(self.menu.menu_dict[key].keys())[0]} \n")
                self.send_message_to_comm(message_to_comm)
            if not self.menu.status:
                self.send_message_to_comm("Could not calculate Menu! \n Try changing calories or diet!")


    def compile_dates(self, start_date, date_label_var):
        compiled_date = datetime.strptime(start_date,'%d.%m.%Y')
        day_list = ["D1","D2","D3","D4","D5","D6","D7"]
        weekdays = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        for i in range(0,7):
            new_date = compiled_date + timedelta(days=i)
            date_label_var[day_list[i]]['date_var'].set(new_date.strftime('%d.%m.%Y') )
            date_label_var[day_list[i]]['day_var'].set(weekdays[new_date.weekday()])
        self.dates_set = True
    def send_message_to_comm(self, message):
        self.comm_var.set(message)
    def meal_toggle(self, button, chosen_group_var,color_list, color_number, index, group_dict, meals_days_list):
        """This function declares the mealslots for which the user wants to eat"""
        if button.config('relief')[-1] == 'sunken':
            button.config(relief="raised", background="SystemButtonFace")
            for key in group_dict.keys():
                if meals_days_list[index] in group_dict[key]:
                    group_dict[key].remove(meals_days_list[index])
        else:
            button.config(relief="sunken", background=color_list[color_number])
            group_dict[chosen_group_var.get()].append(meals_days_list[index])
    def radio_create(self,amount_of_groups,button_frame,radio_button_dict,variable,group_dict):
        """this function creates radiobuttons which refer to recipe-groups"""
        if len(radio_button_dict.keys()) == 0:
            for i in range(amount_of_groups):
                radio_button_dict[i] = tk.Radiobutton(
                    button_frame,
                    text=f"recipe No. {i+1}",
                    variable=variable,
                    value=i,
                    bg=self.color_list[i+1]
                    )
                group_dict[i] = []
                radio_button_dict[i].grid()
            pass
        if len(self.radio_button_dict.keys()) > amount_of_groups:
            for i in range(amount_of_groups,len(radio_button_dict.keys())):
                radio_button_dict[i].destroy()
                radio_button_dict.pop(i)
                self.group_dict.pop(i)

        elif len(self.radio_button_dict.keys()) < amount_of_groups:
            for i in range(len(self.radio_button_dict.keys()), amount_of_groups):
                radio_button_dict[i] = tk.Radiobutton(
                    button_frame,
                    text=f"recipe No. {i+1}",
                    variable=variable,
                    value=i,
                    bg=self.color_list[i+1]
                    )
                group_dict[i] = []
                radio_button_dict[i].grid()
        else:
            pass
    def set_new_user(self):
        #if self.user_name not in list(user_database.keys()):
        #    user_database[self.user_name] = {
        #          "cals": cals,
        #          "exclude_list": [],
        #          "recipes":{} }
        NewUserWindow(self)
    def confirm_menu(self):
        if not self.menu.status:
            self.send_message_to_comm("Error! Calculate a menu first!")
            pass
        if self.user_name.get() not in self.user_database:
            self.user_database[self.user_name.get()] = {
                "exclude_list": [],
                "recipes": {}}

        for key in self.menu.menu_dict.keys():
            recipe_name = list(self.menu.menu_dict[key].keys())[0]
            recipe_id = self.menu.reversed_recipe_dict[recipe_name]
            for subitem in key:
                recipe_date = subitem[0]
                if recipe_id not in self.user_database[self.user_name.get()]["recipes"].keys():
                    self.user_database[self.user_name.get()]["recipes"][recipe_id] = [recipe_date]
                else:
                    self.user_database[self.user_name.get()]["recipes"][recipe_id].append(recipe_date)
        with open(
                os.path.join(dirname, "data\\user_database.json"),
                'w') as file:
            json.dump(self.user_database, fp=file)
            file.close()

    def create_gui(self):
        # =============================================================================
        # entry for groups and frame for radiobuttons of groups:
        # =============================================================================
        radio_button_frame = tk.Frame(self.master)
        radio_button_frame.grid(column=1, row=1)
        radio_instruction_label = tk.Label(radio_button_frame, text = "Type in the \n amount of recipes you want \n to eat and hit enter!")
        radio_instruction_label.grid(row = 0)
        chosen_group_int = tk.IntVar()
        amount_of_groups_var = tk.IntVar()
        amount_of_groups_entry = tk.Entry(radio_button_frame, textvariable = amount_of_groups_var)
        amount_of_groups_entry.grid(row = 2)
        amount_of_groups_entry.bind('<Return>',
                                    lambda event: self.radio_create(amount_of_groups = amount_of_groups_var.get(),
                                                                     button_frame = radio_button_frame,
                                                                     radio_button_dict = self.radio_button_dict,
                                                                     variable=chosen_group_int,
                                                                    group_dict=self.group_dict))
        # =============================================================================
        # frame for calories, user name, diet, starting date
        # =============================================================================

        config_frame = tk.Frame(self.master)
        config_frame.grid(row = 1, column = 0)
        # enter the starting date

        self.date = tk.StringVar()
        self.date.set(str(datetime.today().strftime('%d.%m.%Y')))
        date_instruction_label = tk.Label(config_frame, text = "Type in the start date \n "
                                                               "of your menu as \n DD.MM.YYYY! \n "
                                                               "and hit Enter!")

        date_instruction_label.grid(row = 0)
        date_entry = tk.Entry(config_frame, textvariable = self.date)
        date_entry.grid(row = 1)
        # declare calories
        kcal = tk.IntVar()
        kcal.set(2500)
        kcal_label = tk.Label(config_frame, text = "Type in your daily \n calorie-goal:")
        kcal_label.grid(row = 2)
        kcal_entry = tk.Entry(config_frame, textvariable = kcal)
        kcal_entry.grid(row = 3)
        # chose a user
        user_instruction_label = tk.Label(config_frame, text = "Choose a user \n from database:")
        user_instruction_label.grid(row = 4)
        user_list = [name for name in user_database.keys()]
        self.user_name = tk.StringVar()
        self.user_name.set(user_list[0])
        user_dropdown = tk.OptionMenu(config_frame, self.user_name, *user_list)
        user_dropdown.grid(row = 5)
        # chose a diet
        diet_instruction_label = tk.Label(config_frame, text = "Choose a diet:")
        diet_instruction_label.grid(row = 6)
        diet_list = ["keto", "lchf"]
        chosen_diet = tk.StringVar()
        chosen_diet.set(diet_list[0])
        diet_dropdown = tk.OptionMenu(config_frame, chosen_diet, *diet_list)
        diet_dropdown.grid(row = 7)

        # =============================================================================
        # frame for mealslot-buttons and weekdays
        # =============================================================================
        DAYS = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7']
        MEALS = ['M1', 'M2', 'M3']
        MEALS_DAYS = [(day,meal) for day in DAYS for meal in MEALS]
        mealslot_frame = tk.Frame(self.master)
        mealslot_frame.grid(row=1, column = 3)
        # create the dates as column headers
        self.date_label_var_dict = {"D1":{},
                               "D2":{},
                               "D3":{},
                               "D4":{},
                               "D5":{},
                               "D6":{},
                               "D7":{}}
        i = 0
        for d in list(self.date_label_var_dict.keys()):
            self.date_label_var_dict[d]['date_var'] = tk.StringVar()
            self.date_label_var_dict[d]['day_var'] = tk.StringVar()
            self.date_label_var_dict[d]['date_label'] = tk.Label(mealslot_frame, textvariable = self.date_label_var_dict[d]['date_var'])
            self.date_label_var_dict[d]['day_label'] = tk.Label(mealslot_frame, textvariable = self.date_label_var_dict[d]['day_var'])
            self.date_label_var_dict[d]['date_label'].grid(row = 0, column = i)
            self.date_label_var_dict[d]['day_label'].grid(row = 1, column = i)
            i += 1
        date_entry.bind('<Return>', lambda event: self.compile_dates(start_date = self.date.get(),date_label_var=self.date_label_var_dict))
        # create the mealslot-buttons
        for r, i in zip(itertools.cycle(range(len(MEALS))), range(len(MEALS_DAYS))):
            self.tile_button_dict["button_" + str(MEALS_DAYS[i])] = tk.Button(
                mealslot_frame,
                width=20,
                height=10,
                wraplength=200,
                justify=tk.LEFT,
                relief=tk.RAISED,
                command=lambda j=i: self.meal_toggle(button=self.tile_button_dict["button_" + str(MEALS_DAYS[j])],
                                                     chosen_group_var = chosen_group_int,
                                                     color_list= self.color_list,
                                                     color_number= int(chosen_group_int.get() + 1),
                                                     index = j,
                                                     group_dict=self.group_dict,
                                                     meals_days_list=MEALS_DAYS)
            )
            col = int(i / 3)
            row = r + 3
            self.tile_button_dict["button_" + str(MEALS_DAYS[i])].grid(row=row, column=col)
        # comm-Frame
        self.comm_frame = tk.Frame(self.master)
        self.comm_frame.grid(row=2, column = 3)
        comm_label = tk.Label(self.comm_frame, textvariable = self.comm_var)
        comm_label.grid()
        # action frame and buttons
        self.action_frame = tk.Frame(self.master)
        self.action_frame.grid(row=2, column = 1)
        # button to start the recipe-calculation:
        self.menu = diet_sched.Menu()

        calculate_button = tk.Button(self.action_frame, text = "calculate menu!",
                                     bg = "red",
                                     command = lambda: threading.Thread(target = self.calculate_menu_parse_result,
                                                                args = [kcal,chosen_diet]).start())
        calculate_button.grid()
        # button to confirm & save menu
        confirm_button = tk.Button(self.action_frame, text = "confirm menu, save to user-database!",
                                   command = lambda: self.confirm_menu())
        confirm_button.grid()
        new_user_button = tk.Button(self.action_frame, text = "enter new user!",
                                    bg = "green",
                                    command = lambda: self.set_new_user())
        new_user_button.grid()
root = tk.Tk()
manager_gui = SchedulerWindow(root,user_database,food_database,dirname = dirname)
root.mainloop()
