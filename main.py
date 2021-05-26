import sys
import pygame
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import tkinter.simpledialog
import tkinter.filedialog
import os.path
import time
import threading
import files

pygame.init()

# constants for various options
CONDENSE_PIXELS = True
TOP_MARGIN_INCLUDES_TOP_BAR = True
CENTER_HORIZONTALLY = True

# constants for generating the display area
SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 800, 400

def percentWidth(percent):
  return SCREEN_WIDTH / 100 * percent

def percentHeight(percent):
  return SCREEN_HEIGHT / 100 * percent

DISPLAY_FLAGS =  pygame.DOUBLEBUF | pygame.HWSURFACE #| pygame.FULLSCREEN

# constants for margins around the grid
TOP_MARGIN = percentHeight(20)
BOTTOM_MARGIN = percentHeight(10)
LEFT_MARGIN = percentWidth(10)
RIGHT_MARGIN = percentWidth(10)
GRID_LEFT_MARGIN = LEFT_MARGIN

# constants for grid dimensions
GRID_DIMS = GRID_COLS, GRID_ROWS = 17,17
GRID_WIDTH = SCREEN_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
GRID_HEIGHT = SCREEN_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN
GRID_SIZE = GRID_WIDTH, GRID_HEIGHT
GRID_GAP = percentWidth(0.7)

# constants for pixel dimensions and spacing

def recalcDims():
  global PIXEL_X_SPACE, PIXEL_Y_SPACE, PIXEL_MIN_SPACE, PIXEL_RADIUS, BOTTOM_MARGIN, GRID_LEFT_MARGIN
  PIXEL_X_SPACE = (GRID_WIDTH + GRID_GAP) / GRID_COLS
  PIXEL_Y_SPACE = (GRID_HEIGHT + GRID_GAP) / GRID_ROWS
  PIXEL_MIN_SPACE = min(PIXEL_X_SPACE, PIXEL_Y_SPACE)
  PIXEL_RADIUS = (PIXEL_MIN_SPACE - GRID_GAP) / 2
  if CONDENSE_PIXELS:
    PIXEL_X_SPACE = PIXEL_Y_SPACE = PIXEL_MIN_SPACE
    BOTTOM_MARGIN = SCREEN_HEIGHT - (TOP_MARGIN + PIXEL_Y_SPACE * GRID_ROWS)
  
  if CENTER_HORIZONTALLY:
    GRID_LEFT_MARGIN = (SCREEN_WIDTH - PIXEL_X_SPACE * GRID_COLS) / 2

recalcDims()

# constants for frame-change arrows
ARROW_MARGIN = percentWidth(0.5)
ARROW_FONT = "dejavusansmono, arial"
ARROW_FONT_SIZE = round(LEFT_MARGIN)
ARROW_ACTIVE_COLOR = (255, 255, 255)
ARROW_INACTIVE_COLOR = (66, 66, 66)

# constants for top bar
TOP_BAR_HEIGHT = TOP_MARGIN
TOP_BAR_PADDING = percentHeight(1)
TOP_BAR_FONT = "freesans, arial"
TOP_BAR_FONT_SIZE = min(round(TOP_BAR_HEIGHT / 3), round(GRID_WIDTH / 20))
TOP_BAR_TEXT_COLOR = (255, 255, 255)
TOP_BAR_LEFT_MARGIN = LEFT_MARGIN
TOP_BAR_RIGHT_MARGIN = RIGHT_MARGIN
TOP_BAR_ELEMENT_PADDING = percentWidth(1)
PLAY_BUTTON_FONT = "dejavusans, segoeuisymbol"
PLAY_BUTTON_FONT_SIZE = min(round(TOP_BAR_HEIGHT / 2), round(GRID_WIDTH / 10))
PLAY_BUTTON_COLOR = (255, 255, 255)
if not TOP_MARGIN_INCLUDES_TOP_BAR:
  TOP_MARGIN += TOP_BAR_HEIGHT

#constants for sequence playback
PLAYBACK_SECONDS_PER_FRAME = 1

# constants for use with pygame's MOUSECLICK event's button property
LEFT_CLICK = 1
RIGHT_CLICK = 3

# constants for use with pygame's MOUSEMOTION event's buttons array
LEFT_MOUSE_BUTTON = 0
RIGHT_MOUSE_BUTTON = 2

