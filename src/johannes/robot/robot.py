import numpy as np
import math3d as m3d
import math
import sys
import urx
from time import sleep
from svgpathtools import svg2paths, Arc, Line, QuadraticBezier, CubicBezier

from johannes.environment.environment import Environment

class Robot():

    def __init__(self, environment):
        self.robot = urx.Robot("192.168.0.2", use_rt=True)
        self.robot.set_tcp((0, 0, 0.15, 0, 0, 0))
        self.robot.set_payload(0.1)
        sleep(0.2)

        #
        self.robot.set_csys(m3d.Transform())

        #Speed and Distance parameters
        self.a = 0.1  # max acceleration m/s^2
        self.v = 0.3  # max velocity m/s
        self.hover = 0.02  # hover over canvas while not painting
        self.feed = 0.003  # brush feed while painting in m/m
        self.offset = 0.008  # initial brush when starting to paint in m

        #Time when changing colour
        self.paint_depth = 0.100  # depth of color pot in m
        self.in_paint_duration = 0.5  # duration for brush in paint pot in s
        self.drop_off_duration = 1  # duration to stay over paint pot in s

        #The environmnet in which the robot operates (i.e. where the pain is lcoated
        self.environment = environment

        # Joint configurations:
        # Make sure that a free path exists between any of those!
        self.j_home = (0, -math.pi / 2, 0, -math.pi / 2, 0, 0)
        self.j_paint_above = (-1.257, -1.332, -2.315, -1.065, 1.571, 0.313)
        self.j_canvas_above = (-0.671, -1.464, -1.975, 0.026, 2.302, -0.169)
        self.j_brush_change = (0.0, -0.725, -2.153, -1.570, 0, 0)

        # Brush calibration point
        self.brush_calib_above = (-0.168, -0.315, 0.080, 0, np.pi, 0)
        self.brush_calib_down = (-0.168, -0.315, 0.027, 0, np.pi, 0)
        
        # Brush calibration parameters
        self.brush = {"red": self.brush_transform(-1, 34 * np.pi / 180, 0.143),
                 "yellow": self.brush_transform(0, 31 * np.pi / 180, 0.148),
                 "blue": self.brush_transform(1, 30 * np.pi / 180, 0.144),
                 "black": self.brush_transform(2, 31 * np.pi / 180, 0.144)}

    def brush_transform(index, angle, length):
        rot = m3d.Orientation.new_rot_z(index * np.pi / 2)
        rot.rotate_x(angle)
        vec = m3d.Transform(rot, (0, 0, 0)) * m3d.Vector(0, 0, length)
        return m3d.Transform(rot, vec)

    def move_home(self):
        print "Move to home"
        self.robot.movej(self.j_home, acc=1.0, vel=self.v)

    def move_to_canvas(self):
        print "Move to canvas"
        j = self.robot.getj()  # Keep orientation of last joint
        self.robot.movej(self.j_canvas_above[:5] + (j[5],), acc=self.a, vel=self.v)

    def move_to_paint(self):
        print "Move to paint"
        self.robot.movej(self.j_paint_above, acc=self.a, vel=self.v)
        # j = self.robot.getj() # Keep orientation of last joint
        # self.robot.movej(j_paint_above[:5] + (j[5],), acc=a, vel=v)

    def move_to_brush_change(self):
        print "Move to brush change"
        self.robot.movej(self.j_brush_change, acc=self.a, vel=self.v)

    def move_to_brush_calibration(self, stroke):
        print "Set base coordiante system"
        self.robot.set_csys(m3d.Transform())

        print "Calibrate brush"
        #   Move with no brush selected to avoid extreme rotations of last joint
        self.robot.set_tcp((0, 0, 0.15, 0, 0, 0))
        print "  Move over calibration point"
        self.robot.movel(self.brush_calib_above, acc=self.a, vel=self.v)
        #   Select brush
        self.robot.set_tcp(self.brush[stroke])
        self.robot.movel(self.brush_calib_above, acc=self.a, vel=self.v)
        #   Move into color
        print "  Move to calibration point"
        self.robot.movel(self.brush_calib_down, acc=self.a / 2, vel=self.v / 4)

    def calibrate_brush(self, stroke):
        self.move_to_brush_calibration(stroke)
        raw_input("Measure brush length and press enter to continue...")
        self.robot.movel(self.brush_calib_above, acc=self.a, vel=self.v)

    def move_to_canvas_origin(self, stroke):
        print "Set canvas coordinate system"
        self.robot.set_csys(self.canvas_coordinates)
        self.robot.set_tcp(self.brush[stroke])
        self.robot.movel((0, 0, -self.hover, 0, 0, 0), acc=self.a, vel=self.v)

    def move_to_canvas_xaxis(self, stroke):
        print "Set canvas coordinate system"
        self.robot.set_csys(self.canvas_coordinates)
        self.robot.set_tcp(self.brush[stroke])
        self.robot.movel((0.75, 0, -self.hover, 0, 0, 0), acc=self.a, vel=self.v)

    def move_to_canvas_yaxis(self, stroke):
        print "Set canvas coordinate system"
        self.robot.set_csys(self.canvas_coordinates)
        self.robot.set_tcp(self.brush[stroke])
        self.robot.movel((0, 0.55, -self.hover, 0, 0, 0), acc=self.a, vel=self.v)

    def get_paint(self, stroke):
        print "Set base coordiante system"
        self.robot.set_csys(m3d.Transform())

        # TODO: check current position
        print "  Distance to pots:", self.robot._get_joints_dist(self.j_paint_above)

        print "Get new paint"
        #   Move with no brush selected to avoid extreme rotations of last joint
        self.robot.set_tcp((0, 0, 0.15, 0, 0, 0))
        print "  Move over color pot"
        self.robot.movel(self.environment.paint[stroke], acc=self.a, vel=self.a)
        # TODO:  Measure color depth

        #   Select brush
        self.robot.set_tcp(self.brush[stroke])
        self.robot.movel(self.environment.paint[stroke], acc=self.a, vel=self.v)
        #   Move into color
        print "  Move into color pot"
        self.robot.down(z=self.paint_depth, acc=self.a / 2, vel=self.v / 3)
        sleep(self.in_paint_duration)

        print "  Move over color pot"
        self.robot.movel(self.environment.paint[stroke], acc=self.a, vel=self.v)
        print "  Wait for color to drop off"
        sleep(self.drop_off_duration)

        print "  Remove paint from tip of brush"
        radius = 0.018
        circle = [
            m3d.Transform(m3d.Orientation.new_rot_z(i * np.pi / 6), (0, 0, 0)) * m3d.Vector(-radius, -radius, 0) for
            i in range(8)]
        circle = [m3d.Transform((0, np.pi, 0), self.environment.mesh[stroke] + c) for c in circle]
        circle.append(m3d.Transform(self.environment.paint[stroke]))
        self.robot.movels(circle, acc=self.a, vel=self.v / 4)

    def paint_path(self, path):
        print "Set canvas coordinate system"
        self.robot.set_csys(self.environment.canvas_coordinates)

        # TODO: check current position
        print "  Distance to canvas:", self.robot._get_joints_dist(self.j_canvas_above)

        print "Paint path"
        for sub in path.continuous_subpaths():
            print "  Paint continuous sub path with length %smm" % (round(sub.length()))
            self.robot.movel((sub.start.real / 1e3, sub.start.imag / 1e3, -self.hover, 0, 0, 0), acc=self.a, vel=self.v)
            poses = []
            acc_dist = 0
            for seg in sub:
                if isinstance(seg, Line):
                    #print "    ", seg, "length:", seg.length()
                    poses.append((seg.start.real / 1e3, seg.start.imag / 1e3, offset + feed * acc_dist / 1e3, 0, 0, 0))
                elif isinstance(seg, Arc) or isinstance(seg, QuadraticBezier) or isinstance(seg, CubicBezier):
                    # one point every curve_interp_step, but at least two points
                    step = min(curve_interp_step * 1e3 / seg.length(), 0.5)
                    points = [seg.point(t) for t in np.arange(0, 1, step)]
                    # TODO acc_dist should be incremented from point to point:
                    poses.extend([(p.real / 1e3, p.imag / 1e3, offset + feed * acc_dist / 1e3, 0, 0, 0) for p in points])
                acc_dist += seg.length()
            poses.append((sub.end.real / 1e3, sub.end.imag / 1e3, offset, 0, 0, 0))
            poses.append((sub.end.real / 1e3, sub.end.imag / 1e3, -hover, 0, 0, 0))
            r.movels(poses, acc=a, vel=v/4, threshold=0.001)
        # If we are on left side of canvas move to save position first
        r.movel((0.6, 0.3, -hover, 0, 0, 0), acc=a, vel=v)

    def paint_svg(paths, attributes):
        i = 0
        for (path, attr) in zip(paths, attributes):
            stroke = attr['stroke']
            print "Path", i, "with color", stroke, "of length", round(path.length())

            move_to_paint()
            try:
                get_paint(stroke)
                move_to_canvas()
                paint_path(path)
            except Exception as e:
                print "ERROR:", e
                raw_input("Press enter to continue... ")

            i += 1
