import os
from random import sample

from openalea.plantgl.all import (
    NurbsCurve2D,
    QuantisedFunction,
    Scene,
    connect_all_connex_components,
    densities_from_r_neighborhood,
    k_closest_points_from_ann,
    r_neighborhoods,
)

from .livnymethod import livny_method_mtg
from .mtgmanip import initialize_mtg
from .sca import adaptivespacecolonization_method, spacecolonization_method
from .xumethod import graphcolonization_method, xu_method


def load_points(filename):
    """
    Load a point cloud from a file.

    Parameters
    ~~~~~~~~~~
    filename: str
        Path to the file of the point cloud.

    Returns
    ~~~~~~~
        PointList of the point cloud.
    """
    # Check if file exists
    assert os.path.exists(filename)
    s = Scene(filename)
    # Check if pointList is on the loaded file
    assert len(s) == 1

    geom = s[0].geometry
    # Unwrap transformations if needed
    if hasattr(geom, "geometry"):
        # e.g. Translated, Scaled, etc.
        points = geom.geometry.pointList
        # points.translate(s[0].geometry.translation)
    else:
        points = geom.pointList
    return points


def subsample(points, ptsnb=None):
    """
    Subsample a point cloud using random.sample algorithm.

    Parameters
    ~~~~~~~~~~
    points: PointList
        PointList of the point cloud, usualy obtained with :func:`load_points`.
    ptsnb: int | None
        Number of points to keep.
        Default to None, which means that the number of points is kept as is.

    Returns
    ~~~~~~~
        PointList of the subsampled point cloud.
    """
    if ptsnb is None:
        return points
    else:
        nbPoints = len(points)
        subset = sample(range(nbPoints), ptsnb)
        return points.subset(subset)


def filter_points(points, densityfilterratio=0.05, densityradius=None, k=16):
    """
    Filter a point cloud using density estimation.

    Parameters
    ~~~~~~~~~~
    points: PointList
        PointList of the point cloud, usualy obtained with :func:`load_points`.
    densityfilterratio: float
        Density ratio to use to filter the point cloud using density estimation.
        Default to 0.05.
    densityradius: float
        Value of the radius to use to estimate the density. Default is None, which means that the
        value is calculated as 1/100 of the max-min of the point cloud in the z direction.
    k: int
        Number of neighbors to use to estimate the density. Default to 16.

    Returns
    ~~~~~~~
        PointList of the filtered point cloud.
    """
    # Determine default value of radius for density estimation
    if densityradius is None:
        mini, maxi = points.getZMinAndMaxIndex()
        zdist = points[maxi].z - points[mini].z
        densityradius = zdist / 100.0
    # Connect all points to k closest neighbors
    kclosests = k_closest_points_from_ann(points, k, True)
    kclosests = connect_all_connex_components(points, kclosests, True)
    # Determine the neighbors in a radius
    rnbgs = r_neighborhoods(points, kclosests, densityradius)
    # Estimate densities
    densities = densities_from_r_neighborhood(rnbgs, densityradius)
    # Determine value of density under which we filter
    mind, maxd = densities.getMinAndMax(True)
    densitythreshold = mind + (maxd - mind) * densityfilterratio
    # Determine index of points to filter
    nbPoints = len(points)
    subset = [i for i in range(nbPoints) if densities[i] < densitythreshold]
    # Return result
    return points.opposite_subset(subset)


def find_root(points):
    """
    Find the root of the point cloud.

    Notes
    ~~~~~
    We define the center of the point cloud as (x_c, y_c, z_c). Then the root is defined
    as the closest point from the cloud to the point (x_c, y_c, z_min)

    Parameters
    ~~~~~~~~~~
    points: PointList
        PointList of the point cloud, usualy obtained with :func:`load_points`.

    Returns
    ~~~~~~~
    Tuple of the root node id, the minimum z value and the maximum z value.
    """
    center = points.getCenter()
    pminid, pmaxid = points.getZMinAndMaxIndex()
    zmin = points[pminid].z
    zmax = points[pmaxid].z
    initp = center
    initp.z = zmin
    return points.findClosest(initp)[0], zmin, zmax


