from curses import wrapper
import curses.textpad
from time import sleep
import multiprocessing, curses, json, sys, os

sounds = os.listdir(path="sounds/")
# remove random mac cache file
if ".DS_Store" in sounds:
  sounds.remove(".DS_Store")
sounds = sounds[:9]

# uses afplay to play the samples
def play_sequence(sequence, tempo, sounds):
  beats = len(sequence)
  tracks = len(sequence[0])
  while True:
    for beat in range(beats):
      for track in range(tracks):
        if sequence[beat][track]:
          os.system("nohup afplay sounds/{} >/dev/null 2>&1 &".format(sounds[track]))
      sleep(60/tempo)

def handle_hotkey(key):
  if key == 'q':
    sys.exit()
  if key.isdigit():
    n = int(key) - 1
    if n in range(len(sounds)):
      os.system("afplay sounds/{} &".format(sounds[n]))

# list all the available
def display_sounds(stdscr, offset, show_numbers):
  for i in range(len(sounds)):
    name = " ".join(" ".join(".".join(sounds[i].split(".")[:-1]).split("-")).split("_"))
    stdscr.addstr(offset+i, 5, "{} - {}".format(i+1, name) if show_numbers else name)

# simple user input function for getting file names
def file_input(stdscr):
  stdscr.clear()
  stdscr.addstr(2, 5, "Enter filename", curses.A_UNDERLINE)
  stdscr.refresh()
  window = curses.newwin(1, 40, 4, 5)
  input_box = curses.textpad.Textbox(window)
  input_box.edit()
  filename = input_box.gather()
  return filename

# allows users to change the order of sounds in the sampler using the arrow keys
def select_sounds_screen(stdscr):
  global sounds
  available = os.listdir(path="sounds/")
  if ".DS_Store" in available:
    available.remove(".DS_Store")
  available.append("")

  if len(sounds) < len(available) - 1:
    sounds = sounds + [""]*(len(available)-len(sounds))

  initial = list(sounds)
  selected = 0

  while True:
    stdscr.clear()
    stdscr.addstr(2, 5, "Select Sounds", curses.A_UNDERLINE)
    for i in range(len(sounds)):
      stdscr.addstr(4+i, 5, str(i+1))
    for i in range(len(sounds)):
      stdscr.addstr(4+i, 7, "<{}>".format(sounds[i]), curses.color_pair(1) if i is selected else curses.A_NORMAL)

    stdscr.addstr(4+len(sounds)+1, 5, "s - save changes and return to home screen")
    stdscr.addstr(4+len(sounds)+2, 5, "r - revert changes")
    stdscr.addstr(4+len(sounds)+3, 5, "h - return to home screen without saving")
    stdscr.addstr(4+len(sounds)+4, 5, "left and right arrow keys to select sounds")
    stdscr.refresh()
    key = stdscr.getkey()

    if len(key) == 1:
      if key is "s":
        sounds = [sound for sound in sounds if sound != ""]
        return
      elif key is "r":
        sounds = list(initial)
      elif key is "h":
        sounds = list(initial)
        return
      else:
        handle_hotkey(key)
    else:
      if key == "KEY_DOWN":
        selected = (selected + 1) % len(available)
      elif key == "KEY_UP":
        selected = (selected - 1) % len(available)
      elif key == "KEY_RIGHT":
        sounds[selected] = available[(available.index(sounds[selected])+1)%len(available)]
      elif key == "KEY_LEFT":
        sounds[selected] = available[(available.index(sounds[selected])-1)%len(available)]

