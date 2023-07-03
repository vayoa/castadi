import modules.scripts as scripts
import gradio as gr
import os

from modules import script_callbacks


def on_ui_tabs():
    with open('settings.json', 'r') as file:
        default_settings = file.read()

    with gr.Blocks(analytics_enabled=False) as ui_component:
        with gr.Row():
            with gr.Tab("Script"):
                script = gr.TextArea(
                    lines=20,
                    show_label=False,
                )

            with gr.Tab("Settings"):
                settings = gr.Code(
                    language='json',
                    lines=20,
                    show_label=False,
                    value=default_settings,
                )

            with gr.Column():
                btn = gr.Button(
                    "Generate",
                    variant='primary'
                )

                gallery = gr.Gallery(
                    label="Dummy Image",
                    show_label=False,
                )

        btn.click(
            dummy_images,
            inputs=[script, settings],
            outputs=[gallery],
        )

        return [(ui_component, "Extension Example", "extension_example_tab")]


def dummy_images(script):
    if (script):
        return [
            "https://chichi-pui.imgix.net/uploads/post_images/eee3b614-f126-4045-b53d-8bf38b98841d/05aba7f3-208b-4912-92f3-32d1bfc2edc3_1200x.jpeg?auto=format&lossless=0"
        ]
    else:
        return []


script_callbacks.on_ui_tabs(on_ui_tabs)
