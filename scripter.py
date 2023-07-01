from ast import literal_eval
import re


class Character():
    def __init__(self, tags, bubble_props=None):
        self.tags = tags
        self.bubble_props = bubble_props


class Event:
    def __init__(self, text, character=None):
        self.text = text
        self.character = Character(
            character) if character is not None else None

    def bake(self, characters):
        baked = re.sub(r'\[(.*?)\]', lambda match: characters.get(
            match.group(1), match.group(0)).tags, self.text)
        return baked[:-1] if baked.endswith('.') else baked

    def bubble(self):
        if self.character is None:
            return None
        elif self.character.bubble_props is None:
            return (self.text, ) + (None,) * 4
        return (self.text, *self.character.bubble_props)


class Panel:
    def __init__(self, location=None, events=None, split_on_width=None):
        self.location = location
        self.events = events if events is not None else []
        self.split_on_width = split_on_width

    def bake(self, characters):
        baked = ', '.join([e.bake(characters)
                           for e in self.events if e.character is None])
        return baked + f', {self.location}'

    def get_dialog(self):
        bubbles = []
        for e in self.events:
            bubble = e.bubble()
            if bubble is not None:
                bubbles.append(bubble)
        return bubbles if bubbles else None


class Page:

    def parse(line):
        m = re.match(r"-(\w+)(?:\((.+)\))?", line)
        if m:
            props = m.group(2) or ""
            props = props.split('|')
            props_dict = {}
            for prop in props:
                prop = prop.strip()
                split = prop.split(':')
                if len(split) == 2:
                    props_dict[split[0].strip()] = split[1].strip()

            if 'min' in props_dict:
                props_dict['min'] = literal_eval(props_dict['min'])

            return Page(m.group(1), panel_min_percent=props_dict.get('min', None))

    def __init__(self, name, panels=None, panel_min_percent=None):
        self.name = name
        self.panels = panels if panels is not None else []
        self.panel_min_percent = panel_min_percent

    def get_dialog(self):
        return [p.get_dialog() for p in self.panels]

    def get_splits(self):
        return [p.split_on_width for p in self.panels[1:]] + [None]


def script(text):
    lines = text.split('\n')
    pages = []
    current_page = None
    events = []
    current_location = None
    split = None
    last_character = None

    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            continue
        if line.startswith('-'):
            if current_page is not None:
                pages.append(current_page)
            current_page = Page.parse(line)
        elif line.startswith('location:'):
            current_location = line.replace('location:', '').strip()
        elif line.startswith('split:'):
            split = line.replace('split:', '').strip()
            split = split.startswith('h') or split.startswith('H')
        elif not line:
            if events:
                current_page.panels.append(
                    Panel(current_location, events, split_on_width=split))
                events = []
                split = None
        else:
            words = line.split(' ')
            for word in words:
                word = word.strip()
                if word.startswith('[') and word.endswith(']'):
                    last_character = word[1:-1]

            m = re.search(r'^^(?:\[.*\]\s+)?\"(.+)\"', line)
            if m:
                events.append(Event(m.group(1).strip(), last_character))
            else:
                events.append(Event(line))

    if events:
        current_page.panels.append(
            Panel(current_location, events, split_on_width=split))
        events = []
        split = None

    if current_page is not None:
        pages.append(current_page)

    return pages
