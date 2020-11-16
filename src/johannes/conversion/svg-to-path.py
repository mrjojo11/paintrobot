
class svg_to_path_conversion:

    def __init__(self):
        # steps in m for arc and bezier interpolation
        self.curve_interp_step = 0.01

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