def skeleton(
    points,
    skel_func=xu_method,
    xu_binratio=50,
    xu_neighbors=20,
    gc_min_growth_length=None,
    gc_max_growth_length=None,
    gc_radius_func=None,
    sc_growth_length=None,
    sc_kill_distance_ratio=0.9,
    sc_presence_distance_ratio=2.5,
    sc_min_nb_pt_per_bud=5,
    asc_min_growth_length=None,
    asc_max_growth_length=None,
    asc_radius_func=None,
    asc_kill_distance_ratio=0.9,
    asc_presence_distance_ratio=2.5,
    asc_min_nb_pt_per_bud=5,
    livny_contraction_nb=3,
    livny_filtering_nb=5,
    livny_min_edge_ratio=0.15,
):
    """
    Topology reconstruction of a point cloud.

    Parameters
    ~~~~~~~~~~
    points: PointList
        PointList of the point cloud used to reconstruct topology.
    skel_func: function
        Reconstruction algorithm to use. Default to `xu_method`.
        Other possible algorithms are:
        - `graphcolonization_method`: Graph Colonization Algorithm
        - `spacecolonization_method`: Space colonization reconstruction
        - `adaptivespacecolonization_method`: Adaptive Space Colonization Algorithm
        - `livny_method_mtg`: Livny algorithm
    xu_binratio: float
        Value of the bin ratio to use to estimate the topology.
        Only used for XU method. Default to 50.
    xu_neighbors: int
        Number of neighbors to use to estimate the topology.
        Only used for XU method. Default to 20.
    gc_min_growth_length: float
        Minimum growth length for the graph colonization algorithm.
        Only used for Graph Colonization algorithm. Default to zdist / 200.
    gc_max_growth_length: float
        Maximum growth length for the graph colonization algorithm.
        Only used for Graph Colonization algorithm. Default to zdist / 50.
    gc_radius_func: function
        Density - bin length Relationship function for the graph colonization algorithm.
        Only used for Graph Colonization algorithm. Default to a NurbsCurve2D function with custom parameters.
    sc_growth_length: float
        Growth length for the space colonization algorithm.
        Only used for Space Colonization algorithm. Default to zdist / 50.
    sc_kill_distance_ratio: float
        Kill distance ratio for the space colonization algorithm.
        Only used for Space Colonization algorithm. Default to 0.9.
    sc_presence_distance_ratio: float
        Perception distance ratio for the space colonization algorithm.
        Only used for Space Colonization algorithm. Default to 2.5.
    sc_min_nb_pt_per_bud: int
        Minimum number of points per bud for the space colonization algorithm.
        Only used for Space Colonization algorithm. Default to 5.
    asc_max_growth_length: float
        Maximum growth length for the adaptive space colonization algorithm.
        Only used for Adaptive Space Colonization algorithm. Default to zdist / 50.
    asc_min_growth_length: float
        Minimum growth length for the adaptive space colonization algorithm.
        Only used for Adaptive Space Colonization algorithm. Default to zdist / 100.
    asc_radius_func: function
        Density - Radius Relationship function for the adaptive space colonization algorithm.
        Only used for Adaptive Space Colonization algorithm. Default to a NurbsCurve2D function with custom parameters.
    asc_kill_distance_ratio: float
        Kill distance ratio for the adaptive space colonization algorithm.
        Only used for Adaptive Space Colonization algorithm. Default to 0.9.
    asc_presence_distance_ratio: float
        Perception distance ratio for the adaptive space colonization algorithm.
        Only used for Adaptive Space Colonization algorithm. Default to 2.5.
    asc_min_nb_pt_per_bud: int
        Minimum number of points per bud for the adaptive space colonization algorithm.
        Only used for Adaptive Space Colonization algorithm. Default to 5.
    livny_contraction_nb: int
        Number of contraction steps for the livny algorithm.
        Only used for Livny algorithm. Default to 3.
    livny_filtering_nb: int
        Number of filtering steps for the livny algorithm.
        Only used for Livny algorithm. Default to 5.
    livny_min_edge_ratio: int
        Ratio of the minimum edge size for the livny algorithm.
        Only used for Livny algorithm. Default to 0.15.

    Returns
    ~~~~~~~
        openalea.mtg.MTG object representing the topology of the point cloud.
    """
    root, zmin, zmax = find_root(points)

    mtg = initialize_mtg(root)
    zdist = zmax - zmin

    vtx = list(mtg.vertices(mtg.max_scale()))
    startfrom = vtx[0]

    def call_xu():
        binlength = zdist / xu_binratio
        return skel_func(mtg, startfrom, points, binlength, xu_neighbors)

    def call_gc():
        densities = mtg.pointinfo.densities
        max_length = (
            asc_max_growth_length if gc_max_growth_length is not None else zdist / 50
        )
        min_length = (
            asc_min_growth_length if gc_min_growth_length is not None else zdist / 200
        )
        if gc_radius_func is None:
            radius_func = NurbsCurve2D(
                [(0, 0, 1), (0.3, 0.3, 1), (0.7, 0.7, 1), (1, 1, 1)]
            )
        else:
            radius_func = gc_radius_func
        return skel_func(
            mtg,
            startfrom,
            points,
            densities,
            min_length,
            max_length,
            QuantisedFunction(radius_func.__deepcopy__({})),
        )

    def call_sc():
        length = sc_growth_length if sc_growth_length is not None else zdist / 50
        return skel_func(
            mtg,
            startfrom,
            points,
            length,
            sc_kill_distance_ratio,
            sc_presence_distance_ratio,
            sc_min_nb_pt_per_bud,
        )

    def call_asc():
        densities = mtg.pointinfo.densities
        max_length = (
            asc_max_growth_length if asc_max_growth_length is not None else zdist / 50
        )
        min_length = (
            asc_min_growth_length if asc_min_growth_length is not None else zdist / 100
        )
        if asc_radius_func is None:
            radius_func = NurbsCurve2D(
                [(0, 0, 1), (0.3, 0.3, 1), (0.7, 0.7, 1), (1, 1, 1)]
            )
        else:
            radius_func = asc_radius_func
        return skel_func(
            mtg,
            startfrom,
            points,
            densities,
            min_length,
            max_length,
            QuantisedFunction(radius_func.__deepcopy__({})),
            asc_kill_distance_ratio,
            asc_presence_distance_ratio,
            asc_min_nb_pt_per_bud,
        )

    def call_livny():
        return skel_func(
            mtg,
            startfrom,
            points,
            livny_contraction_nb,
            livny_filtering_nb,
            livny_min_edge_ratio,
        )

    dispatch = {
        xu_method: call_xu,
        graphcolonization_method: call_gc,
        spacecolonization_method: call_sc,
        adaptivespacecolonization_method: call_asc,
        livny_method_mtg: call_livny,
    }

    try:
        return dispatch[skel_func]()
    except KeyError:
        raise ValueError(f"Unsupported skeleton function: {skel_func}")
