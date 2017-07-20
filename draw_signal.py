import svgwrite
import random

def indefinito(ran, vscale):
	dati = [(0, 0)]
	for x in ran:
		rnumb = random.random() * vscale
		dati.append((x, rnumb))
	return dati

def draw_vec(s, sig, rng, totl, vscale, hscale, name, labels):
	outer = s.g()
	g = s.g()
	font_size= 10
	
	if sig[0][0] != 0:
		sig = [(0, 'undefined sig.')] + sig
	count = 0
	inc = 3
	pathd = ""
	oldtime = 0
	txtg = s.g()
	for point in sig:
		#top part and descending line
		pathd += "M " + str(oldtime + inc) + " 0"
		pathd += "L " + str(max(point[0] * hscale - inc, 0)) + " 0"
		if count > 0:
			pathd += "L" + str(point[0] * hscale + inc) + " " + str(vscale)
		#bottom part and rising line
		pathd += "M " + str(oldtime + inc) + " " + str(vscale)
		pathd += "L " + str(max(point[0] * hscale - inc, 0)) + " " + str(vscale)
		if count > 0:
			pathd += "L" + str(point[0] * hscale + inc) + " 0"
		#get center:
		try:
			fine = sig[count+1][0]
		except IndexError:
			fine = totl
		center = (fine - point[0]) * hscale / 2
		#add text with signal value
		if rng != []:
			value_txt = "".join([point[1][x] for x in rng])
		else:
			value_txt = str(point[1])
		txt = s.text(value_txt, (point[0] * hscale + center, vscale/2 + font_size*.4), font_family="Roboto", font_size= font_size, text_anchor = "middle")
		txtg.add(txt)
		oldtime = point[0] * hscale
		count += 1
	#conclude disegno
	pathd += "M " + str(oldtime + inc) + " 0" 
	pathd += "L " + str(totl*hscale) + " 0"
	pathd += "M " + str(oldtime + inc) + " " + str(vscale) 
	pathd += "L " + str(totl*hscale) + " " + str(vscale) 
	
	path = s.path(d = pathd, stroke="#000000", stroke_width = "1", fill="none")

	decorate(s, name, totl, vscale, hscale, None, None, g, labels)
	g.add(path)
	g.add(txtg)
	return g

def draw_bin_signal(s, sig, ind, totl, vscale, hscale, name, labels):
	g = s.g()
	font_size= 10
	#normalize data points in 1:0 for drawing purposes
	punti = [float(x[1][ind]) for x in sig]
	sigmin = min(punti)
	punti = [x - sigmin for x in punti]
	sigmax = max(punti)
	if sigmax == 0:
		sigmax = 1 #hack
	punti = [(1 - (x / sigmax)) * vscale for x in punti]
	
	oldv = 0
	if sig[0][0] != 0:
		#segnale indefinito
		try:
			fine = sig[0][0]
		except IndexError:
			fine = totl
		rumore = indefinito(range(0, fine, int(5/hscale)), vscale) 
		punti = [x[1] for x in rumore] + punti
		sig = rumore + sig
		oldv = rumore[-1][1]
	count = 0
	pathd = "M0 1"
	for point in sig:
		pathd += " L" + str(point[0] * hscale) + " " + str(oldv) 
		pathd += " L" + str(point[0] * hscale) + " " + str(punti[count])
		oldv = punti[count]
		count += 1
	pathd += " L" + str(totl * hscale) + " " + str(punti[-1])
	
	path = s.path(d = pathd, stroke="#000000", stroke_width = "1", fill="none")
	decorate(s, name, totl, vscale, hscale, sigmin, sigmax, g, labels)
	g.add(path)
	return g

def decorate(s, name, totl, vscale, hscale, sigmin, sigmax, g, labels):
	font_size = 10
	font = "Roboto"
	rect = s.rect((0, 0), (totl*hscale, vscale),
	              stroke="#777777",
	              stroke_width=1,
	              fill = "#ffffff", 
	              stroke_dasharray="1,2")
	if sigmin is not None:
		min_label = s.text(str(sigmin),(- 5, vscale),
		                   text_anchor = "end",
		                   font_size = font_size,
		                   font_family= font)
		g.add(min_label)
	if sigmax is not None:
		max_label = s.text(str(sigmax),(- 5, font_size*.8),
		                   text_anchor = "end",
		                   font_size = font_size,
		                   font_family=font)
		g.add(max_label)
	
	name_label = s.text(name, (-5, vscale/2 + font_size*.4),
						text_anchor ="end",
						font_size = font_size*1.2,
						font_family=font)
	g.add(rect)
	g.translate(labels, 0)
	g.add(name_label)
