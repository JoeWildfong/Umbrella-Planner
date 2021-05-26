import json
import os

def numberToLetter(number):
  return chr(ord('A') + number)

def toA1(row, col):
  smallest = col - 1
  letter_portion = ""
  letter_portion = numberToLetter(smallest % 26) + letter_portion
  while smallest >= 26:
    smallest = smallest // 26 - 1
    letter_portion = numberToLetter(smallest % 26) + letter_portion
  return letter_portion + str(row)


def fixNames(path):
  data = {}
  with open(path, "r") as f:
    data = json.loads(f.read())
  for row in range(len(data["names"])):
    for col in range(len(data["names"][row])):
      data["names"][row][col] = toA1(row+1, col+1)
  with open(path, "w") as f:
    f.write(json.dumps(data))

if __name__ == "__main__":
  for f in os.scandir("saves"):
    fixNames(f)