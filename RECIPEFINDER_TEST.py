import kivy
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
import sqlite3
import requests
import logging
import webbrowser
from kivy.uix.spinner import Spinner
from kivymd.app import MDApp
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
import os
from kivy.uix.widget import Widget
from BaseScreen import BaseScreen 
from kivy.clock import Clock
from spellchecker import SpellChecker
import urllib.parse
from NutrientRecommendation import NutrientRecommendation
from security_utils import hash_password, check_password


kivy.require('2.1.0')

app_id = "b0e9c0d6"
app_key = "04ce4e0e4d17b4721882d3c610cd89e6"

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def create_tables():
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()

    # Create the users table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT NOT NULL,
                        email TEXT NOT NULL,
                        password TEXT NOT NULL,
                        calories REAL,
                        carbs REAL,
                        protein REAL,
                        fats REAL,
                        dietary_preference TEXT
                    )''')

    # Check and add missing columns to the users table if they don't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN calories REAL")
    except sqlite3.OperationalError:
        pass  # Ignore the error if the column already exists

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN carbs REAL")
    except sqlite3.OperationalError:
        pass  # Ignore the error if the column already exists

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN protein REAL")
    except sqlite3.OperationalError:
        pass  # Ignore the error if the column already exists

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN fats REAL")
    except sqlite3.OperationalError:
        pass  # Ignore the error if the column already exists

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN dietary_preference TEXT")
    except sqlite3.OperationalError:
        pass  # Ignore the error if the column already exists

    # Create the saved_recipes table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS saved_recipes (
                        user_id INTEGER,
                        recipe_name TEXT,
                        recipe_url TEXT,
                        recipe_ingredients TEXT,
                        recipe_source TEXT,
                        UNIQUE(user_id, recipe_name)
                    )''')

    conn.commit()
    conn.close()


def sign_up(username, email, password):
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
    conn.commit()
    conn.close()

def login(username, password):
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

def is_recipe_saved(user_id, recipe_name):
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM saved_recipes WHERE user_id = ? AND recipe_name = ?", (user_id, recipe_name))
    result = cursor.fetchone()
    conn.close()
    return result is not None


class RecipeDetailsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(RecipeDetailsScreen, self).__init__(**kwargs)

        self.container = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.root_layout.add_widget(self.container)

        self.recipe_title = Label(text='', size_hint=(1, 0.1), font_size='35sp', color=(0, 0, 0, 1))
        self.container.add_widget(self.recipe_title)

        self.scroll_view = ScrollView(size_hint=(1, 0.7))
        self.recipe_details = Label(text='', size_hint_y=None, color=(0, 0, 0, 1), font_size='24sp')
        self.recipe_details.bind(texture_size=self.recipe_details.setter('size'))
        self.scroll_view.add_widget(self.recipe_details)
        self.container.add_widget(self.scroll_view)

        self.button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        self.recipe_url_button = Button(text='View Full Recipe', size_hint=(0.8, 1))
        self.recipe_url_button.bind(on_press=self.open_recipe_url)
        self.button_layout.add_widget(self.recipe_url_button)

        self.save_recipe_button = MDIconButton(
            icon="cards-heart-outline",
            size_hint=(None, None),
            icon_size="48sp"
        )
        self.save_recipe_button.bind(on_press=self.toggle_save_recipe)
        self.button_layout.add_widget(self.save_recipe_button)

        self.container.add_widget(self.button_layout)

        self.back_button = Button(text='Back', size_hint=(1, 0.1))
        self.back_button.bind(on_press=self.go_back)
        self.container.add_widget(self.back_button)

    def display_recipe(self, recipe):
        try:
            self.recipe = recipe
            self.recipe_title.text = recipe['label']
            self.recipe_details.text = f"Source: {recipe['source']}\n\nIngredients:\n" + \
                                       '\n'.join(recipe['ingredientLines'])
            self.recipe_url_button.recipe_url = recipe['url']
            app = MDApp.get_running_app()
            if is_recipe_saved(app.user_id, recipe['label']):
                self.save_recipe_button.icon = "cards-heart"
            else:
                self.save_recipe_button.icon = "cards-heart-outline"
        except Exception as e:
            logging.error(f"Error in display_recipe: {e}")
            popup = Popup(title='Error', content=Label(text=f"Error: {e}"), size_hint=(None, None), size=(400, 200))
            popup.open()

    def open_recipe_url(self, instance):
        webbrowser.open(instance.recipe_url)

    def toggle_save_recipe(self, instance):
        app = MDApp.get_running_app()
        user_id = app.user_id
        if user_id is None:
            popup = Popup(title='Error', content=Label(text='You must be logged in to save recipes.'), size_hint=(None, None), size=(400, 200))
            popup.open()
            app.previous_screen = 'details'
            app.next_action = 'save_recipe'
            app.next_recipe = self.recipe
            app.screen_manager.current = 'login'
            return

        if self.save_recipe_button.icon == "cards-heart-outline":
            self.save_recipe(user_id)
        else:
            self.unsave_recipe(user_id)

    def save_recipe(self, user_id):
        try:
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO saved_recipes (user_id, recipe_name, recipe_url, recipe_ingredients, recipe_source) VALUES (?, ?, ?, ?, ?)",
                           (user_id, self.recipe['label'], self.recipe['url'], '\n'.join(self.recipe['ingredientLines']), self.recipe['source']))
            conn.commit()
            self.save_recipe_button.icon = "cards-heart"
            popup = Popup(title='Success', content=Label(text='Recipe saved successfully!'), size_hint=(None, None), size=(400, 200))
            popup.open()
            conn.close()
        except sqlite3.IntegrityError:
            popup = Popup(title='Error', content=Label(text='Recipe already saved.'), size_hint=(None, None), size=(400, 200))
            popup.open()
        except Exception as e:
            logging.error(f"Error in save_recipe: {e}")
            popup = Popup(title='Error', content=Label(text=f"Error: {e}"), size_hint=(None, None), size=(400, 200))
            popup.open()
        finally:
            conn.close()

        app = MDApp.get_running_app()
        if app and app.previous_screen == 'saved_recipes':
            app.saved_recipes_screen.display_saved_recipes(user_id)

    def unsave_recipe(self, user_id):
        try:
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM saved_recipes WHERE user_id = ? AND recipe_name = ?", (user_id, self.recipe['label']))
            conn.commit()
            conn.close()
            self.save_recipe_button.icon = "cards-heart-outline"
            popup = Popup(title='Success', content=Label(text='Recipe unsaved successfully!'), size_hint=(None, None), size=(400, 200))
            popup.open()
        except Exception as e:
            logging.error(f"Error in unsave_recipe: {e}")
            popup = Popup(title='Error', content=Label(text=f"Error: {e}"), size_hint=(None, None), size=(400, 200))
            popup.open()

        app = MDApp.get_running_app()
        if app and app.previous_screen == 'saved_recipes':
            app.saved_recipes_screen.display_saved_recipes(user_id)

    def go_back(self, instance):
        app = MDApp.get_running_app()
        if app.previous_screen == 'saved_recipes':
            app.screen_manager.current = 'saved_recipes'
        else:
            app.screen_manager.current = 'main'
        app.previous_screen = None
        logging.debug(f"Navigated back to {app.screen_manager.current} from RecipeDetailsScreen")


