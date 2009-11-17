#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009 Timothée Lecomte

# This file is part of Friture.
#
# Friture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# Friture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Friture.  If not, see <http://www.gnu.org/licenses/>.

import PyQt4.Qwt5 as Qwt
from PyQt4 import QtCore, QtGui
from audiodata import *

class FreqScaleDraw(Qwt.QwtScaleDraw):
	def __init__(self, *args):
		Qwt.QwtScaleDraw.__init__(self, *args)

	def label(self, value):
		if value >= 1e3:
			label = "%gk" %(value/1e3)
		else:
			label = "%d" %(value)
		return Qwt.QwtText(label)

class picker(Qwt.QwtPlotPicker):
	def __init__(self, *args):
		Qwt.QwtPlotPicker.__init__(self, *args)
		
	def trackerText(self, pos):
		pos2 = self.invTransform(pos)
		return Qwt.QwtText("%d s, %d Hz" %(pos2.x(), pos2.y()))

class PlotImage(Qwt.QwtPlotItem):
	def __init__(self):
		Qwt.QwtPlotItem.__init__(self)
		self.canvasscaledspectrogram = CanvasScaledSpectrogram()

	def addData(self, freq, xyzs, logfreqscale):
		self.canvasscaledspectrogram.setlogfreqscale(logfreqscale)
		self.canvasscaledspectrogram.addData(freq, xyzs)

	def draw(self, painter, xMap, yMap, rect):
		self.canvasscaledspectrogram.setcanvas_height(rect.height())
		self.canvasscaledspectrogram.setcanvas_width(rect.width())

		pixmap = self.canvasscaledspectrogram.getpixmap()
		offset = self.canvasscaledspectrogram.getpixmapoffset()
		painter.drawPixmap(rect.left(), rect.top(), pixmap,  offset,  0,  0,  0)
		
		#print painter
		#print xMap.p1(), xMap.p2(), xMap.s1(), xMap.s2()
		#print yMap.p1(), yMap.p2(), yMap.s1(), yMap.s2()
		#print rect

	def settimerange(self, timerange_seconds):
		self.canvasscaledspectrogram.setT(timerange_seconds)

	def setfreqrange(self, minfreq, maxfreq):
		self.canvasscaledspectrogram.setfreqrange(minfreq, maxfreq)

	def erase(self):
		self.canvasscaledspectrogram.erase()

class ImagePlot(Qwt.QwtPlot):

	def __init__(self, *args):
		Qwt.QwtPlot.__init__(self, *args)

		# we do not need caching
		self.canvas().setPaintAttribute(Qwt.QwtPlotCanvas.PaintCached, False)
		self.canvas().setPaintAttribute(Qwt.QwtPlotCanvas.PaintPacked, False)

		# set plot layout
		self.plotLayout().setMargin(0)
		self.plotLayout().setCanvasMargin(0)
		self.plotLayout().setAlignCanvasToScales(True)
		# use custom labelling for frequencies
		self.setAxisScaleDraw(Qwt.QwtPlot.yLeft, FreqScaleDraw())
		self.setAxisScaleDraw(Qwt.QwtPlot.yRight, FreqScaleDraw())
		# set axis titles
		self.setAxisTitle(Qwt.QwtPlot.xBottom, 'Time (s)')
		self.setAxisTitle(Qwt.QwtPlot.yLeft, 'Frequency (Hz)')
		self.enableAxis(Qwt.QwtPlot.yRight)
		# attach a plot image
		self.plotImage = PlotImage()
		self.plotImage.attach(self)
		self.setlinfreqscale()
		self.setfreqrange(20., 20000.)

		self.setAxisScale(Qwt.QwtPlot.xBottom, 0., 10.)
		
		self.paint_time = 0.
		
		# picker used to display coordinates when clicking on the canvas
		self.picker = picker(Qwt.QwtPlot.xBottom,
                               Qwt.QwtPlot.yLeft,
                               Qwt.QwtPicker.PointSelection,
                               Qwt.QwtPlotPicker.CrossRubberBand,
                               Qwt.QwtPicker.ActiveOnly,
                               self.canvas())
		
		self.replot()
		
		self.cached_canvas = self.canvas()

	def addData(self, freq, xyzs):
		self.plotImage.addData(freq, xyzs, self.logfreqscale)
		# self.replot() would call updateAxes() which is dead slow (probably because it
		# computes label sizes); instead, let's ask Qt to repaint the canvas only next time
		# This works because we disable the cache
		# TODO what happens when the cache is enabled ?
		# Could that solve the perceived "unsmoothness" ?
		
		self.cached_canvas.update()
		
		#print self.canvas().testPaintAttribute(Qwt.QwtPlotCanvas.PaintCached)
		#print self.canvas().paintCache()

	def setlinfreqscale(self):
		self.plotImage.erase()
		self.logfreqscale = 0
		self.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLinearScaleEngine())
		self.setAxisScaleEngine(Qwt.QwtPlot.yRight, Qwt.QwtLinearScaleEngine())
		self.replot()

	def setlog10freqscale(self):
		self.plotImage.erase()
		self.logfreqscale = 1
		self.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLog10ScaleEngine())
		self.setAxisScaleEngine(Qwt.QwtPlot.yRight, Qwt.QwtLog10ScaleEngine())
		self.replot()
		
	def setlog2freqscale(self):
		self.plotImage.erase()
		self.logfreqscale = 2
		print "Warning: Frequency scales are not implemented in the spectrogram"
		self.setAxisScaleEngine(Qwt.QwtPlot.yLeft, Qwt.QwtLog10ScaleEngine())
		self.setAxisScaleEngine(Qwt.QwtPlot.yRight, Qwt.QwtLog10ScaleEngine())
		self.replot()

	def settimerange(self, timerange_seconds):
		self.plotImage.settimerange(timerange_seconds)
		self.setAxisScale(Qwt.QwtPlot.xBottom, 0., timerange_seconds)
		self.replot()

	def setfreqrange(self, minfreq, maxfreq):
		self.plotImage.setfreqrange(minfreq, maxfreq)
		self.setAxisScale(Qwt.QwtPlot.yLeft, minfreq, maxfreq)
		self.setAxisScale(Qwt.QwtPlot.yRight, minfreq, maxfreq)
		self.replot()

	def drawCanvas(self, painter):
		t = QtCore.QTime()
		t.start()
		Qwt.QwtPlot.drawCanvas(self, painter)
		self.paint_time = (95.*self.paint_time + 5.*t.elapsed())/100.
