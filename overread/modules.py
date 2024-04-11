from collections import namedtuple
import glob
import importlib
import os
import sys


Module = namedtuple("Module", "name get color whats wheres default_where")


async def load():
    sys.path += [os.path.join(os.path.dirname(os.path.realpath(__file__)), "builtin_modules")]
    if os.getenv("OVERREAD_MODULE_PATHS"):
        module_paths = os.environ["OVERREAD_MODULE_PATHS"].split(",")
        sys.path += module_paths
    for m in _find_ov_modules():
        try:
            mod = importlib.import_module(m)
            yield Module(
                name = m.split("overread_", 1)[-1],
                get = mod.get,
                color = mod.color(),
                whats = mod.whats(),
                wheres = [w async for w in mod.wheres()],
                default_where = mod.default_where()
            )
        except Exception as e:
            print(f"Error loading module {m}: {e}")


def _find_ov_modules():
    for dir in sys.path:
        yield from {
            os.path.splitext(os.path.basename(full_path))[0]
            for full_path in glob.glob(os.path.join(dir, "overread_*.py"))
        }
