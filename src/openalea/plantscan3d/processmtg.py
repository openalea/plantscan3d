from math import atan2, degrees

import numpy as np
from numpy.linalg import norm
from openalea.plantgl.all import (
    centroid_of_group,
    direction,
    dot,
    estimate_radii_from_points,
    pointset_orientation,
)

from .mtgmanip import gaussian_filter, mtg2pgltree, pipemodel
from .processpoints import (
    filter_points,
    load_points,
    skeleton,
    subsample,
)


def characterize_mtg(g):
    """
    Function to characterize a MTG object.

    Parameters
    ~~~~~~~~~~
    g : openalea.mtg.MTG
        MTG object to be characterized

    Returns
    ~~~~~~~
    Dictionary of results
        - trunk_length : length of the trunk
        - trunk_branching_zone_start : start of the trunk branching zone
        - trunk_branching_zone_end : end of the trunk branching zone
        - trunk_branching_zone_length : length of the trunk branching zone
        - trunk_base_radius : base radius of the trunk
        - trunk_top_radius : top radius of the trunk
        - nb_short_axis : number of short lateral axis
        - nb_long_axis : number of long lateral axis
    """
    shortaxis, longaxis = trunk_lateral_axes(g)
    trunk_dir = trunk_direction(g, 0.5)
    trunkbaseradius, trunktopradius = trunk_radii(g, 0.1, 0.1)

    res = dict(
        trunk_length=trunk_length(g),
        trunk_branching_zone_start=trunk_branching_zone_start(g),
        trunk_branching_zone_end=trunk_branching_zone_end(g),
        trunk_branching_zone_length=trunk_branching_zone_length(g),
        trunk_base_radius=trunkbaseradius,
        trunk_top_radius=trunktopradius,
        nb_short_axis=len(shortaxis),
        nb_long_axis=len(longaxis),
    )

    bot_angle_param = 0, 0.15
    top_angle_param = 0.85, 1

    res.update(
        [
            ("axis1_length_" + str(i), axis_length(g, longax))
            for i, longax in enumerate(longaxis)
        ]
    )
    res.update(
        [
            ("axis1_chord_length_" + str(i), axis_chord_length(g, longax))
            for i, longax in enumerate(longaxis)
        ]
    )
    res.update(
        [
            (
                "axis1_angle_bot_" + str(i),
                axis_subpart_angle(
                    g, longax, bot_angle_param[0], bot_angle_param[1], trunk_dir
                ),
            )
            for i, longax in enumerate(longaxis)
        ]
    )
    res.update(
        [
            (
                "axis1_angle_top_" + str(i),
                axis_subpart_angle(
                    g, longax, top_angle_param[0], top_angle_param[1], trunk_dir
                ),
            )
            for i, longax in enumerate(longaxis)
        ]
    )
    res.update(
        [
            (
                "axis1_extremities_angle_" + str(i),
                axis_extremities_angle(g, longax, trunk_dir),
            )
            for i, longax in enumerate(longaxis)
        ]
    )
    for i, longax in enumerate(longaxis):
        rfirst, rmedian, rlast = retrieve_axis_radii(g, longax)
        res["axis1_rfirst_" + str(i)] = rfirst
        res["axis1_rlast_" + str(i)] = rlast
        res["axis1_rmedian_" + str(i)] = rmedian
    return res


