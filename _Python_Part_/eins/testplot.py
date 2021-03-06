#!/usr/bin/env python
# coding=utf-8

import road as br
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.path import Path
import matplotlib.patches as patches

class BasicLayer(object):
    '最底层图层设置'
    def __init__(self, initSize_ = 10, initColor_ = 'black',xlim_=[0, 100], ylim_=[0, 62.5]):
        #WIDTH --> Y : 6.25 --> 1  WIDTH --> X : 10 --> 1      X轴Y轴的增量映射到绘图坐标轴上的比率是不一样的！！！！！
        self.fig = plt.figure(figsize=(initSize_, initSize_), facecolor = initColor_)
        self.ax = self.fig.add_axes([0, 0, 1, 1], frameon = False)
        self.ax.set_xlim(xlim_)
        self.ax.set_ylim(ylim_)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.time_text = self.ax.text(0, 0.85, '', transform=self.ax.transAxes, color = 'orange')

    def getLayer(self):
        return self.fig
    def getScatLayer(self):
        return self.ax

class RoadPlot(object):
    '绘制直线跑道'
    def __init__(self, rX, rY, roadbox, plotLayer):
        self.rX = rX                                                   #道路起点和终点的X坐标
        #由于绘图时xlim,ylim不一样,这里要重新映射rY
        self.rY = 62.5*rY/100.0                                        #道路起点和终点的Y坐标

        self.road = roadbox[0]                                         #指向要绘出的道路
        self.width = 1 + self.road.get_road_lanes()*2                  #道路宽度的绘图倍数
        self.roadbox = roadbox
        self.plotLayer = plotLayer                                     #指向要绘画的图层
        self.scat = self.plotLayer.scatter([0], [0], s = 1)

        #计算坐标偏移量
        self.mirrorLength = np.sqrt(np.power(self.rX[0] - self.rX[1],2) + np.power(self.rY[0] - self.rY[1], 2) )
        self.costheta = (self.rX[1] - self.rX[0])/self.mirrorLength
        self.sintheta = np.sqrt(1 - np.power(self.costheta, 2))
        self.yOffset = self.width*self.costheta/2
        self.xOffset = self.width*self.sintheta/2

        #变换坐标轴(新原点,角度为theta)
        self.newXSet = self.rX[0] - self.xOffset
        self.newYSet = self.rY[0] + self.yOffset

        self.lanes = self.road.get_road_lanes()
        self.time_template = 'exec rule & road id: '+str(self.road.execRule)
        self.time_template += '\nexec_time = %.fs '
        if self.road.autoAdderSwitch is True:
            self.time_template += '\nboundary: Time'
        elif self.road.autoAdderByTime is True:
            self.time_template += '\nboundary: Cycle'
        else:
            self.time_template += '\nboundary: None'

        self.time_template += '\nmean speed: %.2f m/s'
        self.time_template += '\nnum of cars: %.f'
        self.time_template += '\nnum of leave cars: %.f '

    def plot(self, color_ = True, reflush_ = True):
        if reflush_:
            self.scat.set_offsets(self.getPlotInfo())
            if color_:                                                      #如果color_为True,则会根据车辆的当前速度与最大速度为其绘制颜色
                self.scat.set_edgecolors(self.getColorMap())
            for road in self.roadbox:
                road.reflush_status()
        else:
            pass

    def setPlot(self):
        #绘制跑道
        verts = [
            (self.rX[0] - self.xOffset, self.rY[0] + self.yOffset),
            (self.rX[1] - self.xOffset, self.rY[1] + self.yOffset),
            (self.rX[1] + self.xOffset, self.rY[1] - self.yOffset),
            (self.rX[0] + self.xOffset, self.rY[0] - self.yOffset),
            (self.rX[0] - self.xOffset, self.rY[0] + self.yOffset)
        ]
        codes = [
            Path.MOVETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.CLOSEPOLY,
        ]

        path = Path(verts, codes)
        patch = patches.PathPatch(path, facecolor='white', alpha = 0.3)
        self.plotLayer.add_patch(patch)

        #绘制边界
        self.plotLayer.plot([self.rX[0] - self.xOffset, self.rX[1] - self.xOffset], [self.rY[0] + self.yOffset, self.rY[1] + self.yOffset], 'w')
        self.plotLayer.plot([self.rX[0] + self.xOffset, self.rX[1] + self.xOffset], [self.rY[0] - self.yOffset, self.rY[1] - self.yOffset], 'w')

        #绘制车道
        for i in xrange(1,self.lanes+1):
             self.plotLayer.plot()

    def getColorMap(self):
        collector = []
        carbox = self.road.get_cars()
        vmax = self.road.get_road_vmax()
        for lane in carbox:
            for car in lane:
                if car.name != 'default':
                    offset = 0.5
                else:
                    offset = 0.0
                if car.speed <= 0.2*vmax:
                    collector.append([1. - offset, 0., 0., 1. - offset])
                elif car.speed <= 0.6*vmax:
                    collector.append([1. - offset, 1., 0., 1. - offset])
                else:
                    collector.append([0., 1. - offset, 0., 1. - offset])
        return np.array(collector)

    def setRoadWidth(self, num):
        self.width = num

    #TODO:多车道映射未作
    def getPlotInfo(self):
        offsetX = self.width*0.9*self.costheta/(self.lanes + 1)
        offsetY = self.width*0.9*self.sintheta/(self.lanes + 1)
        output = np.array([])

        #---temp test
        index = 0
        negindex = -1
        flag = True
        #---
        for index, locate in enumerate(self.road.get_cars_locate()):
            if flag is True:
                value = index
            else:
                value = negindex

            mapping = locate/self.road.get_road_length()                 #映射比率值
            plotX = mapping*((self.rX[1] - self.rX[0])) + self.rX[0]
            #---
            plotY = mapping*((self.rY[1] - self.rY[0])) + self.rY[0] + self.yOffset - index*2 - 1.5
            #---
            output = np.append(output, np.array((plotX,plotY)).T)
            if flag is True:
                index += 1
                flag = False
            else:
                negindex -= 1
                flag = True
        return output
#-----------------------------------------------------------------------------
'绘制动画'
execroad = []
layer = BasicLayer()
def addRoad(road):
    time_template = 'exec_time = %.0fs '
    temp = RoadPlot(np.array([0, 100]), np.array([50, 50]), road, layer.getScatLayer())
    temp.setPlot()
    execroad.append(temp)
    road = road[0]


def update(frame_number):
    for road in execroad:
        lanes, whole = road.road.get_mean_speed()
        num = sum(road.road.get_cars_num())
        num2 = sum(road.road.get_leave_cars())
        if whole is None:
            whole = 0
        layer.time_text.set_text(road.time_template % (frame_number, whole, num, num2))
        road.plot()

def plot():
    'Waring: Cannot stop this,once started'
    anim = FuncAnimation(layer.getLayer(), update, interval = 10)
    plt.show()
#----------------------------------------------------------------------------
