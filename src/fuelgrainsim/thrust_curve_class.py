"""
Contains class definitions for SVG, Shape, and Plot
"""

import matplotlib as mpl
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from svgpathtools import svg2paths, Line, Path, Arc
from svgpathtools import path

import math

import shapely as sg
import shapely.affinity as sa
from shapely import get_geometry, symmetric_difference, remove_repeated_points, get_coordinates, \
    get_exterior_ring, centroid, get_x, get_y


class SVG:
    """
    Converts an SVG file into a series of paths objects containing arc and line elements.

    Parameters
        file_name: name of svg file to convert to path objects (str)

    Attributes
        .corrected: a path object including the inner, outer, and scale bar
        .scaled_inner: a path object of the scaled inner ring
        .scaled_outer: a path object of the scaled outer ring
        .scalar: quantity path is scaled by to get accurate dimensions
    """

    def __init__(self,file_name):
        self.paths, self.attributes = svg2paths(file_name)
        self.corrected = path.concatpaths(self.paths[4:])
        _len_list = []
        for each in self.corrected:
           _len_list.append(each.length())
        max1 = max(_len_list)
        self._outer_path = Path(self.corrected.pop(_len_list.index(max1)))
        _len_list.remove(max1)
        max1 = max(_len_list)
        self._outer_path.append(Path(self.corrected.pop(_len_list.index(max1))))
        _len_list.remove(max1)
        self._scalar_path = self.corrected.pop(0)
        self._inner_path = self.corrected
        self._scale()

    def _scale(self):
        """
        returns path object scaled by scale factor .scalar
        """
        self.scalar = 10 / self._scalar_path.length()
        self.scaled_path = path.scale(self._scalar_path, self.scalar, self.scalar)
        self.scaled_outer = path.scale(self._outer_path, self.scalar, self.scalar)
        self.scaled_inner = path.scale(self._inner_path, self.scalar, self.scalar)

    def get_inner(self):
        return self.scaled_inner

    def get_outer(self):
        return self.scaled_outer


