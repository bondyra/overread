from nicegui import ui

# from rich.markup import escape
# from rich.text import Text

# from textual.app import App, ComposeResult
# from textual.binding import Binding
# from textual.containers import Container, ScrollableContainer
# from textual.reactive import reactive
# from textual.suggester import SuggestFromList
# from textual.widgets import (Button, Footer, Input, Static, Tree)

from overread.service import load_modules


# from_markup = Text.from_markup


# class Body(ScrollableContainer):
#     pass


# class Message(Static):
#     pass


# class Section(Container):
#     pass


# class ResourceData(Tree):
#     def __init__(self, resource_name, resource_data, *args, **kwargs):
#         super().__init__(resource_name, *args, **kwargs)
#         def add_node(name, node, data) -> None:
#             if isinstance(data, dict):
#                 node.set_label(Text(name))
#                 for key, value in data.items():
#                     new_node = node.add("")
#                     add_node(key, new_node, value)
#             elif isinstance(data, list):
#                 node.set_label(Text(f"[] {name}"))
#                 for index, value in enumerate(data):
#                     new_node = node.add("")
#                     add_node(str(index), new_node, value)
#             else:
#                 node.allow_expand = False
#                 if name:
#                     label = Text.assemble(
#                         Text.from_markup(f"{name}: {data}")
#                     )
#                 else:
#                     label = Text(repr(data))
#                 node.set_label(label)

#         add_node(resource_name, self.root, resource_data)


# class ElementContainer(Container):
#     pass


# class Vertex(Container):
#     def __init__(self, resource_name, resource_data, where, *args, **kwargs):
#         self._resource_name = resource_name
#         self._resource_data = resource_data
#         self._where = where
#         self._suggestions = list(self._data_to_suggestions(self._resource_data))
#         super().__init__(*args, **kwargs)

#     def compose(self) -> ComposeResult:
#         yield ElementContainer(
#             Static(self._resource_name, classes="label"),
#             Input(None, "search", suggester=SuggestFromList(self._suggestions)),
#             ResourceData("data", self._resource_data),
#             Input(None, "link", suggester=SuggestFromList(self._suggestions)),
#         )

#     def _data_to_suggestions(self, data):
#         if isinstance(data, dict):
#             for key in data.keys():
#                 yield key
#                 yield from self._data_to_suggestions(data[key])
#         elif isinstance(data, list):
#             for item in data:
#                 yield from self._data_to_suggestions(item)
#         else:
#             yield data


# class Overread(App[None]):
#     CSS_PATH = "ui.tcss"
#     TITLE = "Overread"
#     BINDINGS = [
#         ("ctrl+s", "app.screenshot()", "Screenshot"),
#         Binding("up", "navigate(-1,0)", "Move Up", False),
#         Binding("down", "navigate(1,0)", "Move Down", False),
#         Binding("left", "navigate(0,-1)", "Move Left", False),
#         Binding("right", "navigate(0,1)", "Move Right", False),
#         Binding("ctrl+c", "app.quit", "Quit", show=True),
#     ]

#     show_sidebar = reactive(False)

#     def __init__(self, modules, *args, **kwargs):
#         self._modules = modules
#         super().__init__(*args, **kwargs)

#     def compose(self) -> ComposeResult:
#         yield Container(
#             Body(
#                 Section(
#                     Vertex("cos", {"dupaMark": {"mleczko": {"chujKurwa": "mleko123"}}}, "default/us-east-1"),
#                 ),
#                 classes="location-widgets location-first",
#             ),
#         )
#         yield Footer()

#     def on_mount(self) -> None:
#         self.query_one("Vertex", Vertex).focus()

#     def action_screenshot(self, filename = None, path = "./"):
#         path = self.save_screenshot(filename, path)
#         message = f"Screenshot saved to [bold green]'{escape(str(path))}'[/]"
#         self.notify(message)


modules = load_modules()
ui.label("Kurwa!")
ui.label("Cipa!")
with ui.row().style('display: block;'):
    with ui.column().style('display: block;'):
        with ui.card():
            ui.input('Name')
            ui.tree(
                [
                    {'id': 'numbers', 'children': [{'id': '1'}, {'id': '2'}]},
                    {'id': 'letters', 'children': [{'id': 'A'}, {'id': 'B'}]},
                ], 
                label_key='id'
            )
        with ui.card():
            ui.input('Name')
            ui.tree(
                [
                    {'id': 'numbers', 'children': [{'id': '1'}, {'id': '2'}]},
                    {'id': 'letters', 'children': [{'id': 'A'}, {'id': 'B'}]},
                ], 
                label_key='id'
            )
    with ui.column().style('display: block;'):
        ui.html('<svg width="32" height="500"><line x1="10" y1="10" x2="190" y2="10" style="stroke: gray; stroke-width: 5;" /></svg>')
    with ui.column().style('display: block;'):
        with ui.card():
            ui.input('Name')
            ui.tree(
                [
                    {'id': 'numbers', 'children': [{'id': '1'}, {'id': '2'}]},
                    {'id': 'letters', 'children': [{'id': 'A'}, {'id': 'B'}]},
                ], 
                label_key='id'
            )
        with ui.card():
            ui.input('Name')
            ui.tree(
                [
                    {'id': 'numbers', 'children': [{'id': '1'}, {'id': '2'}]},
                    {'id': 'letters', 'children': [{'id': 'A'}, {'id': 'B'}]},
                ], 
                label_key='id'
            )
ui.run(dark=True)
