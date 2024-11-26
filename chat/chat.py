import reflex as rx

from chat import style
from chat.state import SettingsState
from chat.components.settings import settings_icon
from chat.components.reset import reset
from chat.views.templates import templates
from chat.views.chatc import chat, action_bar


def index() -> rx.Component:
    return rx.theme(
        rx.el.style(
            f"""
            :root {{
                --font-family: "{SettingsState.font_family}", sans-serif;
            }}
        """
        ),
        # Top bar with the reset and settings buttons
        rx.box(
            reset(),
            settings_icon(),
            class_name="top-4 right-4 absolute flex flex-row items-center gap-3.5",
        ),
        # Main content
        rx.box(
            # Prompt examples
            templates(),
            # Chat history
            chat(),
            # Action bar
            action_bar(),
            class_name="relative flex flex-col justify-between gap-20 mx-auto px-6 pt-16 lg:pt-6 pb-6 max-w-4xl h-screen",
        ),
        accent_color=SettingsState.color,
    )


app = rx.App(stylesheets=style.STYLESHEETS, style={"font_family": "var(--font-family)"})
app.add_page(
    index, title="Chatbot", description="A chatbot powered by Reflex and LlamaIndex!"
)