def generate_mtg(
    filename,
    do_filter_points=True,
    do_gaussian_filter=True,
    do_determine_radius=True,
    do_pipemodel=True,
    **kwargs,
):
    """
    Summary function that generates a MTG from a point cloud.

    Parameters
    ~~~~~~~~~~
    filename : str
        Filename of the point cloud.
    do_filter_points: bool
        If True, points are filtered to keep only points with a density above a threshold.
        Default to True.
    do_gaussian_filter: bool
        If True, a gaussian filter is applied to the position property of the mtg.
        Default to True.
    do_determine_radius: bool
        If True, the radius of each node is estimated.
        Default to True.
    do_pipemodel: bool
        If True, the pipe model is applied to correct the radius of each node.
        Default to True.
    kwargs:
        additional arguments to pass to the inner functions

    Returns
    ~~~~~~~
    openalea.mtg.MTG
        mtg object representing the point cloud with a skeleton and radius estimation for each node.

    Notes
    ~~~~~
    `generate_mtg` is a wrapper around the following functions (in that order):
        - :func:`load_points`
        - :func:`subsample`
        - :func:`filter_points`
        - :func:`skeleton`
        - :func:`determine_radius`
        - :func:`pipemodel`
    Arguments passed to the inner functions can be passed as keyword arguments to `generate_mtg`.

    Example
    ~~~~~~~
    >>> mtg = generate_mtg("path/to/pointcloud.pts")

    >>> mtg = generate_mtg("path/to/pointcloud.pts",
                gaussian_filter=False,
                subsample={"ptsnb": 1000},
                filter_points={"densityfilterratio": 0.05, "densityradius": 0.1, "k": 20},
                skeleton={"skel_func": adaptivespacecolonization_method, "asc_max_growth_lengt": 0.01},
                determine_radius={"radiusproperty": "Radii", "maxmethod": False}
                )

    """
    points = load_points(filename)
    points = subsample(points, **kwargs.get("subsample", {}))
    if do_filter_points:
        points = filter_points(points, **kwargs.get("filter_points", {}))
    mtg = skeleton(points, **kwargs.get("skeleton", {}))
    if do_gaussian_filter:
        gaussian_filter(mtg, "position")
    if do_determine_radius:
        determine_radius(mtg, points, **kwargs.get("determine_radius", {}))
    if do_pipemodel:
        pipemodel_radii = pipemodel(mtg, **kwargs.get("pipemodel", {}))
        mtg.property("radius").update(pipemodel_radii)
    return mtg


def determine_radius(g, points, maxmethod=True, radiusproperty="radius"):
    """
    Function to determine the radius of each node of a MTG object.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        mtg object. Usually, the skeleton of the point cloud.
    points: PointSet
        PointSet of the point cloud.
    maxmethod: bool
        Wether to use the max (True) or the mean (False) method to estimate the radius.
        Default is True.
    radiusproperty: str
        Name of the property in the mtg to store the radius.
        Default is "radius".
    """
    nodes, parents, vertex2node = mtg2pgltree(g)

    estimatedradii = estimate_radii_from_points(
        points, nodes, parents, maxmethod=maxmethod
    )

    radii = g.property(radiusproperty)
    for vid, nid in vertex2node.items():
        radii[vid] = estimatedradii[nid]


class Line:
    def __init__(self, position, direction, extend):
        self.position = position
        self.direction = direction
        self.extend = extend

    def __repr__(self):
        return (
            "Line("
            + str(self.position)
            + ","
            + str(self.direction)
            + ","
            + str(self.extend)
            + ")"
        )

    @staticmethod
    def estimate(positions):
        idx = range(len(positions))
        pos = centroid_of_group(positions, idx)
        dir = direction(pointset_orientation(positions, idx))
        if dot(pos - positions[0], dir) < 0:
            dir *= -1
        extend = max([abs(dot(p - pos, dir)) for p in positions])
        return Line(pos, dir, extend)


def nb_lateral_children(g, vid):
    return sum(lateral_children(g, vid))


def trunk_branching_zone_start(g):
    """
    Detemine the start of the trunk branching zone.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed.

    Returns
    ~~~~~~~
        The length of the trunk from bottom to the start of the branching zone.
    """
    trunknodes = trunk_nodes(g)
    firstidpos = None
    for i, vid in enumerate(trunknodes):
        if nb_lateral_children(g, vid) > 0:
            firstidpos = i
            break
    if firstidpos is None:
        return None
    trunknodes = trunknodes[: firstidpos + 1]
    return sum([node_length(g, n) for n in trunknodes])


def trunk_branching_zone_end(g):
    """
    Determine the end of the trunk branching zone.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed.

    Returns
    ~~~~~~~
        The length of the trunk from bottom to the end of the branching zone.
    """

    trunknodes = trunk_nodes(g)

    lastidpos = None
    for i, vid in enumerate(reversed(trunknodes)):
        if nb_lateral_children(g, vid) > 0:
            lastidpos = i
            break
    if lastidpos is None:
        return None
    trunknodes = trunknodes[:-lastidpos]
    return sum([node_length(g, n) for n in trunknodes])


