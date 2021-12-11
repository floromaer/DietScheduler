import re
import xlsxwriter

def parse_menu_to_excel(filename,menu_dict,days_dict,results,goal_dict,food_database,reversed_ingredient_dict,grocery_dict):
    # making a temporary dict to map dates and columns in excel:
    temp_dates_dict = {}
    i=0
    for key in days_dict.keys():
        temp_dates_dict[days_dict[key]['date_var'].get()] = i
        i += 1
    temp_meals_dict = {}
    i = 0
    for meal in ['Breakfast', 'Lunch','Dinner']:
        temp_meals_dict[meal] = i
        i += 1
    # converting the menu-dict to dates and lunches
    for item in list(menu_dict.keys()):
        new_key = tuple(tuple(elem.replace('M1', 'Breakfast').replace('M2', 'Lunch').replace('M3', 'Dinner').replace('D1', days_dict['D1']['date_var'].get()).replace('D2',days_dict['D2']['date_var'].get()).replace('D3',days_dict['D3']['date_var'].get()).replace('D4',days_dict['D4']['date_var'].get()).replace('D5',days_dict['D5']['date_var'].get()).replace('D6',days_dict['D6']['date_var'].get()).replace('D7',days_dict['D7']['date_var'].get())
        for elem in tup) for tup in item)
        menu_dict[new_key] = menu_dict[item]
        menu_dict.pop(item)
    # putting it into an excel file:
    workbook = xlsxwriter.Workbook(filename)
    separator_format = workbook.add_format({'bg_color': '#000000'})
    # make worksheets
    menu_worksheet = workbook.add_worksheet(f"Menu - {days_dict['D1']['date_var'].get()} to {days_dict['D7']['date_var'].get()}") # for menu
    temp_worksheet_dict = {}
    global_groceries_worksheet = workbook.add_worksheet("your grocery list")
    for group in list(menu_dict.keys()):
        temp_worksheet_dict[group] = workbook.add_worksheet(f"{list(menu_dict[group].keys())[0][:31]}")
    # print the menu to menu-sheet
    col = 0
    for key in temp_dates_dict:
        menu_worksheet.write(0, col, key)
        col += 1
    row = 1
    for key in temp_meals_dict:
        menu_worksheet.write(row, 0, key)
        row += 1
    for group in menu_dict.keys():
        for slot in group:
            menu_worksheet.write(temp_meals_dict[slot[1]] + 1,temp_dates_dict[slot[0]] + 1, str(list(menu_dict[group].keys())[0]))
    for i in range(0,8):
        menu_worksheet.write(4,i,"",separator_format)
    menu_worksheet.write(5,0, "Results:")
    row = 5
    for metric in results.keys():
        menu_worksheet.write(row,1,str(f"{metric}: {round(results[metric],2)}"))
        row += 1
    menu_worksheet.write(5,2, "Goals:")
    row = 6
    for metric in goal_dict.keys():
        menu_worksheet.write(row,3,str(f"{metric}: {round(goal_dict[metric],2)}"))
        row += 1

    # writing the global grocery-list:
    row = 1
    col = 0
    global_groceries_worksheet.write(0,0,"Your grocery list:")
    for ingredient in grocery_dict.keys():
        ingredient_id = reversed_ingredient_dict[ingredient]
        global_groceries_worksheet.write(row, col, ingredient)
        global_groceries_worksheet.write(row, col + 1, str(grocery_dict[ingredient]))
        global_groceries_worksheet.write(row, col + 2, str(food_database['ingredients'][ingredient_id]['unit']))
        row += 1
    # writing the recipe-lists:
    for group in menu_dict.keys():
        temp_worksheet_dict[group].write(0,0, f"Ingredient list for {list(menu_dict[group].keys())[0]}:")
        row = 1
        col = 0
        for recipe in menu_dict[group].keys():
            for ingredient in menu_dict[group][recipe].keys():
                ingredient_id = reversed_ingredient_dict[ingredient]
                temp_worksheet_dict[group].write(row, col, ingredient)
                temp_worksheet_dict[group].write(row, col + 1, str(menu_dict[group][recipe][ingredient]))
                temp_worksheet_dict[group].write(row, col + 2, str(food_database['ingredients'][ingredient_id]['unit']))
                row += 1
    workbook.close()