# constants for pixel colors
BACKGROUND_COLOR = (0, 0, 0)
PIXEL_OFF_COLOR = (66, 66, 66)
PIXEL_ON_COLOR = (255, 0, 0)
ONIONSKIN_ALPHA = 0.4
ONIONSKIN_COLOR = (
  PIXEL_OFF_COLOR[0] * (1 - ONIONSKIN_ALPHA) + PIXEL_ON_COLOR[0] * ONIONSKIN_ALPHA,
  PIXEL_OFF_COLOR[1] * (1 - ONIONSKIN_ALPHA) + PIXEL_ON_COLOR[1] * ONIONSKIN_ALPHA,
  PIXEL_OFF_COLOR[2] * (1 - ONIONSKIN_ALPHA) + PIXEL_ON_COLOR[2] * ONIONSKIN_ALPHA
) # blend off and on colors according to onionskin alpha value

# constants for keybinding
KEYBINDS = {
  pygame.K_ESCAPE: lambda event: exit(),
  pygame.K_s: lambda event: save(),
  pygame.K_j: lambda event: jumpToFrame(),
  pygame.K_PLUS: lambda event: addFrame(),
  pygame.K_EQUALS: lambda event: addFrame() if event.mod & pygame.KMOD_SHIFT else False,
  pygame.K_DELETE: lambda event: deleteFrame(),
  pygame.K_LEFT: lambda event: changeFrame(-1),
  pygame.K_RIGHT: lambda event: changeFrame(1),
  pygame.K_SPACE: lambda event: toggleSequence(),
  pygame.K_o: lambda event: toggleOnionskin(),
  pygame.K_j: lambda event: jumpToFrame(),
  pygame.K_c: lambda event: clearFrame(),
  pygame.K_f: lambda event: fillFrame(),
  pygame.K_p: lambda event: printInstructions(),
  pygame.K_g: lambda event: printGrid()
}

#constants for right click menu options
def GLOBAL_RIGHT_CLICK_OPTIONS(row=None, col=None):
  cell_arg = "global"
  if type(row) is int and type(col) is int:
    cell_arg = (row, col)

  out = [
    {
      "text": "Save",
      "command": lambda: save()
    },
    {
      "text": "Load file...",
      "command": lambda: loadFile()
    },
    {
      "text": "Generate data.js",
      "command": lambda: printInstructions()
    }
  ]
  global onionskin
  onionskin_text = "Disable onionskin" if onionskin else "Enable onionskin"
  out.append(
    {
      "text": onionskin_text,
      "command": lambda: toggleOnionskin()
    }
  )
  out += [
    {
      "text": "Find unchanged pixels",
      "command": lambda: findUnchanged()
    },
    {
      "text": "Jump to frame...",
      "command": lambda cell_arg=cell_arg: jumpToFrame(cell_arg)
    },
    {
      "text": "Clear current frame",
      "command": lambda cell_arg=cell_arg: clearFrame(cell_arg)
    },
    {
      "text": "Fill current frame",
      "command": lambda cell_arg=cell_arg: fillFrame(cell_arg)
    },
    {
      "text": "Print name grid",
      "command": lambda: printGrid()
    },
    {
      "text": "Resize grid...",
      "command": lambda cell_arg=cell_arg: resizeGrid(cell_arg)
    },
    {
      "text": "New file...",
      "command": lambda: newFile()
    }
  ]
  return out

def RIGHT_CLICK_OPTIONS(row, col):
  out = [
    {
      "text": "Change name...",
      "command": lambda row=row, col=col: changePixelName(row, col)
    }
  ]
  return out


frames = {"sequence 1" : [[]]}
pixel_boxes = []
sequence = frames["sequence 1"]
sequence_name = "sequence 1"
pixel_states = sequence[0]
pixel_names = []

current_frame = 0

arrow_boxes = [None, None]
frame_plus_box = None
frame_minus_box = None
frame_select_box = None
play_button_box = None
sequence_box = None
filename_box = None

current_drag = None

editable = True

onionskin = False

right_click_window = None
sequence_select_window = None

arrow_font = pygame.font.SysFont(ARROW_FONT, ARROW_FONT_SIZE)
bar_font = pygame.font.SysFont(TOP_BAR_FONT, TOP_BAR_FONT_SIZE)
play_font = pygame.font.SysFont(PLAY_BUTTON_FONT, PLAY_BUTTON_FONT_SIZE)

# set up tkinter for right-click menus
root = tk.Tk()
root.wm_withdraw()

screen = pygame.display.set_mode(SCREEN_SIZE, DISPLAY_FLAGS)

