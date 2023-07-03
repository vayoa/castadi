import modules.scripts as scripts
import gradio as gr
from castadi import main_runner as mr

from modules import script_callbacks

DEFAULT_SETTINGS = r'''
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
                    preview=True,
                    object_fit='scale-down',
                )

        btn.click(
            dummy_images,
            inputs=[script, settings],
            outputs=[gallery],
        )

        return [(ui_component, "Castadi", "castadi_tab")]


def dummy_images(script, settings):
    if (script and settings):
        settings = '\n'.join([l for l in settings.split(
            '\n') if not l.strip().startswith('//')])
        _, results = mr.generate(script, settings)
        return results
    else:
        return []


script_callbacks.on_ui_tabs(on_ui_tabs)
