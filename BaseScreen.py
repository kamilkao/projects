from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle

class BaseScreen(Screen):
    def __init__(self, **kwargs):
        super(BaseScreen, self).__init__(**kwargs)

        # Create a root layout for this screen
        self.root_layout = FloatLayout()

        # Add the background image
        image_path = '/Users/kamila/Documents/MacBook Air/GitHub/kamila/IA_Recipe_KIVY/sqlsetup/images/food.JPEG'
        background = Image(source=image_path,
                           allow_stretch=True,
                           keep_ratio=False,
                           size_hint=(1, 1),
                           pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.root_layout.add_widget(background)

        # Add a semi-transparent white overlay
        overlay = Widget()
        with overlay.canvas:
            Color(1, 1, 1, 0.7)  # Semi-transparent white color
            self.bg_rect = RoundedRectangle(size=self.size, pos=self.pos)
            overlay.bind(size=self._update_bg_rect, pos=self._update_bg_rect)
        self.root_layout.add_widget(overlay)

        self.add_widget(self.root_layout)

    def _update_bg_rect(self, instance, value):
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos
