from nicegui import ui, context
from nicegui.events import KeyEventArguments

from dataclasses import dataclass

from overread.service import load_modules

from typing import Dict

x, y, c = None, None, None

@dataclass
class Resource:
    id: str
    data: Dict


class ccard(ui.card):
    def __init__(self, res: Resource, posX, posY) -> None:
        super().__init__()
        self.item = res
        with self.props('draggable').classes('w-full cursor-pointer bg-grey-1').style(f"position: absolute; top: {posX}px; left: {posY}px;"):
            ui.input('Name')
            ui.tree(dict_to_tree(res.data))
        self.on('dragstart', self.handle_dragstart)
        self.on('dragover.prevent', self.highlight)
        self.on('dragleave', self.unhighlight)

    def handle_dragstart(self) -> None:
        global dragged
        dragged = self

    def highlight(self) -> None:
        self.classes(remove='bg-grey-1', add='bg-red-1')

    def unhighlight(self) -> None:
        self.classes(remove='bg-red-1', add='bg-grey-1')


data1 = {"id1": {"f1": "v1", "f2": ["v2", "v3"], "f3": {"f4": {"f5": "v4"}}}}
data2 = {"id2": {"f1": "v1", "f2": ["v2", "v3"], "f3": {"f4": {"f5": "v4"}}}}


def dict_to_tree(inp):
    if isinstance(inp, dict):
        return [{'id': k, 'children': dict_to_tree(v)} for k, v in inp.items()]
    elif isinstance(inp, list):
        return [{'id': i, 'children': dict_to_tree(v)} for i, v in enumerate(inp)]
    else:
        return {'id': str(inp)}


class cunt(ui.row):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def highlight(self):
        self.classes(remove='bg-zinc-600', add='bg-yellow-500')

    def unhighlight(self):
        self.classes(remove='bg-yellow-500', add='bg-zinc-600')

    def load(self):
        with self:
            ui.input('Name')
            ui.tree(dict_to_tree(data1))


class dupagrid(ui.grid):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(columns=32, rows=32, *args, **kwargs)
        with self.classes('w-full gap-5'):
            self._cunts = [
                [cunt().classes('col-span-1 borderless rounded p-1 bg-zinc-600') for _ in range(32)]
                for _ in range(32)
            ]

    def at(self, i, j):
        return self._cunts[i][j] if i < 32 and j < 32 and i >= 0 and j >= 0 else None


context.get_client().content.classes('h-[100vh]')  # 1
ui.add_head_html('<style>.q-textarea.flex-grow .q-field__control { height: 100% }</style>')  # 2

modules = load_modules()
ui.label("overread 0.2")
ui.separator().classes("w-full")


def handle_key(e: KeyEventArguments):
    if e.action.keydown:
        if e.key.arrow_left:
            select(0, -1)
        elif e.key.arrow_right:
            select(0, 1)
        elif e.key.arrow_up:
            select(-1, 0)
        elif e.key.arrow_down:
            select(1, 0)
        elif e.key.enter:
            load()


keyboard = ui.keyboard(on_key=handle_key)

with ui.scroll_area().classes('w-full h-full no-wrap'):
    d = dupagrid().classes("flex-grow")


def select(i, j):
    global x, y, c
    newx, newy = (x or 0) + i, (y or 0) + j
    cc = d.at(newx, newy)
    if cc:
        cc.highlight()
        if c:
            c.unhighlight()
        x, y, c = newx, newy, cc


def load():
    global c
    if c:
        c.load()


select(0, 0)
ui.run(dark=True)