def findUnchanged():
  global sequence, GRID_COLS, GRID_ROWS, pixel_names
  closed_out = ""
  open_out = ""
  or_collect = []
  and_collect = []
  for row in range(GRID_ROWS):
    or_collect.append([False] * GRID_COLS)
    and_collect.append([True] * GRID_COLS)
  for frame in sequence:
    for row in range(len(frame)):
      for col in range(len(frame[row])):
        or_collect[row][col] |= frame[row][col]
        and_collect[row][col] &= frame[row][col]
  for row in range(len(frame)):
    for col in range(len(frame[row])):
      if not or_collect[row][col]:
        closed_out += " " + pixel_names[row][col]
      if and_collect[row][col]:
        open_out += " " + pixel_names[row][col]
  if closed_out == "":
    closed_out = " None"
  if open_out == "":
    open_out = " None"
  out = "Always closed:" + closed_out + "\n" + \
        "Always open:" + open_out
  tk.messagebox.showinfo("Unchanged pixels", out)

def drawGrid(states, arrows = True, top_bar = True):
  global onionskin, pixel_boxes
  screen.fill(BACKGROUND_COLOR)
  local_onionskin = onionskin
  prev_frame_states = None
  if (not states) or current_frame == 0:
    local_onionskin = False
  else:
    prev_frame_states = sequence[current_frame - 1]
  
  pixel_boxes = []
  for row in range(GRID_ROWS):
    row_boxes = []
    for col in range(GRID_COLS):
      xdraw = round(GRID_LEFT_MARGIN + col * PIXEL_X_SPACE + PIXEL_RADIUS)
      ydraw = round(TOP_MARGIN + row * PIXEL_Y_SPACE + PIXEL_RADIUS)
      pixel_color = PIXEL_OFF_COLOR
      if states and states[row][col]:
        pixel_color = PIXEL_ON_COLOR
      elif local_onionskin and prev_frame_states[row][col]:
        pixel_color = ONIONSKIN_COLOR
      box = pygame.draw.circle(
        screen,
        pixel_color,
        (xdraw, ydraw),
        round(PIXEL_RADIUS))
      row_boxes.append(box)
    pixel_boxes.append(row_boxes)

  if arrows:
    drawArrows(False)
  
  if top_bar:
    drawTopBar(False)
  
  pygame.display.flip()

def drawArrows(flip = True):
  if not editable:
    return
  
  left_arrow_color = ARROW_INACTIVE_COLOR
  left_arrow_active = False
  if current_frame > 0:
    left_arrow_color = ARROW_ACTIVE_COLOR
    left_arrow_active = True
  left_arrow = arrow_font.render("<", True, left_arrow_color)
  left_arrow_coords = (round(ARROW_MARGIN),
                       round(SCREEN_HEIGHT / 2 - left_arrow.get_height() / 2))
  left_arrow_box = screen.blit(left_arrow, left_arrow_coords)
  if left_arrow_active:
    arrow_boxes[0] = left_arrow_box
  else:
    arrow_boxes[0] = None
  
  right_arrow_color = ARROW_INACTIVE_COLOR
  right_arrow_active = False
  if current_frame < len(sequence) - 1:
    right_arrow_color = ARROW_ACTIVE_COLOR
    right_arrow_active = True
  right_arrow = arrow_font.render(">", True, right_arrow_color)
  right_arrow_coords = (round(SCREEN_WIDTH - right_arrow.get_width() - ARROW_MARGIN),
                        round(SCREEN_HEIGHT / 2 - right_arrow.get_height() / 2))
  right_arrow_box = screen.blit(right_arrow, right_arrow_coords)
  if right_arrow_active:
    arrow_boxes[1] = right_arrow_box
  else:
    arrow_boxes[1] = None

  if flip:
    pygame.display.flip()

