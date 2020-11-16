import math3d as m3d
import numpy as np

class Environment:

    def __init__(self):
        # Canvas coordinates (base csys):
        # p0 ---------> px
        # |
        # |
        # py
        self.p0 = m3d.Transform((0.542, 0.241, 0.677, -1.497, 1.332, -1.134))
        self.px = m3d.Transform((0.543, -0.509, 0.668, -1.497, 1.332, -1.134))
        self.fpy = m3d.Transform((0.437, 0.245, 0.137, -1.497, 1.333, -1.134))

        self.dx = self.px.pos - self.p0.pos
        self.dy = self.px.pos - self.p0.pos
        self.canvas_coordinates = m3d.Transform.new_from_xyp(self.dx, self.dy, self.p0.pos)

        # Paint pot coordinates:
        self.paint = {"red": (-0.12, -0.280, 0.08, 0, np.pi, 0),
                 "yellow": (-0.04, -0.280, 0.08, 0, np.pi, 0),
                 "blue": (0.04, -0.280, 0.08, 0, np.pi, 0),
                 "black": (0.12, -0.285, 0.08, 0, np.pi, 0)}

        # Paint drop removal coordinates:
        self.mesh = {"red": m3d.Vector(-0.12, -0.40, 0.057),
                "yellow": m3d.Vector(-0.04, -0.40, 0.055),
                "blue": m3d.Vector(0.04, -0.40, 0.054),
                "black": m3d.Vector(0.12, -0.40, 0.053)}