# main sequencer screen
def sequencer_screen(stdscr):
  global sounds

  error = ""
  offset = max([len(".".join(sound.split(".")[:-1])) for sound in sounds])+8
  playing = False
  tempo = 60
  tracks = len(sounds)
  beats = 8

  sequence = [[False]*tracks for i in range(beats)]
  selected = [0, 0]

  while True:
    stdscr.clear()
    stdscr.addstr(2, 5, "Sequencer", curses.A_UNDERLINE)
    display_sounds(stdscr, 4, False)
    for beat in range(beats):
      for track in range(tracks):
        if beat == 0:
          stdscr.addstr(track+4, offset+beat*2-1, "|")
        stdscr.addstr(track+4, offset+beat*2, "." if sequence[beat][track] else " ", curses.color_pair(1) if [beat, track] == selected else curses.A_NORMAL)
        stdscr.addstr(track+4, offset+beat*2+1, "|")

    stdscr.addstr(tracks+5, 5, "tempo - {}".format(tempo))
    stdscr.addstr(tracks+6, 5, "beats - {}".format(beats))

    tmp_offset = 8
  # display all keyboard shortcuts
    stdscr.addstr(tracks+tmp_offset, 5, "enter  - toggle beat")
    stdscr.addstr(tracks+tmp_offset+1, 5, "arrows - move around")

    stdscr.addstr(tracks+tmp_offset+3, 5, "p - play/plause")
    stdscr.addstr(tracks+tmp_offset+4, 5, "c - clear sequence")
    stdscr.addstr(tracks+tmp_offset+6, 5, "t - tempo up (+5)")
    stdscr.addstr(tracks+tmp_offset+7, 5, "T - tempo down (-5)")
    stdscr.addstr(tracks+tmp_offset+9, 5, "b - add beat to end")
    stdscr.addstr(tracks+tmp_offset+10, 5, "B - remove last beat")
    stdscr.addstr(tracks+tmp_offset+12, 5, "e - export sequence to file")
    stdscr.addstr(tracks+tmp_offset+13, 5, "i - import sequence from file")
    stdscr.addstr(tracks+tmp_offset+15, 5, "h - return to home screen")

    if error != "":
      stdscr.addstr(tracks+tmp_offset+17, 5, error, curses.color_pair(2) | curses.A_BOLD)
      error = ""

    stdscr.refresh()
    key = stdscr.getkey()

  # handle key presses
    if len(key) == 1:
      if key == "h":
        break
      elif key == "p":
        if not playing:
          player_process = multiprocessing.Process(target=play_sequence, args=(sequence, tempo, sounds))
          player_process.start()
        else:
          player_process.terminate()
        playing = not playing
      elif key == "c":
        sequence = [[False]*tracks for i in range(beats)]

      elif key == "t":
        tempo = (tempo + 5) % 1000
      elif key == "T":
        tempo = (tempo - 5) % 1000

      elif key == "b":
        if len(sequence) < 32:
          sequence.append([False]*tracks)
          beats += 1
      elif key == "B":
        if len(sequence) > 1:
          sequence.pop(-1)
          beats -= 1
          if selected[0] >= beats:
            selected[0] = beats - 1

      elif key == "e":
        data = {
          "tempo": tempo,
          "sounds": sounds,
          "beats": beats,
          "tracks": tracks,
          "sequence": sequence
        }
        with open(file_input(stdscr)[:-1], "w") as f:
          f.write(json.dumps(data))
      elif key == "i":
        try:
          with open(file_input(stdscr)[:-1], "r") as f:
            data = json.loads(f.read())
            tempo = data["tempo"]
            sounds = data["sounds"]
            beats = data["beats"]
            tracks = data["tracks"]
            sequence = data["sequence"]
        except:
          error = "no such file"

      elif ord(key) == 10:
        sequence[selected[0]][selected[1]] = not sequence[selected[0]][selected[1]]
      else:
        handle_hotkey(key)

  # handle arrow keys
    elif key == "KEY_UP":
      selected[1] = (selected[1] - 1) % tracks
    elif key == "KEY_DOWN":
      selected[1] = (selected[1] + 1) % tracks
    elif key == "KEY_LEFT":
      selected[0] = (selected[0] - 1) % beats
    elif key == "KEY_RIGHT":
      selected[0] = (selected[0] + 1) % beats

# display home screen
def home_screen(stdscr):
  selected = 0
  menu_items = [["Sequencer", sequencer_screen], ["Select Sounds", select_sounds_screen]]

  while True:
    for i in range(len(menu_items)):
      (stdscr.addstr(2+i, 5, menu_items[i][0], curses.color_pair(1)) if i == selected else stdscr.addstr(2+i, 5, menu_items[i][0]))
    display_sounds(stdscr, 3+len(menu_items), True)
    stdscr.addstr(5+len(sounds)+len(menu_items), 5, "use in full screen, if terminal too small might crash")
    stdscr.refresh()
    key = stdscr.getkey()

    if len(key) == 1:
      if ord(key) == 10:
        menu_items[selected][1](stdscr)
        stdscr.clear()
      else:
        handle_hotkey(key)
    else:
      if key == "KEY_DOWN":
        selected = (selected + 1) % len(menu_items)
      if key == "KEY_UP":
        selected = (selected - 1) % len(menu_items)

def main(stdscr):
  # colour pairs for selected and not selected elements (white fg with black bg and black fg with white bg)
  curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
  curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
  stdscr.clear()
  home_screen(stdscr)

if __name__ == "__main__":
  multiprocessing.set_start_method('spawn')
  wrapper(main)