def drawTopBar(flip=True):
  global frame_minus_box, frame_plus_box, play_button_box, sequence_box, frame_select_box, filename_box
  screen.fill(BACKGROUND_COLOR, (0, 0, SCREEN_WIDTH, round(TOP_BAR_HEIGHT)))
  num_frames = len(sequence)
  frame_count_text = bar_font.render(
    "Frames: " + str(num_frames),
    True,
    TOP_BAR_TEXT_COLOR
  )
  minus_color = TOP_BAR_TEXT_COLOR
  if num_frames == 1:
    minus_color = ARROW_INACTIVE_COLOR
  frame_minus = bar_font.render("-", True, minus_color)
  frame_plus = bar_font.render("+", True, TOP_BAR_TEXT_COLOR)
  draw_pos = (
    round(TOP_BAR_LEFT_MARGIN),
    round(TOP_BAR_HEIGHT - TOP_BAR_PADDING - frame_count_text.get_height())
  )
  minus_box = screen.blit(frame_minus, draw_pos)
  if minus_color == TOP_BAR_TEXT_COLOR:
    frame_minus_box = minus_box
  else:
    frame_minus_box = None
  draw_pos = (
    round(draw_pos[0] + frame_minus.get_width() + TOP_BAR_ELEMENT_PADDING),
    draw_pos[1]
  )
  screen.blit(frame_count_text, draw_pos)
  draw_pos = (
    round(draw_pos[0] + frame_count_text.get_width() + TOP_BAR_ELEMENT_PADDING),
    draw_pos[1]
  )
  frame_plus_box = screen.blit(frame_plus, draw_pos)

  current_frame_text = bar_font.render("Frame " + str(current_frame + 1) + " of " + str(num_frames), True, TOP_BAR_TEXT_COLOR)
  draw_pos = (round(SCREEN_WIDTH - TOP_BAR_RIGHT_MARGIN - current_frame_text.get_width()),
              round(draw_pos[1]))
  frame_select_box = screen.blit(current_frame_text, draw_pos)

  play_text = u"\u25B6" if editable else u"\u25AE\u25AE"
  play_button = play_font.render(play_text, True, PLAY_BUTTON_COLOR)
  draw_pos = (round(SCREEN_WIDTH / 2 - play_button.get_width() / 2),
             round(TOP_MARGIN - TOP_BAR_PADDING - play_button.get_height()))
  play_button_box = screen.blit(play_button, draw_pos)

  sequence_text = bar_font.render(sequence_name, True, TOP_BAR_TEXT_COLOR)
  draw_pos = (
    round(SCREEN_WIDTH / 2 - sequence_text.get_width() / 2),
    round(TOP_MARGIN - TOP_BAR_HEIGHT + TOP_BAR_PADDING)
  )
  sequence_box = screen.blit(sequence_text, draw_pos)

  current_file_text = bar_font.render(files.getSaveFile(), True, TOP_BAR_TEXT_COLOR)
  draw_pos = (round(TOP_BAR_LEFT_MARGIN), draw_pos[1])
  filename_box = screen.blit(current_file_text, draw_pos)

  if flip:
    pygame.display.flip()

def changeFrame(rel = 0, **kwargs):
  global current_frame, pixel_states, sequence
  new_frame = current_frame + rel
  if rel == 0 and "absolute" in kwargs:
    new_frame = kwargs["absolute"]
  if new_frame < 0 or new_frame >= len(sequence):
    return
  current_frame = new_frame
  pixel_states = sequence[current_frame]
  drawGrid(pixel_states)

def changeSequence(name):
  global sequence_name, sequence
  clearSequenceSelect()
  sequence_name = name
  sequence = frames[name]
  changeFrame(absolute=0)

def clearSequenceSelect():
  global sequence_select_window
  if sequence_select_window is not None:
    sequence_select_window.destroy()
    sequence_select_window = None

def newSequence():
  clearSequenceSelect()
  good_name = False
  extra_text = ""
  name = ""
  while not good_name:
    name = tk.simpledialog.askstring("Name", extra_text + "\nEnter the new sequence's name:")
    if name == None:
      selectSequence()
      return
    if name == "":
      extra_text = "Name cannot be blank."
    elif name in [*frames]:
      extra_text = "Sequence ''" + name + "'' already exists."
    else:
      good_name = True
  new_grid = []
  for i in range(GRID_ROWS):
    new_grid.append([False] * GRID_COLS)
  frames[name] = [new_grid]
  changeSequence(name)

def centerWindow(toplevel):
  toplevel.withdraw()
  try:
    root.eval('tk::PlaceWindow %s center' % toplevel.winfo_pathname(toplevel.winfo_id()))
  except:
    print("PlaceWindow not supported.")
  toplevel.deiconify()
  toplevel.attributes('-topmost', 1)
  toplevel.focus_force()
  toplevel.update()
  toplevel.attributes('-topmost', 0)
  return toplevel

def renameSequence(sub):
  clearSequenceSelect()
  global frames
  good_name = False
  name = ""
  extra_text = ""
  while not good_name:
    name = tk.simpledialog.askstring("Rename", extra_text + "\nEnter the new name for the sequence '%s':" % sub)
    if name == None:
      sequenceAction(sub)
      return
    if name == "":
      extra_text = "Name cannot be blank."
    elif name in [*frames]:
      extra_text = "Sequence ''" + name + "'' already exists."
    else:
      good_name = True
  frames[name] = frames[sub]
  del frames[sub]

