#! /usr/bin/env python
"""vcd2svg.

Usage: vcd2svg.py VCDFILE OUTPUT [--sigwidth=<px>] [--sigheight=<px>] SIGNAL [SIGNALS ...] 

--sigwidth	width of signal traces [default: 1000]
--sigheight	height of signal traces	[default: 40]

Signal can be "all", "top" or multiple names of signals.
"""

import sys
import os
from docopt import docopt
import svgwrite
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + "/Verilog_VCD/")
from Verilog_VCD import Verilog_VCD

import draw_signal

arguments = docopt(__doc__, version='0.1')
fn = arguments['VCDFILE']
data = Verilog_VCD.parse_vcd(fn)
signals = Verilog_VCD.list_sigs(fn)
if arguments['SIGNAL'] not in ("all", "top"):
	signals = [arguments['SIGNAL']] + arguments['SIGNALS']
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
found_signals = []
found_signals_ugly = []
found_signals_basenames = []
found_signals_tv = []
found_signals_type = []
for x in data:
	try:
		found_signals_tv.append(data[x]['tv'])
		sig_name = data[x]['nets'][0]['name']
		found_signals.append(sig_name)
		sig_type = data[x]['nets'][0]['type']
		found_signals_type.append(sig_type)
		sig_ugly = data[x]['nets'][0]['hier'] + "." + sig_name
		if sig_ugly[0] != ".":
			sig_ugly = "." + sig_ugly
		found_signals_ugly.append(sig_ugly)
		found_signals_basenames.append(sig_ugly.split("[")[0])
	except KeyError:
		pass
	
for c in signals: #segnali richiesti
	c_ugly = "." + c
	c_parts = c_ugly.split("[")
	c_bname = c_parts[0]
	#signal = data[x]
	#name = signal['nets'][0]['name']
	#uglyname = signal['nets'][0]['hier'] + "." + name
	#if signal['nets'][0]['hier'] != "":
	#	name = signal['nets'][0]['hier'] + "." + name
	#basename = name.split("[")[0] #senza [1:3] ad esmepio
	reverse = False
	try:
		sig_index = found_signals_basenames.index(c_bname)
	except ValueError:
		print("not found or empty: " + c_bname)
		continue
	sig_ugly = found_signals_ugly[sig_index]
	sig_type = found_signals_type[sig_index]
	if sig_type == "reg":
		try:
			#default: use all indexes in signal
			indexes = list(map(int, sig_ugly.split("[")[1][:-1].split(":")))
			if indexes[0] > indexes[1]:
				reverse = True
		except IndexError:
			#single signal
			indexes = [0]
		size = max(indexes) + 1
		if len(c_parts) > 1:
			#read requested signals
			indexes = map(int, c_parts[1][:-1].split(":"))
			indexes = list(indexes)
		elif len(indexes) > 1: 
			c += "["+ ":".join(map(str,indexes)) +"]"
	
		if len(indexes) > 1:
			direction = +1 if indexes[0] < indexes[1] else -1
			rng = list(range(indexes[0], indexes[1]+direction, direction))
		else:
			rng = indexes
		if reverse:
			rng = [size-x-1 for x in rng]
		print("drawing signal: " + c + ", with indexes "+ str(rng) )
		try:
			sig = found_signals_tv[sig_index] 
		except KeyError:
			print(" -> skipping empty signal: " + c)
		else:
			if len(rng) == 1:
				group = draw_signal.draw_bin_signal(s, sig, rng[0], end_time,
					                                vscale, hscale, c,
					                                labels)
			else:
				group = draw_signal.draw_vec(s, sig, rng, end_time, vscale,
					                         hscale, c, labels)

	elif sig_type in ("string", "integer"):
		try:
			sig = found_signals_tv[sig_index] 
		except KeyError:
			print(" -> skipping empty signal: " + c)
			continue
		group = draw_signal.draw_vec(s, sig, [], end_time, vscale,
		                                hscale, c, labels)
	else:
		print("unsuppoted signal type: " + sig_type)
		continue
	group.translate(0, v)
	v += vscale + padding
	allg.add(group)
#time things
mults = [(1000000000000000, 'fs'), 
		 (1000000000000, 'ps'),
		 (1000000000, 'ns'),
		 (1000000, 'us'),
		 (1000, 'ms'),
		 (1, 's'),
		 (0.001, 'Ks')]
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
ticktocktack = 0
#fit approx width/50 time steps
#we like numbers of the form {2, 5, 10} * 10^x
while (timestep * (width/50) < end_time):	
	timestep *= 2.5 if ticktocktack == 1 else 2
	ticktocktack = (ticktocktack + 1) % 3

#find best unit for timestep
unit = 0
while (timestep * mult >= 1/mults[unit][0] and unit < len(mults)-1):
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
print("writing file...")
s.save(arguments["OUTPUT"])
