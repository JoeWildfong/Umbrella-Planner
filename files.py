import json
import requests
import ntpath
SAVE_FILE_PATH = "saves/save.json"
PRINT_FILE_PATH = "data.js"
GRID_FILE_PATH = "grid.html"


def load(filename=None):
  global SAVE_FILE_PATH
  if type(filename) is str and filename:
    print("writing filename: " + filename)
    SAVE_FILE_PATH = filename
  try:
    file = open(SAVE_FILE_PATH, "r")
    save_str = file.read()
    save_obj = json.loads(save_str)
    file.close()
    return save_obj
  except:
    return None

def getSaveFile():
  return ntpath.basename(SAVE_FILE_PATH)

def getFullSaveFilePath():
  return SAVE_FILE_PATH

def save(frames, names, sequence_name, filename=None):
  global SAVE_FILE_PATH
  if type(filename) is str and filename:
    print("writing filename: " + filename)
    SAVE_FILE_PATH = filename
  save = dict()
  save["frames"] = frames
  save["names"] = names
  save["sequence"] = sequence_name
  sequence = frames[sequence_name]
  save["rows"] = len(sequence[0])
  save["cols"] = len(sequence[0][0])
  file = open(SAVE_FILE_PATH, "w")
  file.write(json.dumps(save))
  file.close()

def printString(string):
  file = open(PRINT_FILE_PATH, "w")
  file.write(string)
  file.close()

def printArray(ra):
  TEMPLATE = "const allFrames = %s"
  file = open(PRINT_FILE_PATH, "w")
  out = {"data": TEMPLATE % json.dumps(ra)};
  file.write(out["data"])
  file.close()
  requests.post("https://umbrella-script-php.joew3947.repl.co/update.php", data=out)

def printGrid(names):
  out = "<!DOCTYPE html><html><body><table width='100%' height='100%'>"
  for x in names:
    out += "<tr>"
    for y in x:
      out += "<td>" + y + "</td>"
    out += "</tr>"
  out += "</table>"
  out += "<style>td{text-align:center; vertical-align: center}</style>"
  out += "</body></html>"
  file = open(GRID_FILE_PATH, "w")
  file.write(out)
  file.close()