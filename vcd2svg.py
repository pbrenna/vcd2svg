#! /usr/bin/env python
"""vcd2svg.

Usage: vcd2svg.py VCDFILE OUTPUT [--sigwidth=<px>] [--sigheight=<px>] SIGNAL [SIGNALS ...] 

--sigwidth	width of signal traces [default: 1000]
--sigheight	height of signal traces	[default: 40]

Signal can be "all", "top" or multiple names of signals.
"""

import sys
from docopt import docopt
import svgwrite
from Verilog_VCD import Verilog_VCD

import draw_signal

arguments = docopt(__doc__, version='0.1')
print(arguments)
fn = arguments['VCDFILE']
data = Verilog_VCD.parse_vcd(fn)
signals = Verilog_VCD.list_sigs(fn)
if arguments['SIGNAL'] not in ("all", "top"):
	signals = arguments['SIGNALS'] + [arguments['SIGNAL']]
if arguments['SIGNAL'] == "top":
	signals = [x for x in signals if x[0] == "."]
signals = [x[1:] if x[0]=="." else x for x in signals]

width = 1000 #px
if arguments['--sigwidth'] is not None:
	width = int(arguments['--sigwidth'])
vscale= 40 #px
if arguments['--sigheight'] is not None:
	vscale = int(arguments['--sigheight'])
labels = 200.5
end_time = Verilog_VCD.get_endtime()
hscale = width / end_time
padding = 20
#determine height
tot_height = vscale*len(signals) + padding * (len(signals) + 3)
s = svgwrite.Drawing(arguments["OUTPUT"],
                     size= (str(width + labels + padding)+"px",
                     str(tot_height) +"px"))
v = padding * 2 - 0.5 # margine superiore
allg = s.g()
for x in data:
	signal = data[x]
	name = signal['nets'][0]['name']
	uglyname = signal['nets'][0]['hier'] + "." + name
	if signal['nets'][0]['hier'] != "":
		name = signal['nets'][0]['hier'] + "." + name
	if name not in signals:
		continue
	print("drawing signal: " + name)
	if ( int(signal['nets'][0]['size'])) == 1:
		group = draw_signal.draw_bin_signal(s, signal['tv'], end_time, vscale, hscale, name, labels)
	else:
		sig = signal['tv']
		group = draw_signal.draw_vec(s, sig, end_time, vscale, hscale, name, labels)
	group.translate(0, v)
	v += vscale + padding
	allg.add(group)
#time things
mults = [(1000000000000000, 'fs'), 
		 (1000000000000, 'ps'),
		 (1000000000, 'ns'),
		 (1000000, 'us'),
		 (1000, 'ms'),
		 (1, 's')]
ts = Verilog_VCD.get_timescale()

suffix = ts[-2:]
suffixes = [x[1] for x in mults]
multiples = [x[0] for x in mults]
if suffix in suffixes:
	prefix = ts[:-2]
	mult = int(prefix) / multiples[suffixes.index(suffix)]
else:
	mult = 1e-15 #default multiplier
	print("Error: can't establish timescale, using 1fs.")

#determine optimal time step
timestep = 1
ticktock = 0
#fit approx width/50 time steps
while (timestep * (width/50) < end_time):	
	timestep *= 5 if ticktock == 0 else 2
	ticktock = not ticktock

#find best unit for timestep
unit = 0
while (timestep * mult >= 1/mults[unit][0]):
	unit = unit + 1
unit = max(unit - 1, 0)

#draw the timesteps
cur_t = 0
tg = s.g()
tg2 = s.g()
while(cur_t < end_time):
	left = round(cur_t / end_time * width)-0.5 #hinting
	rect = s.rect((left, -padding), (1,4), fill="#000000")
	
	#the line must be added in global reference frame
	line = s.line((left+0.5 + labels, v - padding),
				 (left +0.5 + labels, padding*1.5),
				 stroke="#777777",
				 stroke_dasharray="1,3",
				 stroke_width=1)
	#text label of time
	time_label = s.text(str(round(cur_t * mult * mults[unit][0]))
						 + mults[unit][1], (left,0),
						 text_anchor="middle",
						 font_size= 10,
						 font_family="Roboto")
	time_label2 = time_label.copy()
	time_label2['y'] = padding
	tg.add(rect)
	s.add(line)
	tg.add(time_label)
	tg2.add(time_label2)
	cur_t += timestep

tg.translate(labels, v)
tg2.translate(labels, 0)
s.add(tg)
s.add(tg2)
s.add(allg)
s.save(arguments["OUTPUT"])