class Shape:
    """
    Transforms path objects into shapely polygons to perform operations on.

    Parameters
        svg_path: an iterable path object
        scale: tuple of scale factor (float) and unit (str)
        radius: manually created outer boundary tuple with radius in positive x and y directions (float)
        center: coordinate tuple to center polygon on (float)

    Attributes
        .path: imported path
        .original: polygon generated from .path
        .current: current polygon after offsets have been applied
        .boundary: boundary polygon
        .intersect: polygon created by intersecting the .current with the .boundary
        .units: units of the polygon
        .scale: scale factor that was applied on the polygon when it was created
    """

    def __init__(self, svg_path, scale=(1.0, "mm"), radius=(42.8625,42.8625), center=(0,0)):
        self.path = svg_path
        _points = self._linear_approximation(svg_path)
        _sorted = self._sort(_points)
        self.original = remove_repeated_points(sg.Polygon(_sorted))
        self.current=self._center(center)
        self.unit = scale[1]
        self.scale = scale[0]
        _rad = complex(radius[0], radius[1])
        _start = complex(radius[0] + center[0], center[1])
        _end = complex(center[0] - radius[0], center[1])
        _upper = Arc(_start, _rad, 0, False, False, _end)
        _lower = _upper.rotated(180)
        _boundary = Path(_upper, _lower)
        _b_points = self._linear_approximation(_boundary, 1)
        _b_sorted = self._sort(_b_points)
        self.boundary = remove_repeated_points(sg.Polygon(_b_sorted))
        self.intersect = self.current.intersection(self.boundary)

    def _center(self,center):
        """
        centers the polygon on the chosen coordinates
        """
        _o_cen=centroid(self.original)
        _x_o=center[0]-get_x(_o_cen)
        _y_o=center[1]-get_y(_o_cen)
        return sa.translate(self.original,_x_o,_y_o)

    def _linear_approximation(self, path2, steps_unit=5):
        """
        Takes path and approximates arc segments into line segments for faster computation

        Parameters
            path2: path object to perform approximation on
            steps_unit: line segments to be generated per unit length of arc segment

        returns new path of only line segments
        """
        _nls = []
        for seg in path2:
            if isinstance(seg, Line):
                _nls.append(seg)
            else:
                _steps = math.ceil(seg.length() * steps_unit)
                _ct = 1
                for k in range(_steps):
                    _t = k / _steps
                    _nl = Line(seg.point(_t), seg.point(_t))
                    _nls.append(_nl)
        return Path(*_nls)

    def _sort(self, line_path):
        """
        Sorts the line segments from end to end
        Converts start and end points of segments into list of coordinate tuples

        Parameters
            line_path: path object to sort and convert into a list of coordinates

        returns list of coordinate tuples
        """
        _point_list = []
        _start_line = line_path[0]
        _p1, _p2 = self._get_coord(Path(_start_line))
        _start_point = _p1
        line_path.remove(_start_line)
        _future_start = _start_point
        _future_append = _p2
        _point_list.append(_future_append)
        _current_path = _start_line
        for z in range(len(line_path) - 3):
            _min_d = 1000000
            _point_list.append(_start_point)
            for _x in line_path:
                _p_p_1, _p_p_2 = self._get_coord(Path(_x))
                _d1 = self._distance_path(_start_point, _p_p_1)
                _d2 = self._distance_path(_start_point, _p_p_2)
                if _d1 <= _min_d or _d2 <= _min_d:
                    _current_path = _x
                    if _d1 < _d2:
                        _future_start = _p_p_2
                        _future_append = _p_p_1
                        _min_d = _d1
                    else:
                        _future_start = _p_p_1
                        _future_append = _p_p_2
                        _min_d = _d2
            _start_point = _future_start
            _point_list.append(_future_append)
            line_path.remove(_current_path)
        return _point_list

    def _get_coord(self, path_segment):
        """
        Extracts coordinates from the starts and end points of a line segment

        Parameters
            path_segments: line segment to extract coordinates from

        returns start and end point coordinate tuples
        """
        _d = path_segment.d()
        _d2 = _d.split(" ")
        _start = _d2[1]
        _end = _d2[3]
        _start_x = float(_start.split(",")[0])
        _start_y = float(_start.split(",")[1])
        _end_x = float(_end.split(",")[0])
        _end_y = float(_end.split(",")[1])
        _start_coord = (_start_x, _start_y)
        _end_coord = (_end_x, _end_y)
        _path_points_x, _path_points_y = _start_coord, _end_coord
        return _path_points_x, _path_points_y

    def _distance_path(self, coord_1, coord_2):
        """
        Calculates distance between points for sorting function

        Parameters
            coord_1: start coordinate tuple
            coord_2: end coordinate tuple

        returns distance between coordinates
        """
        _distance = (((coord_1[0]) - (coord_2[0])) ** 2 + ((coord_1[1]) - (coord_2[1])) ** 2) ** .5
        return _distance

    def length(self):
        """
        returns perimeter of intersect polygon
        """
        return self.intersect.length

    def area(self):
        """
        returns area of intersect polygon
        """
        return self.intersect.area

    def hydraulic_diameter(self):
        """
        Calculates the hydraulic diameter from the intersect polygon

        returns the hydraulic diameter
        """
        _area=self.intersect.area
        _length=self.wetted_length()
        _h_d = 4 * _area / _length
        return _h_d

    def wetted_length(self):
        """
        returns the perimeter of exposed fuel grain
        """
        return self.intersect.length-self._sliver()

    def _sliver(self):
        """
        returns length of exposed boundary polygon
        """
        if sg.contains(self.boundary,self.intersect):
            return 0
        else:
            _p0=symmetric_difference(self.intersect,self.boundary,.0001)
            _p1=get_geometry(_p0, 0).length*4
            _p=(self.boundary.length+_p1-self.intersect.length)/2
            _p2=self.boundary.length-_p
            return _p2

    def buffer(self, repetitions=1, offset=1):
        """
        Applies a buffer to the intersect polygon

        Parameters
            repetitions: number of time to perform buffer (int)
            offset: buffer distance in unit, - for opposite direction (float)

        returns a list of polygons generated from the offset
        """
        _poly_list = []
        for e in range(repetitions):
            _b_poly = self.current.buffer(offset, join_style="round", mitre_limit=.5, quad_segs=20, cap_style="flat")
            self.current = _b_poly
            self.intersect = self.current.intersection(self.boundary)
            _poly_list.append(self.intersect)
        return _poly_list

    def get_coords(self,polygon):
        """
        Parameters
             polygon: a polygon object

        return a list of polygon coordinates
        """
        _exterior=get_exterior_ring(polygon)
        return get_coordinates(_exterior)

    def reset(self):
        """
        resets the current polygon to the original polygon
        """
        self.current = self.original

    def get_current(self):
        return self.current

    def get_intersect(self):
        return self.intersect

    def get_original(self):
        return self.original

    def get_path(self):
        return self.path

    def get_unit(self):
        return self.unit

    def get_scale(self):
        return self.scale

    def get_boundary(self):
        return self.boundary