def deleteSequence(sub):
  clearSequenceSelect()
  confirm = tk.messagebox.askyesno("Delete?", "Are you sure you want to delete the sequence '%s'?" % sub)
  if confirm:
    del frames[sub]
  else:
    sequenceAction(sub)

def sequenceAction(sub):
  global sequence_select_window
  clearSequenceSelect()
  sequence_select_window = centerWindow(tk.Toplevel())
  sequence_select_window.protocol("WM_DELETE_WINDOW", clearSequenceSelect)
  sequence_select_window.title("Change sequence...")
  sequence_select_window.grid_columnconfigure(0, weight=1)
  sequence_select_window.grid_rowconfigure(0, weight=1)
  top_frame = ttk.Frame(sequence_select_window, padding='5')
  top_frame.grid_columnconfigure(0, weight=1)
  top_frame.grid(row=0, column=0, sticky='nsew')
  ttk.Label(
    top_frame,
    text='Sequence: ' + sub,
    anchor='center'
  ).grid(row=0, column=0, sticky='new', pady='0 10')
  ttk.Button(
    top_frame,
    text="Switch to",
    command=lambda sub=sub: changeSequence(sub)
  ).grid(row=1, column=0, sticky='ew')
  ttk.Button(
    top_frame,
    text="Rename",
    command=lambda sub=sub: renameSequence(sub)
  ).grid(row=2, column=0, sticky='ew')
  ttk.Button(
    top_frame,
    text="Delete",
    command=lambda sub=sub: deleteSequence(sub)
  ).grid(row=3, column=0, sticky='ew')
  ttk.Button(
    top_frame,
    text="Back",
    command=lambda: selectSequence()
  ).grid(row=4, column=0, sticky='ew', pady='10 0')

def selectSequence():
  global sequence_select_window
  clearSequenceSelect()
  sequence_select_window = centerWindow(tk.Toplevel())
  sequence_select_window.protocol("WM_DELETE_WINDOW", clearSequenceSelect)
  sequence_select_window.title("Change sequence...")
  sequence_select_window.grid_columnconfigure(0, weight=1)
  sequence_select_window.grid_rowconfigure(0, weight=1)
  top_frame = ttk.Frame(sequence_select_window, padding='5')
  top_frame.grid_columnconfigure(0, weight=1)
  top_frame.grid(row=0, column=0, sticky='nsew')
  ttk.Label(
    top_frame,
    text='Current sequence: ' + sequence_name,
    anchor='center'
  ).grid(row=0, column=0, sticky='new', pady='0 10')
  ttk.Label(
    top_frame,
    text='Other sequences:',
    anchor='center'
  ).grid(row=1, column=0, sticky='ew')
  sequence_names = [*frames]
  if len(sequence_names) == 1:
    ttk.Label(top_frame, text='No other sequences.', anchor='center').grid(row=2, column=0, sticky='ew')
  else:
    for i in range(len(sequence_names)):
      if sequence_names[i] == sequence_name:
        continue
      ttk.Button(
        top_frame,
        text=sequence_names[i],
        command=lambda i=i: sequenceAction(sequence_names[i])
      ).grid(row=i+2, column=0, sticky='ew')
  ttk.Button(
    top_frame,
    text="New sequence...",
    command=newSequence
  ).grid(row=len(sequence_names)+2, column=0, sticky='ew', pady='10 0')

def toggleSequence():
  global editable
  if editable:
    playSequence()
  else:
    stopSequence()

def playSequence():
  global editable
  editable = False
  drawGrid(pixel_states)
  def cycleFrames():
    while current_frame < len(sequence) - 1:
      global editable
      time.sleep(PLAYBACK_SECONDS_PER_FRAME)
      if editable:
        break
      changeFrame(1)
    editable = True
    drawGrid(pixel_states)
  threading.Thread(target = cycleFrames).start()

def stopSequence():
  global editable
  editable = True
  drawGrid(pixel_states)
  
def deleteFrame():
  if len(sequence) == 1:
    return
  if current_frame == len(sequence) - 1:
    changeFrame(-1)
  sequence.pop()
  drawGrid(pixel_states)

def addFrame():
  new_frame = []
  for row in range(GRID_ROWS):
    new_frame.append([False] * GRID_COLS)
  sequence.append(new_frame)
  drawArrows(False)
  drawTopBar()