def trunk_branching_zone_length(g):
    """
    Determine the length of the trunk's branching zone.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed.

    Returns
    ~~~~~~~
        The length of the trunk's branching zone.
    """
    trunknodes = trunk_nodes(g)
    firstidpos = None
    for i, vid in enumerate(trunknodes):
        if nb_lateral_children(g, vid) > 0:
            firstidpos = i
            break
    if firstidpos is None:
        return None
    trunknodes = trunknodes[firstidpos + 1 :]
    lastidpos = None
    for i, vid in enumerate(reversed(trunknodes)):
        if nb_lateral_children(g, vid) > 0:
            lastidpos = i
            break
    if lastidpos is None:
        return 0
    trunknodes = trunknodes[:-lastidpos]

    return sum([node_length(g, n) for n in trunknodes])


def trunk_length(g):
    """
    Determine the length of the trunk.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed.

    Returns
    ~~~~~~~
        The length of the trunk.
    """
    return axis_length(g, trunk_root(g))


def axis_length(g, n):
    """
    Determine the length of the axis.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed.
    n: int
        Node id.

    Returns
    ~~~~~~~
        The length of the axis.
    """
    return sum(map(lambda vid: node_length(g, vid), g.Axis(n)))


def node_length(g, n):
    """
    Determine the length of the node.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed.
    n: int
        Node id.

    Returns
    ~~~~~~~
        The length between a node and his parent.
    """
    parent = g.parent(n)
    if parent:
        p1 = node_position(g, n)
        p0 = node_position(g, parent)
        return norm(p1 - p0)
    else:
        return 0


def axis_chord_length(g, n):
    """
    Determine the chord length of the axis.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed.
    n: int
        Node id.

    Returns
    ~~~~~~~
        The chord length of an axis.
    """
    from numpy.linalg import norm

    p0, p1 = axis_extremities(g, n)
    return norm(p1 - p0)


def retrieve_axis_radii(g, vid):
    """
    Determine the radius of the axis:
    radius of the first node, radius of the last node and mean value of the radius of the axis.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed.
    n: int
        Node id.

    Returns
    ~~~~~~~
        Tuple of the radius of the first node, mean value of the radius of the axis and radius of the last node.
    """

    radii = g.property("radius")
    axis = g.Axis(vid)
    axis = [vid for vid in axis if vid in radii]
    nbnodes = len(axis)
    if nbnodes == 0:
        return None, None, None
    elif nbnodes == 1:
        r = radii[axis[0]]
        return r, r, r
    elif nbnodes == 2:
        r0 = radii[axis[0]]
        r1 = radii[axis[1]]
        return r0, (r0 + r1) / 2, r1
    elif nbnodes == 3:
        r0 = radii[axis[0]]
        r1 = radii[axis[1]]
        r2 = radii[axis[2]]
        return r0, r2, r1
    else:
        lradii = list(map(lambda v: radii[v], axis))
        lradii.sort()
        meanradius = lradii[int(len(lradii) / 2)]
        return (radii[axis[0]], meanradius, radii[axis[-2]])


def trunk_radii(g, begratio=0.1, endratio=0.1):
    """
    Determine the radius of the trunk at the base and the top.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed, on which to determine the trunk radius.
    begratio: float
        Ratio of the bottom of the trunk used to determine the bottom radius.
        Default to 0.1.
    endratio: float
        Ratio of the top of the trunk used to determine the top radius.
        Default to 0.1.

    Returns
    ~~~~~~~
    Tuple of the bottom and top radius of the trunk.
    """
    begtrunk = axis_subpart(g, trunk_root(g), 0, begratio)
    endtrunk = axis_subpart(g, trunk_root(g), 1 - endratio, 1)
    radii = g.property("radius")
    return max([radii[n] for n in begtrunk]), max([radii[n] for n in endtrunk])


def node_position(g, n):
    """
    Retuns the position of a node in a MTG.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed, on which to determine the trunk radius.
    n: int
        Index of the node.

    Returns
    ~~~~~~~
    Tupole of the position of the node (x,y,z).
    """
    if "position" in g.property_names():
        return g.property("position")[n]
    return np.array([g.property("XX")[n], g.property("YY")[n], g.property("ZZ")[n]])


def axis_extremities(g, n):
    """
    Determine the extremities of an axis.
    """
    axis = g.Axis(n)
    p1 = node_position(g, axis[-1])
    a0 = axis[0]
    if g.parent(a0):
        a0 = g.parent(a0)
    p0 = node_position(g, a0)
    return p0, p1


def axis_extremities_angle(g, n, refdir=(0, 0, 1)):
    """
    Determine the angle between a reference direction and the extremities of an axis.
    """
    p0, p1 = axis_extremities(g, n)
    return angle(p1 - p0, refdir)


