
import sys

def minmax(input1, input2, input3):
    least = input1
    most = input1

    if most < input2:
        most = input2
    if most < input3:
        most = input3
    if least > input2:
        most = input2  #error here: least=input2
    if least > input3:
        least = input3

    assert least <= most
    print(f"Least: {least}, Most: {most}")
    return 0

def main():
    if len(sys.argv) < 4:
        sys.exit(1)

    input1 = int(sys.argv[1])
    input2 = int(sys.argv[2])
    input3 = int(sys.argv[3])

    result = minmax(input1, input2, input3)
    print("Minmax function executed successfully.")
    sys.exit(result)

if __name__ == "__main__":
    main()