def togglePixel(row, col, box=None):
  draw_color = None
  if box == None:
    box = pixel_boxes[row][col]
  if pixel_states[row][col]:
    pixel_states[row][col] = False
    draw_color = PIXEL_OFF_COLOR
    if onionskin and current_frame > 0 and sequence[current_frame - 1][row][col]:
      draw_color = ONIONSKIN_COLOR
  else:
    pixel_states[row][col] = True
    draw_color = PIXEL_ON_COLOR
  pygame.draw.circle(screen, draw_color, box.center, round(PIXEL_RADIUS))
  pygame.display.flip()

PRINT_TEMPLATE = """
[[contents]]
"""

def printPixel(row, col):
  out = dict()
  for sub in [*frames]:
    sub_states = []
    for frame in frames[sub]:
      sub_states.append(frame[row][col])
    out[sub] = sub_states
  return out

def printInstructions(pixels=None):
  clearRightClickMenu()
  clearSequenceSelect()
  instructions = dict()
  if pixels is None:
    for row in range(GRID_ROWS):
      for col in range(GRID_COLS):
        instructions[pixel_names[row][col]] = printPixel(row, col)
  else:
    for pixel in pixels:
      instructions[pixel_names[pixel[0]][pixel[1]]] = printPixel(pixel[0], pixel[1])
  files.printArray(instructions)

def printGrid():
  files.printGrid(pixel_names)
  tk.messagebox.showinfo("Printed", "Printed name grid.")

def determineTarget(pos):
  special_boxes = {
    "left arrow": arrow_boxes[0],
    "right arrow": arrow_boxes[1],
    "frame minus": frame_minus_box,
    "frame plus": frame_plus_box,
    "play button": play_button_box,
    "sequence name": sequence_box,
    "frame select": frame_select_box,
    "file select": filename_box
  }
  for box in special_boxes:
    if special_boxes[box] != None:
      if special_boxes[box].collidepoint(pos):
        return box
  for row in range(len(pixel_boxes)):
    for col in range(len(pixel_boxes[row])):
      box = pixel_boxes[row][col]
      if box.collidepoint(pos):
        return row, col, box
  return None


def handleLeftClick(pos):
  global current_drag, editable
  target = determineTarget(pos)
  if target == None:
    current_drag = None
    return
  if target == "play button":
    if editable:
      playSequence()
    else:
      stopSequence()
  if editable:
    if target == "left arrow":
      changeFrame(-1)
      return
    elif target == "right arrow":
      changeFrame(1)
    elif target == "frame minus":
      deleteFrame()
    elif target == "frame plus":
      addFrame()
    elif target == "sequence name":
      selectSequence()
    elif target == "frame select":
      jumpToFrame()
    elif target == "file select":
      loadFile(True)
    
    elif type(target) is tuple:
      row, col, box = target
      togglePixel(row, col, box)
      current_drag = row, col

def resizeGrid(from_right_click = None, flip=True):
  global GRID_DIMS, GRID_COLS, GRID_ROWS, frames, sequence, pixel_states
  clearRightClickMenu()
  width = tk.simpledialog.askinteger("Enter width", "Enter the new grid width")
  if width is not None and width > 0:
    height = tk.simpledialog.askinteger("Enter height", "Enter the new grid height")
    if height is not None and height > 0:
      for sub in frames:
        for frame in frames[sub]:
          height_diff = height - len(frame)
          height_op = (lambda width=width: frame.append([False] * width)) if height_diff > 0 else (lambda: frame.pop())
          for i in range(abs(height_diff)):
            height_op()
          for row in frame:
            width_diff = width - len(row)
            width_op = (lambda: row.append(False)) if width_diff > 0 else (lambda: row.pop())
            for i in range(abs(width_diff)):
              width_op()
      GRID_DIMS = GRID_COLS, GRID_ROWS = width, height
      recalcDims()
      generateNames()
      if flip:
        drawGrid(pixel_states)
      return
  if from_right_click == "global":
    globalRightClickMenu()
  elif type(from_right_click) is tuple:
    rightClickMenu(from_right_click[0], from_right_click[1])

def clearFrame(from_right_click = None):
  global pixel_states
  clearRightClickMenu()
  clearSequenceSelect()
  confirm = tk.messagebox.askyesno("Clear frame?", "Clear the current frame (irreversible)?")
  if confirm:
    for row in range(GRID_ROWS):
      for col in range(GRID_COLS):
        pixel_states[row][col] = False
  elif from_right_click == "global":
    globalRightClickMenu()
  elif type(from_right_click) is tuple:
    rightClickMenu(from_right_click[0], from_right_click[1])
  drawGrid(pixel_states)

