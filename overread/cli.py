import sys

from overread.get import get


def main():
    if len(sys.argv) == 1:
        print("usage")
    else:
        cmd = sys.argv[1]
        if cmd == "get":
            get(sys.argv[2:])
    return