def angle(direction, refdir=(0, 0, 1)):
    """
    Determine the angle between a direction and a reference direction (in degrees).
    """
    cosinus = np.dot(direction, refdir)
    vy = np.cross(direction, refdir)
    sinus = norm(vy)
    return degrees(atan2(sinus, cosinus))


def axis_subpart(g, axisroot, beglengthratio, endlengthratio):
    """
    Extract a subpart of an axis.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed, on which to determine the trunk radius.
    axisroot: int
        Node id to determine the axis.
    beglengthratio: float
        Ratio of the length of the subpart to extract to the beginning of the axis.
    endlengthratio: float
        Ratio of the length of the subpart to extract to the end of the axis.

    Returns
    ~~~~~~~
        List of node ids of the subpart of the axis.
    """
    data = axis_nodes_normedposition(g, axisroot)
    beg = 0
    end = len(data) - 1
    while data[beg][1] < beglengthratio:
        if beg + 1 == end or data[beg + 1][1] >= endlengthratio:
            break
        else:
            beg += 1
    while data[end][1] > endlengthratio:
        if end - 1 == beg or data[end - 1][1] <= beglengthratio:
            break
        else:
            end -= 1
    return [node for node, _ in data[beg : end + 1]]


def axis_subpart_angle(g, axisroot, beglengthratio, endlengthratio, refdir=(0, 0, 1)):
    """
    Determine the angle between a subpart of an axis and a reference direction.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed, on which to determine the trunk radius.
    axisroot: int
        Node id to determine the axis.
    beglengthratio: float
        Ratio of the length of the subpart to extract to the beginning of the axis.
    endlengthratio: float
        Ratio of the length of the subpart to extract to the end of the axis.
    refdir: Vector3
        Reference direction.

    Returns
    ~~~~~~~
        Angle (in degrees) between the subpart of the axis and the reference direction.
    """
    nodes = axis_subpart(g, axisroot, beglengthratio, endlengthratio)
    positions = [node_position(g, n) for n in nodes]
    if len(positions) > 2:
        return angle(Line.estimate(positions).direction, refdir)
    return angle(positions[1] - positions[0], refdir)


def axis_nodes_normedposition(g, axisroot):
    data = [(node, node_length(g, node)) for node in g.Axis(axisroot)]
    length = 0
    for i in range(len(data)):
        length += data[i][1]
        data[i] = (data[i][0], length)
    res = [(node, len_n / length) for node, len_n in data]
    if g.parent(axisroot) is not None:
        res = [(g.parent(axisroot), 0)] + res
    return res


def trunk_direction(g, trunkratio=1):
    """
    Determine the direction of the trunk.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object reconstructed, on which to determine the trunk direction.
    trunkratio: float
        Ratio of the trunk length to the total length of the trunk.

    Returns
    ~~~~~~~
        A list of Vector3 objects representing the direction of the trunk.
    """
    nodes = axis_subpart(g, trunk_root(g), 0, trunkratio)
    positions = [node_position(g, v) for v in nodes]
    line = Line.estimate(positions)
    return line.direction


def trunk_lateral_axes(g, length_threshold=0.05):
    """
    Returns the trunk lateral axes. Two lists are returned, the first one
    is the short axes, the second one is the long axes.

    Parameters
    ~~~~~~~~~~
    g : openalea.mtg.MTG
        MTG object
    length_threshold : float
        minimum length of long lateral axis

    Returns
    ~~~~~~~
    shortaxis, longaxis : list
        list of lateral axis nodes. Short axis if smaller than length_threshold,
        long otherwise.
    """
    trunknodes = trunk_nodes(g)
    shortaxis, longaxis = [], []
    for n in trunknodes:
        for lateral in lateral_children(g, n):
            if axis_length(g, lateral) >= length_threshold:
                longaxis.append(lateral)
            else:
                shortaxis.append(lateral)
    return shortaxis, longaxis


def lateral_children(g, vid):
    """
    Returns a list of the lateral children of a node.
    """
    return [cid for cid in g.children(vid) if g.edge_type(cid) == "+"]


def trunk_root(g):
    """
    Returns the root node of the trunk.
    """
    return g.roots(scale=g.max_scale())[0]


def trunk_nodes(g):
    """
    Returns the nodes of the trunk.
    """
    return g.Axis(trunk_root(g))