class RecipeFinderApp(MDApp):
    def build(self):
        # Print current working directory for debugging
        print(f"Current working directory: {os.getcwd()}")

        self.user_id = None  # Initialize user_id to None
        self.next_action = None  # Initialize next_action to None
        self.next_recipe = None  # Initialize next_recipe to None
        self.previous_screen = None  # Initialize previous_screen to None

        # Create the root FloatLayout
        root = FloatLayout()

        # Absolute path to the image
        image_path = '/Users/kamila/Documents/MacBook Air/GitHub/kamila/IA_Recipe_KIVY/sqlsetup/images/food.JPEG'

        # Check if the image exists
        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
        else:
            print(f"Image found: {image_path}")

        # Add the background image
        try:
            background = Image(source=image_path,
                               allow_stretch=False,
                               keep_ratio=False,
                               size_hint=(1, 1),
                               pos_hint={'center_x': 0.5, 'center_y': 0.5})
            root.add_widget(background)
            print("Background image added successfully.")
        except Exception as e:
            print(f"Failed to add background image: {e}")

        # Create the screen manager
        self.screen_manager = ScreenManager()

        # Add all the screens
        self.login_screen = LoginScreen(name='login')
        self.signup_screen = SignupScreen(name='signup')
        self.main_screen = MainScreen(name='main')
        self.recipe_details_screen = RecipeDetailsScreen(name='details')
        self.account_screen = AccountScreen(name='account')
        self.saved_recipes_screen = SavedRecipesScreen(name='saved_recipes')
        self.nutrient_recommendation_screen = NutrientRecommendationScreen(name='nutrient_recommendation')

        # Add existing screens to the screen manager
        self.screen_manager.add_widget(self.login_screen)
        self.screen_manager.add_widget(self.signup_screen)
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.recipe_details_screen)
        self.screen_manager.add_widget(self.account_screen)
        self.screen_manager.add_widget(self.saved_recipes_screen)
        self.screen_manager.add_widget(self.nutrient_recommendation_screen)

        # Add the CreateRecipeScreen
        self.main_screen = MainScreen(name='main')
        self.create_recipe_screen = CreateRecipeScreen(name='create_recipe')

        # Add each screen to the manager
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.add_widget(self.create_recipe_screen)

        # Set the initial screen
        self.screen_manager.current = 'main'

        return self.screen_manager

class LoginScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.container = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.root_layout.add_widget(self.container)

        self.username_input = TextInput(hint_text='Username', multiline=False)
        self.password_input = TextInput(hint_text='Password', multiline=False, password=True)
        self.container.add_widget(self.username_input)
        self.container.add_widget(self.password_input)
        
        login_button = Button(text='Login')
        login_button.bind(on_press=self.login)
        self.container.add_widget(login_button)
        
        signup_button = Button(text='Sign Up')
        signup_button.bind(on_press=self.go_to_signup)
        self.container.add_widget(signup_button)
        
        go_back_button = Button(text='Go Back')
        go_back_button.bind(on_press=self.go_back)
        self.container.add_widget(go_back_button)

    def login(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        user = login(username, password)
        if user:
            app = MDApp.get_running_app()
            app.user_id = user[0]
            if app.next_action == 'save_recipe':
                app.recipe_details_screen.display_recipe(app.next_recipe)
                app.next_action = None
                app.next_recipe = None
                app.screen_manager.current = 'details'
            else:
                app.screen_manager.current = 'main'
        else:
            popup = Popup(title='Login Failed', content=Label(text='Invalid username or password'), size_hint=(None, None), size=(400, 200))
            popup.open()

    def go_to_signup(self, instance):
        MDApp.get_running_app().screen_manager.current = 'signup'
    
    def go_back(self, instance):
        MDApp.get_running_app().screen_manager.current = 'main'


class SignupScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(SignupScreen, self).__init__(**kwargs)

        # Create the container layout for the UI components
        self.container = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.root_layout.add_widget(self.container)
        
        self.username_input = TextInput(hint_text='Username', multiline=False)
        self.email_input = TextInput(hint_text='Email', multiline=False)
        self.password_input = TextInput(hint_text='Password', multiline=False, password=True)
        self.confirm_password_input = TextInput(hint_text='Confirm Password', multiline=False, password=True)
        
        self.container.add_widget(self.username_input)
        self.container.add_widget(self.email_input)
        self.container.add_widget(self.password_input)
        self.container.add_widget(self.confirm_password_input)
        
        signup_button = Button(text='Sign Up')
        signup_button.bind(on_press=self.sign_up)
        self.container.add_widget(signup_button)
        
        go_back_button = Button(text='Go Back')
        go_back_button.bind(on_press=self.go_back)
        self.container.add_widget(go_back_button)


    def sign_up(self, instance):
        username = self.username_input.text
        email = self.email_input.text
        password = self.password_input.text
        confirm_password = self.confirm_password_input.text
        
        if password == confirm_password:
            sign_up(username, email, password)
            app = MDApp.get_running_app()
            app.screen_manager.current = 'login'
        else:
            popup = Popup(title='Sign Up Failed', content=Label(text='Passwords do not match'), size_hint=(None, None), size=(400, 200))
            popup.open()
    
    def go_back(self, instance):
        App.get_running_app().screen_manager.current = 'main'


class MainScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)

        # Initialize the spell checker
        self.spell = SpellChecker()

        image_path = '/Users/kamila/Documents/MacBook Air/GitHub/kamila/IA_Recipe_KIVY/sqlsetup/logo/logo.png'
        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
        else:
            print(f"Image found: {image_path}")

        # Add the logo image
        self.logo = Image(source=image_path,
                          allow_stretch=False,
                          keep_ratio=True,
                          size_hint=(None, None),
                          height=150, width=400,
                          pos_hint={'center_x': 0.5, 'top': 1})
        self.root_layout.add_widget(self.logo)

        # Create the container layout for the UI components
        self.container = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.4})
        self.root_layout.add_widget(self.container)

        # Add existing UI components into the container
        self.ingredient_input = TextInput(hint_text='Enter ingredients separated by commas', size_hint=(1, 0.1), multiline=False)
        self.ingredient_input.bind(on_text_validate=self.on_word_complete)
        self.ingredient_input.bind(text=self.on_text_change)
        self.container.add_widget(self.ingredient_input)

        self.create_recipe_button = Button(text='Create My Recipe', size_hint=(1, 0.1))
        self.create_recipe_button.bind(on_press=self.go_to_create_recipe)
        self.container.add_widget(self.create_recipe_button)


        self.create_recipe_button = Button(text='Create My Recipe', size_hint=(1, 0.1))
        self.create_recipe_button.bind(on_press=self.go_to_create_recipe)
        self.container.add_widget(self.create_recipe_button)


        filter_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)

        self.cuisine_type_spinner = Spinner(
            text='Cuisine Type',
            values=('American', 'Asian', 'Italian', 'Mexican', 'Middle Eastern'),
            size_hint=(1/3, 1)
        )
        filter_layout.add_widget(self.cuisine_type_spinner)

        self.cooking_time_spinner = Spinner(
            text='Cooking Time',
            values=('< 30 minutes', '30-60 minutes', '> 60 minutes'),
            size_hint=(1/3, 1)
        )
        filter_layout.add_widget(self.cooking_time_spinner)

        self.meal_type_spinner = Spinner(
            text='Meal Type',
            values=('Breakfast', 'Lunch', 'Dinner', 'Snack'),
            size_hint=(1/3, 1)
        )
        filter_layout.add_widget(self.meal_type_spinner)

        self.container.add_widget(filter_layout)

        self.search_button = Button(text='Find Recipes', size_hint=(1, 0.1))
        self.search_button.bind(on_press=self.search_recipes)
        self.container.add_widget(self.search_button)

        self.reset_filters_button = Button(text='Reset Filters', size_hint=(1, 0.1))
        self.reset_filters_button.bind(on_press=self.reset_filters)
        self.container.add_widget(self.reset_filters_button)

        self.reset_ingredients_button = Button(text='Reset Ingredients', size_hint=(1, 0.1))
        self.reset_ingredients_button.bind(on_press=self.reset_ingredients)
        self.container.add_widget(self.reset_ingredients_button)

        # Create a layout for the top right buttons (account and saved recipes)
        top_right_layout = BoxLayout(orientation='horizontal', size_hint=(None, None), pos_hint={"right": 0.96, "top": 0.95}, padding=(10, 10, 10, 10))

        self.saved_recipes_button = MDIconButton(
            icon="cards-heart",
            size_hint=(None, None),
            icon_size="48sp"
        )
        self.saved_recipes_button.bind(on_press=self.go_to_saved_recipes)
        top_right_layout.add_widget(self.saved_recipes_button)

        self.account_button = MDIconButton(
            icon="account",
            size_hint=(None, None),
            icon_size="48sp"
        )
        self.account_button.bind(on_press=self.go_to_account)
        top_right_layout.add_widget(self.account_button)

        self.root_layout.add_widget(top_right_layout)

        self.scroll_view = ScrollView(size_hint=(1, 0.7))
        self.results_layout = GridLayout(cols=1, size_hint_y=None)
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        self.scroll_view.add_widget(self.results_layout)

        self.container.add_widget(self.scroll_view)

    def on_text_change(self, instance, value):
        if value and value[-1] in [' ', ',']:
            self.auto_correct_last_word()

    def auto_correct_last_word(self):
        text = self.ingredient_input.text.strip()
        if not text:
            return

        ingredients = text.split(',')

        corrected_ingredients = []
        for ingredient in ingredients:
            words = ingredient.split()
            corrected_words = []
            for word in words:
                word = word.strip().lower()
                if len(word) > 3 and word not in self.spell:
                    corrected_word = self.spell.correction(word)
                    corrected_words.append(corrected_word)
                else:
                    corrected_words.append(word)
            corrected_ingredients.append(" ".join(corrected_words))

        corrected_text = ', '.join(corrected_ingredients)
        if corrected_text != text:
            self.ingredient_input.text = corrected_text
            self.ingredient_input.cursor = (len(corrected_text), 0)

    def on_word_complete(self, instance):
        self.auto_correct_last_word()

    def search_recipes(self, instance):
        ingredient_names = self.ingredient_input.text.strip()
        if not ingredient_names:
            self.results_layout.clear_widgets()
            self.results_layout.add_widget(Label(text='Please enter some ingredients.', color=(0, 0, 0, 1)))
            return

        cuisine_type = self.cuisine_type_spinner.text if self.cuisine_type_spinner.text != 'Cuisine Type' else ''
        cooking_time = self.cooking_time_spinner.text if self.cooking_time_spinner.text != 'Cooking Time' else ''
        meal_type = self.meal_type_spinner.text if self.meal_type_spinner.text != 'Meal Type' else ''

        self.results_layout.clear_widgets()
        self.results_layout.add_widget(Label(text='Searching...', color=(0, 0, 0, 1)))

        ingredients = [ingredient.strip() for ingredient in ingredient_names.split(',')]
        all_recipes = {}

        for ingredient in ingredients:
            query = urllib.parse.quote(ingredient)
            url = f"https://api.edamam.com/search?q={query}&app_id={app_id}&app_key={app_key}&from=0&to=10"

            if cuisine_type:
                url += f"&cuisineType={urllib.parse.quote(cuisine_type.lower())}"
            if cooking_time:
                if cooking_time == '< 30 minutes':
                    url += "&time=0-30"
                elif cooking_time == '30-60 minutes':
                    url += "&time=30-60"
                elif cooking_time == '> 60 minutes':
                    url += "&time=60%2B"
            if meal_type:
                url += f"&mealType={urllib.parse.quote(meal_type.lower())}"

            try:
                response = requests.get(url)
                response.raise_for_status()
                recipes = response.json().get('hits', [])

                for recipe_hit in recipes:
                    recipe = recipe_hit['recipe']
                    recipe_url = recipe['url']
                    recipe_title = recipe.get('label', 'Unknown Title')
                    recipe_description = recipe.get('source', 'Unknown Source')
                    ingredient_lines = recipe.get('ingredientLines', [])

                    # Fetch nutritional data for each recipe by ingredients
                    nutrition_data = self.fetch_nutrition_by_ingredients(ingredient_lines)
                    
                    # If nutrition data is available, calculate per-serving values
                    if nutrition_data:
                        servings = recipe.get('yield', 1)  # Default to 1 serving if not specified
                        calories = nutrition_data.get('ENERC_KCAL', {}).get('quantity', 0) / servings
                        fat = nutrition_data.get('FAT', {}).get('quantity', 0) / servings
                        protein = nutrition_data.get('PROCNT', {}).get('quantity', 0) / servings
                        carbs = nutrition_data.get('CHOCDF', {}).get('quantity', 0) / servings

                        # Store the nutritional data
                        recipe['nutrition'] = {
                            'calories': calories,
                            'fat': fat,
                            'protein': protein,
                            'carbs': carbs
                        }

                    if recipe_url not in all_recipes:
                        all_recipes[recipe_url] = {
                            "title": recipe_title,
                            "description": recipe_description,
                            "url": recipe_url,
                            "ingredients": set(ingredient_lines),
                            "nutrition": recipe.get('nutrition', {}),  # Nutrition data for display
                            "match_count": 0
                        }

                    all_recipes[recipe_url]["match_count"] += len(set(ingredients) & all_recipes[recipe_url]["ingredients"])

            except requests.exceptions.RequestException as e:
                self.results_layout.clear_widgets()
                self.results_layout.add_widget(Label(text=f'Error: {str(e)}', color=(0, 0, 0, 1)))
                logging.error(f"Request Exception: {str(e)}")
                return

        sorted_recipes = sorted(all_recipes.values(), key=lambda r: r["match_count"], reverse=True)

        self.results_layout.clear_widgets()

        if sorted_recipes:
            for recipe in sorted_recipes:
                recipe_button = Button(
                    text=f"{recipe['title']}: {recipe['description']}",
                    size_hint_y=None,
                    height=40
                )
                recipe_button.bind(on_press=lambda instance, r=recipe: self.view_recipe_details(r))
                self.results_layout.add_widget(recipe_button)
        else:
            self.results_layout.add_widget(Label(text='No recipes found for these ingredients.', color=(0, 0, 0, 1)))

    # Add the missing method here
    def fetch_nutrition_by_ingredients(self, ingredients):
        """Fetch nutritional data based on the provided ingredients."""
        try:
            app_id = "b0e9c0d6"
            app_key = "04ce4e0e4d17b4721882d3c610cd89e6"
            url = f"https://api.edamam.com/api/nutrition-details?app_id={app_id}&app_key={app_key}"

            headers = {"Content-Type": "application/json"}
            data = {"ingr": ingredients}

            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            return response.json().get('totalNutrients', {})
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching nutritional data: {e}")
            return {}

        def fetch_nutrition_by_ingredients(self, ingredients):
            try:
                url = f"https://api.edamam.com/api/nutrition-details?app_id={app_id}&app_key={app_key}"
        
        # Prepare the request payload
                payload = {
                    "title": "Recipe Nutrition",
                    "ingr": ingredients  # List of ingredients
                }

        # Make a POST request to Edamam Nutrition Analysis API
                response = requests.post(url, json=payload)
                response.raise_for_status()  # Raise exception for any HTTP errors
        
        # Get the nutrition data from the response
                nutrition_data = response.json().get('totalNutrients', {})

                return nutrition_data  # Return the nutrition data fetched from the API
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching nutritional data: {e}")
                return None

    def view_recipe_details(self, recipe):
        app = MDApp.get_running_app()
        app.previous_screen = app.screen_manager.current

        # Log the recipe data being passed
        logging.debug(f"Viewing recipe details: {recipe}")

        # Ensure the recipe data is correctly passed to the details screen
        app.recipe_details_screen.display_recipe(recipe)

        # Switch to the RecipeDetailsScreen
        app.screen_manager.current = 'details'


    def reset_filters(self, instance):
        self.cuisine_type_spinner.text = 'Cuisine Type'
        self.cooking_time_spinner.text = 'Cooking Time'
        self.meal_type_spinner.text = 'Meal Type'

    def reset_ingredients(self, instance):
        self.ingredient_input.text = ''

    def go_to_saved_recipes(self, instance):
        app = MDApp.get_running_app()
        if app.user_id is None:
            popup = Popup(title='Error', content=Label(text='You must be logged in to view saved recipes.'), size_hint=(None, None), size=(400, 200))
            popup.open()
        else:
            app.saved_recipes_screen.display_saved_recipes(app.user_id)
            app.screen_manager.current = 'saved_recipes'

    def go_to_account(self, instance):
        app = MDApp.get_running_app()
        if app.user_id is None:
            app.screen_manager.current = 'login'
        else:
            app.account_screen.load_account_details()
            app.screen_manager.current = 'account'


    def go_to_create_recipe(self, instance):
        app = MDApp.get_running_app()
        app.screen_manager.current = 'create_recipe'


class CreateRecipeScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(CreateRecipeScreen, self).__init__(**kwargs)

        # Container for UI components
        self.container = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.root_layout.add_widget(self.container)

        # Recipe Name Input
        self.recipe_name_input = TextInput(hint_text='Enter recipe name', size_hint=(1, None), height=40)
        self.container.add_widget(self.recipe_name_input)

        # Ingredient layout container
        self.ingredients_layout = BoxLayout(orientation='vertical', size_hint=(1, None))
        self.ingredients_layout.bind(minimum_height=self.ingredients_layout.setter('height'))
        self.scroll_view = ScrollView(size_hint=(1, 0.5))
        self.scroll_view.add_widget(self.ingredients_layout)
        self.container.add_widget(self.scroll_view)

        # Initialize a list to keep track of the ingredient input fields
        self.ingredient_inputs = []

        # Button to add an ingredient row
        self.add_ingredient_button = Button(text='Add Ingredient', size_hint=(1, None), height=40)
        self.add_ingredient_button.bind(on_press=self.add_ingredient_row)
        self.container.add_widget(self.add_ingredient_button)

        # Steps Input
        self.steps_input = TextInput(hint_text='Enter steps', size_hint=(1, None), height=120, multiline=True)
        self.container.add_widget(self.steps_input)

        # Button to save the recipe
        self.save_recipe_button = Button(text='Save Recipe', size_hint=(1, None), height=40)
        self.save_recipe_button.bind(on_press=self.save_recipe)
        self.container.add_widget(self.save_recipe_button)

        # Label to display success message
        self.success_label = Label(text='', size_hint=(1, None), height=40)
        self.container.add_widget(self.success_label)

        # Label to display nutritional information
        self.nutrition_label = Label(text='Nutritional Info will appear here', size_hint=(1, None), height=40)
        self.container.add_widget(self.nutrition_label)

    def add_ingredient_row(self, instance):
        """Add a new row for ingredient input."""
        ingredient_row = BoxLayout(orientation='horizontal', size_hint=(1, None), height=40)

        # Ingredient name input
        ingredient_input = TextInput(hint_text='Ingredient', size_hint=(0.6, None), height=40)
        ingredient_row.add_widget(ingredient_input)

        # Ingredient quantity input with Spinner
        quantity_spinner = Spinner(
            text='1',  # Default value
            values=('1', '2', '3', '4', '5', '6', '7', '8', '9', '10'),  # Values from 1 to 10
            size_hint=(0.4, None),  # Size to fit in the layout
            height=40
        )
        ingredient_row.add_widget(quantity_spinner)

        # Add the row to the layout and store references to inputs
        self.ingredients_layout.add_widget(ingredient_row)
        self.ingredient_inputs.append((ingredient_input, quantity_spinner))

    def save_recipe(self, instance):
        """Save the recipe to the database and display a success message."""
        # Fetch ingredients from the dynamically generated input fields
        ingredients = [
            f"{quantity_spinner.text} {ingredient_input.text}".strip()
            for ingredient_input, quantity_spinner in self.ingredient_inputs if ingredient_input.text
        ]
        recipe_name = self.recipe_name_input.text
        steps = self.steps_input.text

        # Simulate saving to the database with a unique user ID
        app = MDApp.get_running_app()
        user_id = app.user_id

        # Ensure all required fields are filled
        if not recipe_name or not ingredients or not steps:
            self.success_label.text = "Please fill in all the fields."
            return

        # Call function to save recipe to the database
        success = self.save_recipe_to_database(recipe_name, ingredients, steps, user_id)

        if success:
            # Display success message
            self.success_label.text = "Recipe has been successfully created and saved."
            # Clear input fields after saving
            self.clear_fields()
        else:
            self.success_label.text = "Failed to save the recipe. Please try again."

        # Update the "My Recipes" section in AccountScreen
        app.account_screen.update_my_recipes()

    def save_recipe_to_database(self, recipe_name, ingredients, steps, user_id):
        """Function to save the recipe to the database."""
        try:
            # Example of how to save the recipe to the database
            # You can replace this with your actual database logic
            # Assuming you have a function `save_to_database()` that handles database operations
            recipe_data = {
                "user_id": user_id,
                "recipe_name": recipe_name,
                "ingredients": ingredients,
                "steps": steps
            }
            # Here you save to the database (e.g., using SQLAlchemy, SQLite, etc.)
            save_to_database(recipe_data)
            return True
        except Exception as e:
            logging.error(f"Error saving recipe: {e}")
            return False

    def clear_fields(self):
        """Clear all input fields after saving the recipe."""
        self.recipe_name_input.text = ''
        self.steps_input.text = ''
        self.success_label.text = ''
        self.ingredients_layout.clear_widgets()
        self.ingredient_inputs.clear()

    def calculate_nutrition(self, ingredients):
        # Simulate fetching nutrition data from API or database
        if ingredients:
            # This is where the logic for calculating nutrition based on ingredients would go
            nutrition_data = self.fetch_nutrition_by_ingredients(ingredients)
            if nutrition_data:
                calories = nutrition_data.get('ENERC_KCAL', {}).get('quantity', 'N/A')
                fat = nutrition_data.get('FAT', {}).get('quantity', 'N/A')
                protein = nutrition_data.get('PROCNT', {}).get('quantity', 'N/A')
                carbs = nutrition_data.get('CHOCDF', {}).get('quantity', 'N/A')

                # Update the label to display nutritional information
                self.nutrition_label.text = f"Calories: {calories} kcal, Fat: {fat} g, Protein: {protein} g, Carbs: {carbs} g"
            else:
                self.nutrition_label.text = "Nutritional data not found."
        else:
            self.nutrition_label.text = "Please enter ingredients."

    def fetch_nutrition_by_ingredients(self, ingredients):
        # This is a mock function to simulate fetching nutrition data
        try:
            app_id = "ce7750ed"
            app_key = "4e98af59de94027f47931f0131073f33"
            url = f"https://api.edamam.com/api/nutrition-details?app_id={app_id}&app_key={app_key}"
            headers = {"Content-Type": "application/json"}
            data = {"ingr": ingredients}

            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            return response.json().get('totalNutrients', {})
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching nutritional data: {e}")
            return {}


