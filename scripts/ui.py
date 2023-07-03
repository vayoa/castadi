import modules.scripts as scripts
import gradio as gr
import os

from modules import script_callbacks

DEFAULT_SETTINGS = '''
{
  "canvas_width": 1080,
  "canvas_height": 1920,

  // The default min size a panel would have.
  // based on the percentage of the page size
  "panel_min_width_percent": 0.21,
  "panel_min_height_percent": 0.117,

  // The ratio of panel generation.
  // For example 1 would mean that if a panel is 1080x960 it would
  // be generated at that resulotion. If you don't have enough vram keep it low.
  "image_zoom": "4/9",
  "border_width": 5,
  "default_bubble": {
    "font_size": 16,
    "bubble_color": "(20, 20, 20)",
    "text_color": "white",
    "font": "C:\\Windows\\Fonts\\Arial.ttf"
  },

  "prompt_prefix": "(masterpiece, best quality:1.1)",
  "negative_prompt": "(bad quality, low quality:1.1)",

  "characters": {
    // here is an example character:
    // "character_name": {
    //   "tags": "guy, male, short black hair, white pants, white shirt",
    //   "bubble": {
    //     "bubble_color": "(200, 200, 200)",
    //     "text_color": "black"
    //   }
    // }
  }
}

'''


def on_ui_tabs():
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
                    value=DEFAULT_SETTINGS,
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


def dummy_images(script, settings):
    if (script):
        return [
            "https://chichi-pui.imgix.net/uploads/post_images/eee3b614-f126-4045-b53d-8bf38b98841d/05aba7f3-208b-4912-92f3-32d1bfc2edc3_1200x.jpeg?auto=format&lossless=0"
        ]
    else:
        return []


script_callbacks.on_ui_tabs(on_ui_tabs)