def fillFrame(from_right_click = None):
  global pixel_states
  clearRightClickMenu()
  clearSequenceSelect()
  confirm = tk.messagebox.askyesno("Fill frame?", "Fill the current frame (irreversible)?")
  if confirm:
    for row in range(GRID_ROWS):
      for col in range(GRID_COLS):
        pixel_states[row][col] = True
  elif from_right_click == "global":
    globalRightClickMenu()
  elif type(from_right_click) is tuple:
    rightClickMenu(from_right_click[0], from_right_click[1])
  drawGrid(pixel_states)

def toggleOnionskin():
  global onionskin
  clearRightClickMenu()
  onionskin = not onionskin
  drawGrid(pixel_states)

def jumpToFrame(from_right_click = None):
  clearRightClickMenu()
  clearSequenceSelect()
  good_answer = False
  extra_text = ""
  while not good_answer:
    new_frame = tk.simpledialog.askinteger("Jump to frame", extra_text + "\nEnter a frame number to jump to between 1 and %s" % len(sequence))
    if new_frame is None:
      if from_right_click == "global":
        globalRightClickMenu()
      elif type(from_right_click) is tuple:
        rightClickMenu(from_right_click[0], from_right_click[1])
      return
    elif new_frame <= 0 or new_frame > len(sequence):
      extra_text = "Frame number out of bounds."
    else:
      good_answer = True
  
  changeFrame(absolute=new_frame - 1)


def changePixelName(row, col):
  clearRightClickMenu()
  newName = tk.simpledialog.askstring("Change name...", "Enter the new pixel name:")
  if newName is None:
    rightClickMenu(row, col)
    return
  pixel_names[row][col] = newName

def clearRightClickMenu():
  global right_click_window
  if right_click_window is not None:
    right_click_window.destroy()
    right_click_window = None

def rightClickMenu(row, col):
  global right_click_window
  clearRightClickMenu()
  right_click_window = centerWindow(tk.Toplevel())
  right_click_window.protocol("WM_DELETE_WINDOW", clearRightClickMenu)
  right_click_window.title("Menu")
  right_click_window.grid_columnconfigure(0, weight=1)
  right_click_window.grid_rowconfigure(0, weight=1)
  top_frame = ttk.Frame(right_click_window, padding='5')
  top_frame.grid_columnconfigure(0, weight=1)
  top_frame.grid(row=0, column=0, sticky='nsew')
  ttk.Label(
    top_frame,
    text="%s (row %d, column %d)" % (pixel_names[row][col], row + 1, col + 1),
    anchor="center"
  ).grid(row=0, column=0, sticky="new", pady="0 10")
  options = RIGHT_CLICK_OPTIONS(row, col)
  rowCount = 1
  for i in options:
    ttk.Button(
      top_frame,
      text=i["text"],
      command=i["command"]
    ).grid(row=rowCount, column=0, sticky='ew')
    rowCount += 1
  global_options = GLOBAL_RIGHT_CLICK_OPTIONS(row, col)
  padding = "10 0"
  for i in global_options:
    ttk.Button(
      top_frame,
      text=i["text"],
      command=i["command"]
    ).grid(row=rowCount, column=0, pady=padding, sticky='ew')
    rowCount += 1
    padding = "0 0"

def globalRightClickMenu():
  global right_click_window
  clearRightClickMenu()
  right_click_window = centerWindow(tk.Toplevel())
  right_click_window.protocol("WM_DELETE_WINDOW", clearRightClickMenu)
  right_click_window.title("Menu")
  right_click_window.grid_columnconfigure(0, weight=1)
  right_click_window.grid_rowconfigure(0, weight=1)
  top_frame = ttk.Frame(right_click_window, padding='5')
  top_frame.grid_columnconfigure(0, weight=1)
  top_frame.grid(row=0, column=0, sticky='nsew')
  ttk.Label(
    top_frame,
    text="No pixel selected",
    anchor="center"
  ).grid(row=0, column=0, sticky="new", pady="0 10")
  rowCount = 1
  global_options = GLOBAL_RIGHT_CLICK_OPTIONS()
  for i in global_options:
    ttk.Button(
      top_frame,
      text=i["text"],
      command=i["command"]
    ).grid(row=rowCount, column=0, sticky='ew')
    rowCount += 1


def handleRightClick(pos):
  target = determineTarget(pos)
  if type(target) is tuple:
    rightClickMenu(target[0], target[1])
  else:
    globalRightClickMenu()
  return

def handleClickDrag(pos):
  global current_drag
  target = determineTarget(pos)
  if (type(target)) is not tuple:
    current_drag = None
    return
  row, col, box = target
  if (row, col) == current_drag:
    return
  togglePixel(row, col, box)
  current_drag = row, col

def save():
  response = tk.messagebox.askyesno("Save?", "Would you like to save?")
  if response:
    files.save(frames, pixel_names, sequence_name)
    clearRightClickMenu()

def loadFile(askLate=False):
  if not askLate:
    toSave = tk.messagebox.askyesnocancel("Save?", "Would you like to save before opening another file?")
    if toSave is None:
      return
    elif toSave == True:
      files.save(frames, pixel_names, sequence_name)
  filename = tk.filedialog.askopenfilename(initialdir="saves")
  if filename:
    if os.path.realpath(filename) == os.path.realpath(files.getFullSaveFilePath()):
      return
    if askLate:
      toSave = tk.messagebox.askyesnocancel("Save?", "Would you like to save before opening another file?")
    if toSave is None:
      return
    elif toSave == True:
      files.save(frames, pixel_names, sequence_name)
    loadSave(files.load(filename))
  clearRightClickMenu()

def newFile():
  toSave = tk.messagebox.askyesnocancel("Save?", "Would you like to save before creating a new file?")
  if toSave is None:
    return
  elif toSave == True:
    files.save(frames, pixel_names, sequence_name)
  filename = tk.filedialog.asksaveasfilename(initialdir="saves", defaultextension=".json")
  if not filename:
    return
  generateGrid(GRID_ROWS, GRID_COLS)
  resizeGrid(None, False)
  files.save(frames, pixel_names, sequence_name, filename)
  drawGrid(pixel_states)
  
  

def exit():
  response = tk.messagebox.askyesnocancel("Save?", "Would you like to save before quitting?")
  if response == True:
    files.save(frames, pixel_names, sequence_name)
  elif response == None:
    return # cancel clicked, don't exit
  global editable
  editable = False
  clearRightClickMenu()
  clearSequenceSelect()
  root.destroy()
  pygame.quit()
  sys.exit()

def handleEvents():
  for event in pygame.event.get():
    if event.type == pygame.QUIT:
      exit()
    elif event.type == pygame.KEYDOWN:
      for bind in KEYBINDS:
        if event.key == bind:
          KEYBINDS[bind](event)
    elif event.type == pygame.MOUSEBUTTONDOWN:
      if event.button == LEFT_CLICK:
        handleLeftClick(event.pos)
        continue
      elif event.button == RIGHT_CLICK:
        handleRightClick(event.pos)
        continue
    elif event.type == pygame.MOUSEMOTION and event.buttons[LEFT_MOUSE_BUTTON]:
        handleClickDrag(event.pos)

done = False

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


def generateGrid(rows, cols):
  global GRID_ROWS, GRID_COLS, pixel_names, frames, sequence, pixel_states
  GRID_ROWS = rows
  GRID_COLS = cols
  pixel_states = []
  pixel_names = []
  for row in range(GRID_ROWS):
    pixel_states.append([False] * GRID_COLS)
    row_names = []
    for col in range(GRID_COLS):
      row_names.append(toA1(row + 1, col + 1))
    pixel_names.append(row_names)
  sequence = [pixel_states]
  frames = []
  frames["sequence 1"] = sequence
  changeSequence("sequence 1")

def generateNames():
  global GRID_ROWS, GRID_COLS, pixel_names
  pixel_names = []
  for row in range(GRID_ROWS):
    row_names = []
    for col in range(GRID_COLS):
      row_names.append(toA1(row + 1, col + 1))
    pixel_names.append(row_names)

# draw grid
def loadSave(loaded_save):
  global GRID_ROWS, GRID_COLS, pixel_names, frames
  if loaded_save == None:
    generateGrid(GRID_ROWS, GRID_COLS)
    drawGrid(pixel_states)
  else:
    frames = loaded_save["frames"]
    GRID_COLS = loaded_save["cols"]
    GRID_ROWS = loaded_save["rows"]
    recalcDims()
    pixel_names = loaded_save["names"]
    changeSequence(loaded_save["sequence"])

# load save if it exists
loadSave(files.load())

while not done:
  handleEvents()
  root.update()