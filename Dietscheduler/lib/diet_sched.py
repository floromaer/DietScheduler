from pulp import *
from collections import defaultdict

import json
import math
import itertools
import datetime

class Menu:
    '''class for all menues to be built'''
    def __init__(self):
        self.status = False
    def calculate_menu(self,food_database,groups,exclude_list,kcal,diet,user_database,user,start_date):

        self.food_database = food_database
        self.groups = groups
        self.exclude_list = exclude_list
        self.reversed_ingredient_dict = {self.food_database['ingredients'][key]['name']: key for key in list(self.food_database['ingredients'].keys())}
        self.reversed_recipe_dict = {self.food_database['recipes'][key]['name']: key for key in list(self.food_database['recipes'].keys())}
        self.kcal = kcal
        self.diet = diet
        self.user_database = user_database
        self.user = user
        self.menu_dict = {}
        self.goal_dict = {}
        self.grocery_dict = defaultdict()
        self.result_dict = defaultdict()
        self.portions_dict = {}
        self.days_since_last_usage_dict = {}

        recipe_dictionary = self.food_database["recipes"]
        ingredient_dictionary = self.food_database["ingredients"]
        nutri_goals = {"keto": {
            "calorie": {
                "sense": 0,
                "goal": self.kcal},
            "protein": {
                "sense": 0,
                "goal": 0.20 * self.kcal},
            "fat": {
                "sense": 0,
                "goal": 0.60 * self.kcal},
            "carb": {
                "sense": 0,
                "goal": 0.10 * self.kcal}
        },
            "lchf": {
            "calorie": {
                "sense": 0,
                "goal": self.kcal},
            "protein": {
                "sense": 0,
                "goal": 0.40 * self.kcal},
            "fat": {
                "sense": 0,
                "goal": 0.40 * self.kcal},
            "carb": {
                "sense": 0,
                "goal": 0.20 * self.kcal}
        }}
        meal_goals = {
            "M1": {
                "calorie": 1 / 3 * self.kcal,
                "protein": 1 / 3 * nutri_goals[self.diet]["protein"]["goal"],
                "fat": 1 / 3 * nutri_goals[self.diet]["fat"]["goal"],
                "carb": 1 / 3 * nutri_goals[self.diet]["carb"]["goal"]},
            "M2": {
                "calorie": 1 / 3 * self.kcal,
                "protein": 1 / 3 * nutri_goals[self.diet]["protein"]["goal"],
                "fat": 1 / 3 * nutri_goals[self.diet]["fat"]["goal"],
                "carb": 1 / 3 * nutri_goals[self.diet]["carb"]["goal"]},
            "M3": {
                "calorie": 1 / 3 * self.kcal,
                "protein": 1 / 3 * nutri_goals[self.diet]["protein"]["goal"],
                "fat": 1 / 3 * nutri_goals[self.diet]["fat"]["goal"],
                "carb": 1 / 3 * nutri_goals[self.diet]["carb"]["goal"]},
        }
        # create a dict with recipe_id - timedelta bindings
        recipe_time_distance_dict = {}
        for recipe_id in food_database['recipes'].keys():
            if recipe_id in user_database[self.user]['recipes'].keys():

                latest_date_recipe = max([datetime.datetime.strptime(elem, '%d.%m.%Y') for elem in user_database[self.user]['recipes'][recipe_id]])

                delta = datetime.datetime.strptime(start_date,'%d.%m.%Y')-latest_date_recipe
                recipe_time_distance_dict[recipe_id] = int(delta.days)
                print(recipe_id, "last used on day:", latest_date_recipe, "distance:",int(delta.days))
            else:
                recipe_time_distance_dict[recipe_id] = 100
        for key in recipe_time_distance_dict.keys():
            print("recipe:",key, "\tDistance:",recipe_time_distance_dict[key])
        # retrieve a list of ingredients that should be included into the optimization
        opti_ingredient = [ingredient for ingredient in ingredient_dictionary if
                           ingredient_dictionary[ingredient]['optimization_include'] == True]
        # retrieve a list of ingredients that are distinct
        distinct_ingredient = [ingredient for ingredient in ingredient_dictionary if
                               ingredient_dictionary[ingredient]['distinct_ingredient'] == True]
        # multiply each ingredient and it's nutrient by standard serving and calories
        opti_ingredient_prop = defaultdict()
        for prop, fac in zip(["price", "calorie", "protein", "fat", "carb"], [1, 1, 4.1, 9.1, 4.1]):
            opti_ingredient_prop[prop] = dict()
            for recipe in recipe_dictionary:
                for ingredient in opti_ingredient:
                    if ingredient in recipe_dictionary[recipe]['ingredient']:
                        if prop == "price":
                            opti_ingredient_prop[prop][recipe, ingredient] = float(ingredient_dictionary[ingredient][prop]) * fac * \
                                                                         float(ingredient_dictionary[ingredient][
                                                                         "standard_qty"])
                        else:
                            opti_ingredient_prop[prop][recipe, ingredient] = float(ingredient_dictionary[ingredient][prop]) * fac * \
                                                                         float(ingredient_dictionary[ingredient][
                                                                         "standard_qty"])

        # map recipes and ingredients to one another
        recipe_ingredient_map = dict()
        for ingredient in opti_ingredient:
            for recipe in recipe_dictionary:
                if ingredient in recipe_dictionary[recipe]['ingredient']:
                    recipe_ingredient_map[recipe, ingredient] = {}
        # map number of protein sources and possible recipe-combinations:
        recipe_combinations_dict = dict()
        recipe_combinations = [i for i in itertools.combinations(recipe_dictionary.keys(), len(self.groups))]
        for comb in recipe_combinations:
            recipe_combinations_dict[comb] = len(
                set([recipe_dictionary[comb[i]]["protein_sources"][j] for i in range(len(comb)) for j in
                     range(len(recipe_dictionary[comb[i]]["protein_sources"]))]))
        print(recipe_combinations_dict)
        print(recipe_time_distance_dict)
        # map groups, recipes and ingredients
        groups_recipes_ingredient = [(group, recipe_ingredient) for group in self.groups for recipe_ingredient in
                                     recipe_ingredient_map]
        # map groups and recipes
        group_recipes = [(group, recipe) for group in self.groups for recipe in recipe_dictionary]

        # set up the lp-Variables:
        recipe_date_distance_lp = LpVariable.dict("Time_Distance", recipe_time_distance_dict, 0, cat = 'Continuous') # indicates the time-distance to last usage
        recipe_combination_indicator_lp = LpVariable.dicts("Combo_Chosen", recipe_combinations_dict, 0, cat='Binary')
        recipe_ingredient_amount_lp = LpVariable.dicts("Recipe_Ingredient_Amount", recipe_ingredient_map, 0,
                                                       cat='Continuous')  # amount ingredient, linked to recipe
        recipe_indicator_lp = LpVariable.dicts("Chosen", recipe_dictionary, 0,
                                               cat="Binary")  # indicates, if a recipe is chosen
        group_recipe_amount_lp = LpVariable.dicts("Amount", group_recipes, 0,
                                                  cat='Integer')  # amount of recipe in a group
        group_recipe_indicator_lp = LpVariable.dicts("Chosen", group_recipes, 0,
                                                     cat='Binary')  # indicates if a recipe is chosen in a group
        group_recipe_ingredient_amount_lp = LpVariable.dicts("Amount_Day", groups_recipes_ingredient, 0,
                                                             cat='Integer')  # group-recipe-ingredient-mapping, amount of which used in group
        # initialize Problem
        prob = LpProblem("Diet Problem", LpMinimize)
        prob += lpSum([opti_ingredient_prop['price'][r, i] *
                       recipe_ingredient_amount_lp[r, i]
                       for r in recipe_dictionary
                       for i in opti_ingredient
                       if i in recipe_dictionary[r]['ingredient']]) \
                - 1 * lpSum([recipe_combinations_dict[comb] * recipe_combination_indicator_lp[comb] for comb in
                             recipe_combinations_dict])\
                - 1000 * lpSum([recipe_time_distance_dict[recipe_id] * recipe_indicator_lp[recipe_id] for recipe_id in
               recipe_dictionary])
        print([recipe_time_distance_dict[recipe_id] * recipe_date_distance_lp[recipe_id] for recipe_id in
               recipe_dictionary],"\n",
              [recipe_combinations_dict[comb] * recipe_combination_indicator_lp[comb] for comb in
               recipe_combinations_dict]
              )

        #prob += lpSum([recipe_combination_indicator_lp[combo]*recipe_combinations_dict[combo] for combo in recipe_combinations_dict]) >= len(self.groups)
        # set up the constraints for the ingredients, link with amount of portions:
        for r in recipe_dictionary:
            for i in opti_ingredient:
                for group in self.groups:
                    if i in recipe_dictionary[r]['ingredient']:
                        prob += group_recipe_ingredient_amount_lp[group, (r, i)] >= group_recipe_amount_lp[group, r] * \
                                float(recipe_dictionary[r]['ingredient'][i]['constraints']['min'])
                        prob += group_recipe_ingredient_amount_lp[group, (r, i)] <= group_recipe_amount_lp[group, r] * \
                                float(recipe_dictionary[r]['ingredient'][i]['constraints']['max'])

        # set  up the constraints for nutrients per group:
        group_constraints = defaultdict()
        for group in self.groups:
            group_constraints[group] = defaultdict()
            for prop in ["calorie", "protein", "fat", "carb"]:
                if prop == "calorie":  # hard constraint for calories
                    prob += lpSum([opti_ingredient_prop[prop][r, i] * \
                                   group_recipe_ingredient_amount_lp[group, (r, i)] for r in recipe_dictionary for i in
                                   opti_ingredient if i in \
                                   recipe_dictionary[r]['ingredient']]) >= sum(
                        [meal_goals[slot[1]][prop] for slot in group]) - 100
                    prob += lpSum([opti_ingredient_prop[prop][r, i] * \
                                   group_recipe_ingredient_amount_lp[group, (r, i)] for r in recipe_dictionary for i in
                                   opti_ingredient if i in \
                                   recipe_dictionary[r]['ingredient']]) <= sum(
                        [meal_goals[slot[1]][prop] for slot in group]) + 100
                else:  # elastic constraint for the other nutrients
                    group_constraints[group][prop] = defaultdict()
                    group_constraints[group][prop]["rhs"] = sum([meal_goals[slot[1]][prop] for slot in group])
                    group_constraints[group][prop]["lhs"] = lpSum([opti_ingredient_prop[prop][r, i] *
                                                                   group_recipe_ingredient_amount_lp[group, (r, i)]
                                                                   for r in recipe_dictionary
                                                                   for i in opti_ingredient
                                                                   if i in recipe_dictionary[r]['ingredient']])
                    group_constraints[group][prop]["con"] = LpConstraint(group_constraints[group][prop]["lhs"],
                                                                         sense=nutri_goals[self.diet][prop]['sense'],
                                                                         name=str(group) + prop + "_con",
                                                                         rhs=group_constraints[group][prop]["rhs"])
                    group_constraints[group][prop]["elastic"] = group_constraints[group][prop][
                        "con"].makeElasticSubProblem(penalty=1, proportionFreeBound=0.00001)
                    prob.extend(group_constraints[group][prop]["elastic"])
        # recipes in exclude-list should be not be used
        for r in self.exclude_list:
            prob += lpSum([group_recipe_indicator_lp[g, r] for g in self.groups]) <= 0
        # recipes should only be used in fiting slots (M1 -> M1, M3 -> M3, M2 -> M2)
        for group in self.groups:
            for slot in ["M1", "M2", "M3"]:
                if slot in [meal_slot[1] for meal_slot in group]:
                    prob += lpSum([group_recipe_indicator_lp[group, r] for r in recipe_dictionary if
                                   not recipe_dictionary[r][slot]]) == 0

        # link group-recipe-indicator and recipe-amount
        for r in recipe_dictionary:
            for group in self.groups:
                prob += group_recipe_amount_lp[group, r] >= group_recipe_indicator_lp[group, r] * 0.1
                prob += group_recipe_amount_lp[group, r] <= group_recipe_indicator_lp[group, r] * 8

        # link the recipe-combinations and the recipes:
        for recipe in recipe_dictionary:
            prob += pulp.lpSum([group_recipe_amount_lp[group, recipe] for group in self.groups]) >= recipe_indicator_lp[ \
                recipe] * 0.1
            prob += pulp.lpSum([group_recipe_amount_lp[group, recipe] for group in self.groups]) <= recipe_indicator_lp[ \
                recipe] * 8

        for recipe in recipe_dictionary:
            for ingredient in opti_ingredient:
                if ingredient in recipe_dictionary[recipe]["ingredient"]:
                    prob += lpSum([group_recipe_ingredient_amount_lp[group,(recipe,ingredient)] for group in self.groups]) == recipe_ingredient_amount_lp[recipe,ingredient]

        # link the combo-indicator and the recipe:
        for combo in recipe_combinations_dict:
            prob += lpSum([recipe_indicator_lp[recipe] for recipe in combo]) / len(self.groups) >= \
                    recipe_combination_indicator_lp[combo]
        # no idea why this has to be included, but it's important asf
        prob += pulp.lpSum([recipe_combination_indicator_lp[combo] for combo in recipe_combinations]) == 1
        # every group has to have one recipe
        for g in self.groups:
             prob += lpSum([group_recipe_indicator_lp[g, r] for r in recipe_dictionary]) == 1
        # every recipe in one group at max
        for r in recipe_dictionary:
            prob += lpSum([group_recipe_indicator_lp[g, r] for g in self.groups]) <= 1

        prob.solve(PULP_CBC_CMD(msg=True,maxSeconds=180))
        if LpStatus[prob.status] == 'Optimal':
            self.status = True
        else:
            self.status = False
        obj = value(prob.objective)
        recipe_amount_inv_map = {str(v): k for k, v in group_recipe_amount_lp.items()}
        ingredients_inv_map = {str(v): k for k, v in recipe_ingredient_amount_lp.items()}
        day_meal_inv_map = {str(v): k for k, v in group_recipe_ingredient_amount_lp.items()}

        for prop in ["price", "calorie", "protein", "fat", "carb"]:
            self.result_dict[prop] = 0
        for v in prob.variables():
            if v.value() > 0:
                if ("M1" or "M2" or "M3") and "Amount_Day" in str(v):
                    group = day_meal_inv_map[v.name][0]
                    result = day_meal_inv_map[v.name][1]
                    recipe = self.food_database['recipes'][result[0]]['name']
                    ingredient = self.food_database['ingredients'][result[1]]['name']
                    if group not in self.menu_dict.keys():
                        self.menu_dict[group] = {}

                    if recipe not in self.menu_dict[group]:
                        self.menu_dict[group][recipe] = {}
                    self.menu_dict[group][recipe][ingredient] = v.value()
                if "Amount_((" in str(v):
                    recipe_id = recipe_amount_inv_map[v.name][1]
                    self.portions_dict[recipe_id] = v.value()
                if "Recipe_Ingredient_Amount" in str(v):
                    if self.food_database['ingredients'][ingredients_inv_map[v.name][1]]['name'] in self.grocery_dict.keys():
                        self.grocery_dict[self.food_database['ingredients'][ingredients_inv_map[v.name][1]]['name']] += v.value()
                    else:
                        self.grocery_dict[self.food_database['ingredients'][ingredients_inv_map[v.name][1]]['name']] = v.value()
                    for prop in ["price","calorie", "protein", "fat", "carb"]:
                        self.result_dict[prop] += round(opti_ingredient_prop[prop][ingredients_inv_map[v.name]] * (v.value()), 3)
        self.recipe_list = []
        for key in self.portions_dict.keys():
            parsed_recipe = self.food_database['recipes'][key]['name']
            self.recipe_list.append(parsed_recipe)
            for ingredient in self.food_database['recipes'][key]['ingredient'].keys():
                parsed_ingredient = self.food_database['ingredients'][ingredient]['name']

                for group in self.menu_dict.keys():
                    if parsed_recipe in list(self.menu_dict[group].keys()):
                        if parsed_ingredient not in self.menu_dict[group][parsed_recipe]:
                            self.menu_dict[group][parsed_recipe][parsed_ingredient] = self.food_database['recipes'][key]['ingredient'][ingredient]['qty'] * self.portions_dict[key]
                        if parsed_ingredient not in list(self.grocery_dict.keys()):
                            self.grocery_dict[parsed_ingredient] = self.food_database['recipes'][key]['ingredient'][ingredient]['qty'] * self.portions_dict[key]
        for group in groups:
            for slot in group:
                for key in meal_goals[slot[1]].keys():
                    if key not in self.goal_dict:
                        self.goal_dict[key] = 0
                        self.goal_dict[key] += meal_goals[slot[1]][key]
                    else:
                        self.goal_dict[key] += meal_goals[slot[1]][key]

with open("C:\\Users\\mrvng\\Desktop\\Resilio_Sync\\Arbeit\\R-Weiterbildung\\Python\\recipe_manager\\data\\recipe_ingredient_database.json") as file:
    food_database = json.load(file)
    file.close()
with open(
        "C:\\Users\\mrvng\\Desktop\\Resilio_Sync\\Arbeit\\R-Weiterbildung\\Python\\diet_sched\\data\\user_database.json") as file:
    user_database = json.load(file)
    file.close()
#groups = [(('Monday','M2'), ('Tuesday','M2')), (('Monday','M3'), ('Tuesday','M3')), (('Wednesday','M2'),)]
#new_menu = Menu()
#new_menu.calculate_menu(food_database=food_database,groups=groups,exclude_list = [],kcal = 2700, diet = "keto",
#                        user_database=user_database,user = "Test_Gerhard",start_date=)
