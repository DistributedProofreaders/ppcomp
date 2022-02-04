from ppcomp import ppcomp
import argparse

def test_something():
    #args = {"filename":["bierce.txt", "bierce.html"]}
    parser = argparse.ArgumentParser(description='Diff text document for PGDP PP.')

    parser.add_argument('filename', metavar='FILENAME', type=str, help='input file', nargs=2)
    args = parser.parse_args()

    x = ppcomp.PPComp(None)
    x.simple_html()
