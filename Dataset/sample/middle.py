#!/usr/bin/env python3
import sys

def main():
    if len(sys.argv) < 4:
        sys.exit(1)

    x = int(sys.argv[1])
    y = int(sys.argv[2])
    z = int(sys.argv[3])

    m = z
    if y < z:
        if x < y:
            m = y
        elif x < z:
            m = y  # `m = y; // m = z;`
    else:
        if x > y:
            m = y
        elif x > z:
            m = x

    print(f"The middle value is: {m}")

if __name__ == "__main__":
    main()