class MyGridLayout(GridLayout):
    def __init__(self, **kwargs):
        super(MyGridLayout, self).__init__(**kwargs)
        self.cols = 2
        
        # Create a SpellChecker instance
        self.spell = SpellChecker()

        # Create a TextInput widget for ingredients input
        self.ingredient_input = TextInput(multiline=False)
        self.add_widget(Label(text="Ingredient:"))
        self.add_widget(self.ingredient_input)

        # Create a submit button to trigger auto-correction
        self.submit_button = Button(text="Submit")
        self.submit_button.bind(on_press=self.correct_text)
        self.add_widget(self.submit_button)

    def correct_text(self, instance):
        # Get the text from the TextInput
        text = self.ingredient_input.text

        # Split the text into words
        words = text.split()

        # Correct each word using SpellChecker
        corrected_words = [self.spell.correction(word) for word in words]

        # Join the corrected words back into a string
        corrected_text = " ".join(corrected_words)

        # Set the corrected text back to the TextInput
        self.ingredient_input.text = corrected_text


class RecipeDetailsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(RecipeDetailsScreen, self).__init__(**kwargs)
        self.container = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.root_layout.add_widget(self.container)

        self.recipe_title = Label(text='', size_hint=(1, 0.1), font_size='35sp', color=(0, 0, 0, 1))
        self.container.add_widget(self.recipe_title)

        self.scroll_view = ScrollView(size_hint=(1, 0.7))
        self.recipe_details = Label(text='', size_hint_y=None, color=(0, 0, 0, 1), font_size='24sp')
        self.recipe_details.bind(texture_size=self.recipe_details.setter('size'))
        self.scroll_view.add_widget(self.recipe_details)
        self.container.add_widget(self.scroll_view)

        self.button_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        self.recipe_url_button = Button(text='View Full Recipe', size_hint=(0.8, 1))
        self.recipe_url_button.bind(on_press=self.open_recipe_url)
        self.button_layout.add_widget(self.recipe_url_button)

        self.save_recipe_button = MDIconButton(
            icon="cards-heart-outline",
            size_hint=(None, None),
            icon_size="48sp"
        )
        self.save_recipe_button.bind(on_press=self.toggle_save_recipe)
        self.button_layout.add_widget(self.save_recipe_button)

        self.container.add_widget(self.button_layout)

        self.back_button = Button(text='Back', size_hint=(1, 0.1))
        self.back_button.bind(on_press=self.go_back)
        self.container.add_widget(self.back_button)

    def display_recipe(self, recipe):
        try:
            self.recipe = recipe

            self.recipe_title.text = recipe.get('title', 'No Title Available')

            nutrition_info = recipe.get('nutrition', {})
            calories = nutrition_info.get('calories', 'N/A')
            protein = nutrition_info.get('protein', 'N/A')
            fat = nutrition_info.get('fat', 'N/A')
            carbs = nutrition_info.get('carbs', 'N/A')

        # Update the details text to include nutritional information
            self.recipe_details.text = (
                f"Source: {recipe.get('description', 'Unknown Source')}\n\n"
                f"Ingredients:\n" + '\n'.join(recipe.get('ingredients', [])) +
                f"\n\nNutritional Information:\n"
                f"Calories: {calories}\n"
                f"Protein: {protein}\n"
                f"Fat: {fat}\n"
                f"Carbohydrates: {carbs}"
            )

            self.recipe_url_button.recipe_url = recipe.get('url', '')

            app = MDApp.get_running_app()
            if is_recipe_saved(app.user_id, self.recipe.get('title', 'No Title Available')):
                self.save_recipe_button.icon = "cards-heart"
            else:
                self.save_recipe_button.icon = "cards-heart-outline"
        
        except Exception as e:
            logging.error(f"Error in display_recipe: {e}")
            popup = Popup(title='Error', content=Label(text=f"Error: {e}"), size_hint=(None, None), size=(400, 200))
            popup.open()


        
    def open_recipe_url(self, instance):
        try:
            webbrowser.open(instance.recipe_url)
        except Exception as e:
            logging.error(f"Error opening URL: {e}")
            popup = Popup(title='Error', content=Label(text=f"Error opening URL: {e}"), size_hint=(None, None), size=(400, 200))
            popup.open()

    def toggle_save_recipe(self, instance):
        app = MDApp.get_running_app()
        user_id = app.user_id

        if not hasattr(self, 'recipe') or self.recipe is None:
            logging.error("No recipe data found to save.")
            popup = Popup(title='Error', content=Label(text='No recipe data found to save.'), size_hint=(None, None), size=(400, 200))
            popup.open()
            return

        if user_id is None:
            popup = Popup(title='Error', content=Label(text='You must be logged in to save recipes.'), size_hint=(None, None), size=(400, 200))
            popup.open()
            app.previous_screen = 'details'
            app.next_action = 'save_recipe'
            app.next_recipe = self.recipe
            app.screen_manager.current = 'login'
            return

        if self.save_recipe_button.icon == "cards-heart-outline":
            self.save_recipe(user_id)
        else:
            self.unsave_recipe(user_id)


    def save_recipe(self, user_id):
        try:
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()

            # Use 'title' instead of 'label' as the key
            cursor.execute("INSERT INTO saved_recipes (user_id, recipe_name, recipe_url, recipe_ingredients, recipe_source) VALUES (?, ?, ?, ?, ?)",
                       (user_id, self.recipe.get('title', 'No Title Available'), self.recipe.get('url', ''),
                        '\n'.join(self.recipe.get('ingredients', [])), self.recipe.get('description', 'Unknown Source')))
            conn.commit()
            self.save_recipe_button.icon = "cards-heart"
            popup = Popup(title='Success', content=Label(text='Recipe saved successfully!'), size_hint=(None, None), size=(400, 200))
            popup.open()
        except sqlite3.IntegrityError:
            popup = Popup(title='Error', content=Label(text='Recipe already saved.'), size_hint=(None, None), size=(400, 200))
            popup.open()
        except Exception as e:
            logging.error(f"Error in save_recipe: {e}")
            popup = Popup(title='Error', content=Label(text=f"Error: {e}"), size_hint=(None, None), size=(400, 200))
            popup.open()
        finally:
            conn.close()
            app = MDApp.get_running_app()
            if app.screen_manager.current == 'saved_recipes':
                app.saved_recipes_screen.display_saved_recipes(user_id)


    def unsave_recipe(self, user_id):
        try:
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()

            # Use 'title' instead of 'label' as the key
            cursor.execute("DELETE FROM saved_recipes WHERE user_id = ? AND recipe_name = ?", 
                       (user_id, self.recipe.get('title', 'No Title Available')))
            conn.commit()
            conn.close()
            self.save_recipe_button.icon = "cards-heart-outline"
            popup = Popup(title='Success', content=Label(text='Recipe unsaved successfully!'), size_hint=(None, None), size=(400, 200))
            popup.open()

            app = MDApp.get_running_app()
            if app.screen_manager.current == 'saved_recipes':
                app.saved_recipes_screen.display_saved_recipes(user_id)

        except Exception as e:
                logging.error(f"Error in unsave_recipe: {e}")
                popup = Popup(title='Error', content=Label(text=f"Error: {e}"), size_hint=(None, None), size=(400, 200))
                popup.open()


    def go_back(self, instance):
        app = MDApp.get_running_app()
        if app.previous_screen == 'saved_recipes':
            app.screen_manager.current = 'saved_recipes'
        else:
            app.screen_manager.current = 'main'
        app.previous_screen = None
        logging.debug(f"Navigated back to {app.screen_manager.current} from RecipeDetailsScreen")



class AccountScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(AccountScreen, self).__init__(**kwargs)

        # Create the container layout for the UI components
        self.container = BoxLayout(orientation='vertical', padding=10, spacing=5, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.container.bind(minimum_height=self.container.setter('height'))
        self.container.bind(minimum_width=self.container.setter('width'))
        self.root_layout.add_widget(self.container)

        self.username_label = Label(text='Username: ', color=(0, 0, 0, 1), font_size='24sp', size_hint=(None, None), halign='center', valign='middle')
        self.username_label.bind(size=self.username_label.setter('text_size'))
        self.container.add_widget(self.username_label)

        self.email_label = Label(text='Email: ', color=(0, 0, 0, 1), font_size='24sp', size_hint=(None, None), halign='center', valign='middle')
        self.email_label.bind(size=self.email_label.setter('text_size'))
        self.container.add_widget(self.email_label)

        # Button to navigate to Nutrient Recommendation Screen
        self.nutrition_button = Button(text='Nutrition Recommendation', size_hint=(None, None), width=400, height=50, pos_hint={'center_x': 0.5})
        self.nutrition_button.bind(on_press=self.go_to_nutrition_recommendation)
        self.container.add_widget(self.nutrition_button)

        # Add the "Back" button at the bottom
        self.back_button = Button(text='Back', size_hint=(None, None), width=400, height=50, pos_hint={'center_x': 0.5, 'y': 0.1})
        self.back_button.bind(on_press=self.go_back)
        self.root_layout.add_widget(self.back_button)

        self.nutrition_label = Label(text='', color=(0, 0, 0, 1), font_size='18sp', size_hint=(None, None))
        self.container.add_widget(self.nutrition_label)

         # Create a container for the account details
        self.container = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.root_layout.add_widget(self.container)

        # Add "My Recipes" label
        self.my_recipes_label = Label(text='My Recipes', size_hint=(1, None), height=40)
        self.container.add_widget(self.my_recipes_label)

        # Scrollable view for user's recipes
        self.my_recipes_scroll = ScrollView(size_hint=(1, 0.8))
        self.my_recipes_list = GridLayout(cols=1, size_hint_y=None)
        self.my_recipes_list.bind(minimum_height=self.my_recipes_list.setter('height'))
        self.my_recipes_scroll.add_widget(self.my_recipes_list)
        self.container.add_widget(self.my_recipes_scroll)

    def update_my_recipes(self):
        """Fetch and update the list of user's recipes."""
        # Clear the current list
        self.my_recipes_list.clear_widgets()

        # Fetch recipes from the database
        app = MDApp.get_running_app()
        user_id = app.user_id

        # Assuming you have a function `fetch_user_recipes(user_id)` to get recipes from the database
        recipes = fetch_user_recipes(user_id)

        # Display each recipe
        for recipe in recipes:
            recipe_button = Button(text=recipe['recipe_name'], size_hint_y=None, height=40)
            self.my_recipes_list.add_widget(recipe_button)


    def go_to_nutrition_recommendation(self, instance):
        # Navigate to the NutrientRecommendationScreen
        MDApp.get_running_app().screen_manager.current = 'nutrient_recommendation'

    def load_account_details(self):
        """Load the user's account details and nutritional data from the database."""
        try:
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()
            cursor.execute("SELECT username, email, calories, carbs, protein, fats, dietary_preference FROM users WHERE user_id = ?", (MDApp.get_running_app().user_id,))
            user = cursor.fetchone()
            conn.close()

            if user:
                self.username_label.text = f'Username: {user[0]}'
                self.email_label.text = f'Email: {user[1]}'
                self.nutrition_label.text = (
                    f"Calories: {user[2]:.2f} kcal\n"
                    f"Carbs: {user[3]:.2f} g\n"
                    f"Protein: {user[4]:.2f} g\n"
                    f"Fats: {user[5]:.2f} g\n"
                    f"Dietary Preference: {user[6]}"
                )
            else:
                self.username_label.text = 'Username: '
                self.email_label.text = 'Email: '
                self.nutrition_label.text = 'Nutritional Data: Not Available'

        except Exception as e:
            popup = Popup(title='Error', content=Label(text=f"Error loading account details: {str(e)}"), size_hint=(None, None), size=(400, 200))
            popup.open()

    def go_back(self, instance):
        MDApp.get_running_app().screen_manager.current = 'main'


class NutrientRecommendationScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(NutrientRecommendationScreen, self).__init__(**kwargs)
        
        # Initialize database
        self.initialize_db()

        # Layout for the input fields
        self.container = BoxLayout(orientation='vertical', padding=10, spacing=5, size_hint=(None, None), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.container.bind(minimum_height=self.container.setter('height'))
        self.container.bind(minimum_width=self.container.setter('width'))
        self.root_layout.add_widget(self.container)

        # Age input
        self.age_input = TextInput(hint_text='Age', size_hint=(None, None), width=400, height=50)
        self.container.add_widget(self.age_input)

        # Sex input
        self.sex_input = Spinner(
            text='Select Sex',
            values=('Male', 'Female'),
            size_hint=(None, None),
            width=400,
            height=50
        )
        self.container.add_widget(self.sex_input)

        # Weight input
        self.weight_input = TextInput(hint_text='Weight (kg)', size_hint=(None, None), width=400, height=50)
        self.container.add_widget(self.weight_input)

        # Height input
        self.height_input = TextInput(hint_text='Height (cm)', size_hint=(None, None), width=400, height=50)
        self.container.add_widget(self.height_input)

        # Activity level input
        self.activity_input = Spinner(
            text='Select Activity Level',
            values=('Sedentary', 'Lightly Active', 'Moderately Active', 'Very Active', 'Extra Active'),
            size_hint=(None, None),
            width=400,
            height=50
        )
        self.container.add_widget(self.activity_input)

        # Goal input
        self.goal_input = Spinner(
            text='Select Goal',
            values=('Weight Loss', 'Maintenance', 'Muscle Gain'),
            size_hint=(None, None),
            width=400,
            height=50
        )
        self.container.add_widget(self.goal_input)

        # Dietary preference input
        self.dietary_input = Spinner(
            text='Select Dietary Preference',
            values=('None', 'Vegan', 'Vegetarian', 'Lactose Free', 'Paleo', 'Ketogenic', 'Fully Plant Based'),
            size_hint=(None, None),
            width=400,
            height=50
        )
        self.container.add_widget(self.dietary_input)

        # Calculate button
        self.calculate_button = Button(text='Calculate', size_hint=(None, None), width=400, height=50)
        self.calculate_button.bind(on_press=self.calculate_nutrition)
        self.container.add_widget(self.calculate_button)

        # Save button
        self.save_button = Button(text='Save Data', size_hint=(None, None), width=400, height=50)
        self.save_button.bind(on_press=self.save_user_data)
        self.container.add_widget(self.save_button)

        # Results label
        self.results_label = Label(
            text='',
            color=(0, 0, 0, 1),
            font_size='18sp',
            size_hint=(None, None),
            halign='center',  # Align text to the left
            valign='middle',  # Align text vertically in the middle
            text_size=(400, None),  # Set a fixed width for the label to wrap text properly
            padding=(10, 10)  # Add padding for a nicer look
        )
        self.results_label.bind(size=self.results_label.setter('text_size'))
        self.results_label.pos_hint = {'x': 0.4}
        self.container.add_widget(self.results_label)

        # Back button
        self.back_button = Button(text='Back', size_hint=(None, None), width=400, height=50, pos_hint={'center_x': 0.5})
        self.back_button.bind(on_press=self.go_back)
        self.container.add_widget(self.back_button)

    def calculate_nutrition(self, instance):
        """Calculate nutritional recommendations based on user input."""
        try:
            # Retrieve user inputs
            age = int(self.age_input.text)
            sex = self.sex_input.text
            weight = float(self.weight_input.text)
            height = float(self.height_input.text)
            activity_level = self.activity_input.text.lower()
            goal = self.goal_input.text.lower()
            dietary_preference = self.dietary_input.text.lower()

            goal = self.goal_input.text.lower().replace(' ', '_')  # Converts "Weight Loss" to "weight_loss", etc.
            dietary_preference = self.dietary_input.text.lower()

            # Create a NutrientRecommendation object and calculate values
            nutrient_recommendation = NutrientRecommendation(age, sex, weight, height, activity_level, goal, dietary_preference)
            self.daily_calories = nutrient_recommendation.get_daily_calorie_needs()
            self.macronutrients = nutrient_recommendation.get_macronutrient_distribution()

            # Display results
            self.results_label.text = (
                f"Calories: {self.daily_calories:.2f} kcal\n"
                f"Carbs: {self.macronutrients['carbs']:.2f} g\n"
                f"Protein: {self.macronutrients['protein']:.2f} g\n"
                f"Fats: {self.macronutrients['fats']:.2f} g"
            )

        except ValueError as ve:
            popup = Popup(title='Error', content=Label(text=f"Invalid input: {str(ve)}"), size_hint=(None, None), size=(400, 200))
            popup.open()
        except Exception as e:
            popup = Popup(title='Error', content=Label(text=f"Error calculating nutrition: {str(e)}"), size_hint=(None, None), size=(400, 200))
            popup.open()

    def save_user_data(self, instance):
        """Save user input data to the database."""
        try:
            # Calculate the nutrition data first
            self.calculate_nutrition(instance)

            # Fetch the current user's ID
            user_id = MDApp.get_running_app().user_id

            # Save the nutritional data and dietary preference to the user's profile
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET calories = ?, carbs = ?, protein = ?, fats = ?, dietary_preference = ? WHERE user_id = ?
            """, (self.daily_calories, self.macronutrients['carbs'], self.macronutrients['protein'], self.macronutrients['fats'], self.dietary_input.text, user_id))
            conn.commit()
            conn.close()

            popup = Popup(title='Success', content=Label(text='User data saved successfully!'), size_hint=(None, None), size=(400, 200))
            popup.open()

            app = MDApp.get_running_app()
            app.account_screen.load_account_details()
            app.screen_manager.current = 'account'
        
        except Exception as e:
            popup = Popup(title='Error', content=Label(text=f"Error saving data: {str(e)}"), size_hint=(None, None), size=(400, 200))
            popup.open()

    def initialize_db(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            conn = sqlite3.connect('nutrient_recommendations.db')
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_data (
                              age INTEGER, 
                              sex TEXT, 
                              weight REAL, 
                              height REAL, 
                              activity_level TEXT, 
                              goal TEXT,
                              dietary_preference TEXT)''')
            conn.close()
        except Exception as e:
            popup = Popup(title='Error', content=Label(text=f"Error initializing database: {str(e)}"), size_hint=(None, None), size=(400, 200))
            popup.open()

    def go_back(self, instance):
        MDApp.get_running_app().screen_manager.current = 'account'



class SavedRecipesScreen(BaseScreen):
    def __init__(self, **kwargs):
        super(SavedRecipesScreen, self).__init__(**kwargs)
        self.container = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint=(0.9, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.root_layout.add_widget(self.container)

        self.scroll_view = ScrollView(size_hint=(1, 0.8))
        self.results_layout = GridLayout(cols=1, size_hint_y=None)
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        self.scroll_view.add_widget(self.results_layout)
        self.container.add_widget(self.scroll_view)

        go_back_button = Button(
            text='Go Back',
            size_hint=(1, 0.1)
        )
        go_back_button.bind(on_press=self.go_back)
        self.container.add_widget(go_back_button)

    def execute_query(self, query, params=()):
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.close()
        return result

    def display_saved_recipes(self, user_id):
        self.results_layout.clear_widgets()
        saved_recipes = self.execute_query("SELECT recipe_name, recipe_url, recipe_ingredients, recipe_source FROM saved_recipes WHERE user_id = ?", (user_id,))
        
        if saved_recipes:
            for recipe_name, recipe_url, recipe_ingredients, recipe_source in saved_recipes:
                box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
                recipe_button = Button(
                    text=recipe_name,
                    size_hint_x=0.8,
                )
                recipe_button.bind(on_press=lambda instance, rname=recipe_name, rurl=recipe_url, ringredients=recipe_ingredients, rsource=recipe_source: self.view_recipe(rname, rurl, ringredients, rsource))
                
                unsave_button = MDIconButton(
                    icon="cards-heart",
                    size_hint_x=0.2,
                    icon_size="32sp"
                )
                unsave_button.bind(on_press=lambda instance, rname=recipe_name: self.toggle_save_recipe(instance, user_id, rname))

                box.add_widget(recipe_button)
                box.add_widget(unsave_button)
                self.results_layout.add_widget(box)
        else:
            self.results_layout.add_widget(Label(text='No saved recipes found.', color=(0, 0, 0, 1)))

    def view_recipe(self, recipe_name, recipe_url, recipe_ingredients, recipe_source):
        try:
            app = MDApp.get_running_app()
            app.recipe_details_screen.display_recipe({
                'title': recipe_name,
                'url': recipe_url,
                'ingredients': recipe_ingredients.split('\n'),
                'description': recipe_source if recipe_source else 'Unknown Source'
            })
            app.previous_screen = 'saved_recipes'
            app.screen_manager.current = 'details'
        except Exception as e:
            logging.error(f"Error in view_recipe: {e}")
            popup = Popup(title='Error', content=Label(text=f"Error: {e}"), size_hint=(None, None), size=(400, 200))
            popup.open()

    def toggle_save_recipe(self, instance, user_id, recipe_name):
        try:
            conn = sqlite3.connect('example.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM saved_recipes WHERE user_id = ? AND recipe_name = ?", (user_id, recipe_name))
            saved = cursor.fetchone()
            
            if saved:
                cursor.execute("DELETE FROM saved_recipes WHERE user_id = ? AND recipe_name = ?", (user_id, recipe_name))
                conn.commit()
                instance.icon = "cards-heart-outline"
                Clock.schedule_once(lambda dt: self.display_saved_recipes(user_id), 0.9)
            else:
                cursor.execute("INSERT INTO saved_recipes (user_id, recipe_name, recipe_url, recipe_ingredients, recipe_source) VALUES (?, ?, ?, ?, ?)",
                               (user_id, recipe_name, "", "", ""))
                conn.commit()
                instance.icon = "cards-heart"
            conn.close()
        except Exception as e:
            logging.error(f"Error in toggle_save_recipe: {e}")
            popup = Popup(title='Error', content=Label(text=f"Error: {e}"), size_hint=(None, None), size=(400, 200))
            popup.open()
        finally:
            self.display_saved_recipes(user_id)

    def go_back(self, instance):
        app = MDApp.get_running_app()
        app.screen_manager.current = 'main'

if __name__ == '__main__':
    create_tables()
    RecipeFinderApp().run()
