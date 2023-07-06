import uuid
import numpy as np
import base64
import cv2
from PIL import Image
from castadi import scripter as s, panel_generator as pg, image_generator as ig


class DrawnPanel(s.Panel):
    def __init__(self, panel, dimensions, image_bytes=None):
        super().__init__(
            panel.location,
            panel.events,
            panel.split_on_width,
            panel.concepts,
        )
        self.image_bytes = image_bytes
        self.dimensions = dimensions

    @staticmethod
    def from_dict(d):
        return DrawnPanel(
            s.Panel(
                d["location"],
                [s.Event.from_dict(event) for event in d["events"]],
                d["split_on_width"],
                d["concepts"],
            ),
            d["image_bytes"],
            d["dimensions"],
        )

    def to_dict(self):
        return {
            "location": self.location,
            "events": [event.to_dict() for event in self.events],
            "split_on_width": self.split_on_width,
            "concepts": self.concepts,
            "image_bytes": self.image_bytes,
            "dimensions": self.dimensions,
        }

    def draw(
        self,
        settings,
        controlnet_payload=None,
    ):
        _, _, width, height = self.dimensions
        baked = self.bake(settings["embeds"]["characters"])
        width = int(width * settings["image_zoom"])
        height = int(height * settings["image_zoom"])
        self.image_bytes = ig.generate(
            prompt=settings["prompt_prefix"] + baked,
            negative_prompt=settings["negative_prompt"],
            width=width,
            height=height,
            controlnet_payload=controlnet_payload,
        )
        return self.image_bytes

    def get_image_bytes(self):
        if self.image_bytes is not None:
            return self.image_bytes
        _, _, width, height = self.dimensions
        return Image.new("RGB", (width, height), "white")

    def update(self, panel):
        self.location = panel.location
        self.events = panel.events
        self.split_on_width = panel.split_on_width
        self.concepts = panel.concepts


class DrawnPage(s.Page):
    def __init__(self, name, panels, panel_min_percent, mode, controlnet):
        self.name = name
        self.panels = panels
        self.panel_min_percent = panel_min_percent
        self.mode = mode
        self.controlnet = controlnet

    @staticmethod
    def from_page(page, settings):
        canvas_size = settings["canvas_size"]

        min_page_panel_size_perc = (
            page.panel_min_percent or settings["panel_min_percent"]
        )

        min_page_size = (
            int(canvas_size[0] * min_page_panel_size_perc[0]),
            int(canvas_size[1] * min_page_panel_size_perc[1]),
        )

        all_dimensions = pg.get_panels(
            len(page.panels),
            panels=[(0, 0, *canvas_size)],
            min_size=min_page_size,
            split_on_width=page.get_splits(),
        )

        p = DrawnPage(
            page.name,
            [
                DrawnPanel(panel, dimensions)
                for panel, dimensions in zip(page.panels, all_dimensions)
            ],
            page.panel_min_percent,
            page.mode,
            page.mode == "controlnet",
        )
        p.prep(settings["embeds"]["characters"])
        return p

    @staticmethod
    def from_dict(d):
        return DrawnPage(
            d["name"],
            [DrawnPanel.from_dict(panel) for panel in d["panels"]],
            d["panel_min_percent"],
            d["mode"],
            d["controlnet"],
        )

    def to_dict(self):
        return {
            "name": self.name,
            "panels": [panel.to_dict() for panel in self.panels],
            "panel_min_percent": self.panel_min_percent,
            "mode": self.mode,
            "controlnet": self.controlnet,
        }

    def get_images(self, settings, controlnet_payload=None, draw_only=None):
        images = []
        for i, panel in enumerate(self.panels):
            if draw_only is None or i == draw_only:
                x, y, width, height = panel.dimensions
                print(f"drawing panel {i}, size {width}x{height} location ({x},{y})...")
                panel.draw(settings, controlnet_payload)
                print("done panel")

            images.append(panel.get_image_bytes())
        return images

    def get_all_dimensions(self):
        return [panel.dimensions for panel in self.panels]

    def draw(self, settings, panel=None):
        page_id = str(uuid.uuid4())

        results, names = [], []

        all_dimensions = self.get_all_dimensions()
        bubbles = self.get_dialog()

        canvas = pg.draw_rectangles(
            self.get_images(settings, draw_only=panel) if not self.controlnet else None,
            all_dimensions,
            bubbles if not self.controlnet else None,
            settings,
            reverse=self.controlnet,
        )

        if self.controlnet:
            names.append(f"{page_id}-layout.png")
            results.append(canvas.copy())

            # Convert the Pillow image to a NumPy array
            image_array = np.array(canvas)

            # Convert the NumPy array to BGR order (required by cv2)
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

            # Encode the image into PNG format
            _, buffer = cv2.imencode(".png", image_bgr)

            # Convert the image buffer to base64
            img_str = base64.b64encode(buffer).decode("utf-8")  # type: ignore

            self.panels[0].dimensions = [(0, 0, *settings["canvas_size"])]
            self.panels = [self.panels[0]]

            canvas = pg.draw_rectangles(
                None,
                all_dimensions,
                bubbles,
                settings,
                background=self.get_images(
                    settings,
                    controlnet_payload={
                        "input_image": img_str,
                        "module": "none",
                        "model": "control_v11p_sd15s2_lineart_anime [3825e83e]",
                        "weight": 2,
                        "control_mode": 2,
                    },
                )[0],
            )

        names.append(f"{page_id}.jpg")
        print(f"finished generation {names[-1]}")
        results.append(canvas)

        return names, results

    def update(self, page, settings):
        for old, new in zip(self.panels, page.panels):
            old.update(new)
        self.prep(settings["embeds"]["characters"])
        return self


def script_from_dict(d):
    return [DrawnPage.from_dict(page) for page in d]


def script_to_dict(script):
    return [page.to_dict() for page in script]
