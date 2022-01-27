#!/usr/bin/env python

from pathlib import Path

SHELL_KEYS = "spdfghSPDFGH"

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input", help=".gbs formatted basis set file")
    parser.add_argument("-o", "--output", help="destination tonto basis set file")

    args = parser.parse_args()

    inp = Path(args.input).read_text()
    lines = inp.splitlines()
    basis_name = Path(args.input).stem
    if not args.output:
        args.output = Path(args.input).stem

    with Path(args.output).open("w") as f:
        f.write(f"! converted from {args.input} by gbs2tonto.py\n")
        new_section = True
        header_written = False
        for line in lines:
            lstrip = line.strip()
            if not lstrip:
                continue
            elif lstrip.startswith("!"):
                f.write(line)
            elif lstrip.startswith("*"):
                new_section = True
                f.write("      }\n")
            else:
                if not header_written:
                    f.write("{\n   keys= { turbomole= }\n   data= {\n\n")
                    header_written = True
                if new_section:
                    tokens = lstrip.split()
                    f.write(f"      {tokens[0]}:{basis_name} {{")
                    new_section = False
                else:
                    if lstrip[0] in SHELL_KEYS:
                        tokens = lstrip.lower().split()
                        f.write(f"      {tokens[1]}   {tokens[0]}")
                    else:
                        lstrip = lstrip.lower().replace("d", "e")
                        tokens = lstrip.split()
                        alpha, exp = float(tokens[0]), float(tokens[1])
                        f.write(f"         {alpha:20.12f}    {exp:20.12f}")

            f.write("\n")
        f.write("   }\n}\n")


if __name__ == "__main__":
    main()