class Plot:
    """
    Generates plot object that can plot polygon shapes and dataframe data

    Parameters
        polygons: list of polygons to (can be initialized with an empty list)
        df: pandas data frame

    Attributes
    .polygons: list of polygons
    .df: data frame
    """

    def __init__(self, polygons, data_frame):
        self.polygons = polygons
        self.df = data_frame

    def plot_polygons(self,color,color_2,ax=None,fig=None):
        """
        Plots the list of polygons contained in .polygons

        Parameters
            ax: matplotlib axes object you wish to plot to. By default, a new axes object is created.
        """
        test = mpl.colormaps[color+"_r"].resampled(len(self.polygons))
        test_2 = mpl.colormaps[color_2 + "_r"].resampled(len(self.polygons))
        colors = test.colors  # Get all colors in the colormap as an RGBA array
        colors_2 = test_2.colors

        if ax is None:
            fig, ax = plt.subplots(layout='constrained')

        cmap = mpl.cm.inferno_r
        plt.colorbar(mpl.cm.ScalarMappable(norm=mpl.colors.Normalize(0, 5.6), cmap=cmap), ax=ax, orientation='vertical', label='Time (s)')

        counter = 0
        for each in self.polygons:
            tup = (colors[counter][0], colors[counter][1], colors[counter][2])
            tup_2 = (colors_2[counter][0], colors_2[counter][1], colors_2[counter][2])
            if counter%2 == 1:
                ax.plot(*each.exterior.xy,color = tup)
            else:
                ax.plot(*each.exterior.xy, color=tup_2)

            counter += 1
        ax.set_xlabel("(mm)")
        ax.set_ylabel("(mm)")

    def plot_data(self,column,title="",x_label="",y_label="",ax=None,fig=None):
        """
        Plots data contained in .df as line plot

        Parameters
            column: string column name in data frame to be plotted
            title: string label for title
            x_label: string label for x-axis
            y_label: string label for y-axis
            ax: matplotlib axes object you wish to plot to. By default, a new axes object is created.
        """
        if ax is None:
            fig, ax = plt.subplots()
        ax.plot(self.df.index, self.df[column])
        ax.set_title(title)
        ax.set_ylim(0,self.df[column].max()*1.1)
        ax.set_xlim(0, 5.6)

        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.xaxis.set_minor_locator(MultipleLocator(0.25))
        ax.yaxis.set_minor_locator(AutoMinorLocator())

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)


    def animate(self,name,location,save=False):

        fig_5, axes_2 = plt.subplots()
        axes_2.xaxis.set_major_locator(MultipleLocator(20))
        axes_2.yaxis.set_major_locator(MultipleLocator(20))
        plt.gca().set_aspect('equal')
        plt.ylim(-45, 45)
        plt.xlim(-45, 45)

        line_1, = axes_2.plot(*self.polygons[0].exterior.xy)
        line_2, = axes_2.plot(*self.polygons[-1].exterior.xy, color="black")
        line_3, = axes_2.plot(*self.polygons[-1].exterior.xy, color="black")
        leg = plt.legend(labels=["Thrust: 0", "Regression: 0", "Time: 0"], loc=1, handletextpad=0, handlelength=0,
                         title="Data")
        axes_2.set_xlabel("(mm)")
        axes_2.set_ylabel("(mm)")

        def update(frame):
            txt_1 = 'Thrust: ' + str(round(self.df["Thrust"].tolist()[frame], 4))
            txt_2 = 'Regression: ' + str(round(self.df["Regression"].tolist()[frame], 4))
            txt_3 = 'Time: ' + str(round(self.df.index.tolist()[frame], 1))
            line_1.set_data(*self.polygons[frame].exterior.xy)
            line_1.set_color("red")
            leg.get_texts()[0].set_text(txt_1)
            leg.get_texts()[1].set_text(txt_2)
            leg.get_texts()[2].set_text(txt_3)
            return line_1

        anim = animation.FuncAnimation(fig=fig_5, func=update, frames=range(57), repeat=False)

        if save is True:
            file_n = location  / f"{name}.gif"
            anim.save(filename=file_n, writer="pillow")

        plt.close()