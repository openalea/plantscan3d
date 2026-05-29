from openalea.plantgl.all import *


def livny_contraction(pointList, root, connectall=True, adjacencies=None):
    """
    Perform a single Livny contraction step on a point cloud skeleton.

    Parameters
    ~~~~~~~~~~
    pointList: list of Vector3
        Input points representing the skeleton.
    root: int
        Index of the root point.
    connectall: bool
        If True, ensure all components are connected.
    adjacencies: list of list of int or None
        Precomputed adjacency lists. If None, computed from k=7 nearest neighbours.

    Returns
    ~~~~~~~
    tuple
        (newPointList, parents, weights) after contraction.
    """
    if adjacencies is None:
        adjacencies = k_closest_points_from_ann(pointList, 7, True)
        if connectall:
            adjacencies = connect_all_connex_components(pointList, adjacencies, True)
    parents, distances = points_dijkstra_shortest_path(pointList, adjacencies, root)
    weights = carried_length(pointList, parents)
    weights += 1
    orientationList = optimize_orientations(pointList, parents, weights)
    newPointList = optimize_positions(pointList, orientationList, parents, weights)
    return newPointList, parents, weights


def livny_method(
    pointList,
    root,
    connectall=True,
    nbcontractionsteps=3,
    maxfiltering=10,
    minedgeratio=0.15,
):
    """
    Reconstruct a tree skeleton using the Livny method.

    Parameters
    ~~~~~~~~~~
    pointList: list of Vector3
        Input point cloud.
    root: int
        Index of the root point.
    connectall: bool
        If True, ensure all components are connected.
    nbcontractionsteps: int
        Number of contraction iterations.
    maxfiltering: int
        Maximum number of node merging passes.
    minedgeratio: float
        Minimum edge length ratio for filtering short edges.

    Returns
    ~~~~~~~
    tuple
        (pointList, parents, radii) of the reconstructed skeleton.
    """
    firstPointList = pointList
    for i in range(nbcontractionsteps):
        pointList, parents, weights = livny_contraction(pointList, root, connectall)

    avgradius = average_radius(firstPointList, pointList, parents)
    print("average distance to points :", avgradius)
    print("compute radii")
    radii = estimate_radii_from_pipemodel(
        pointList, parents, weights.log(), avgradius / 10, 2.5
    )
    print("edge length characterization")
    elengths = min_max_mean_edge_length(pointList, parents=parents)
    minelength = elengths[0] + (elengths[1] - elengths[0]) * minedgeratio
    print("Filter nodes", minelength)
    shorts = detect_short_nodes(pointList, parents, minelength)
    print(
        "Percentage short node filtered :",
        100 * len(shorts) / float(len(pointList)),
        "(",
        len(shorts),
        ")",
    )
    pointList, parents, radii = remove_nodes(shorts, pointList, parents, radii)
    weights = carried_length(pointList, parents)

    itfilter = 0
    while itfilter < maxfiltering:
        itfilter += 1
        print("Filtering : pass", itfilter)
        merges = detect_similar_nodes(pointList, parents, radii, weights)
        print("similar nodes detected :", len(merges))

        nbmerges = len(merges)
        filtered = sum([len(i) - 1 for i in merges])
        filtering = set()
        for m in merges:
            for v in m:
                if v in filtering:
                    print(v, m)
                    print("multiple time same node in merge")
                else:
                    filtering.add(v)
        for m in merges:
            if parents[m[1]] == m[0]:
                if len(m) > 2:
                    p = m[1]
                    for v in m[2 : len(m)]:
                        if p != parents[v]:
                            print(m, [parents[i] for i in m])
                            assert False and "Not a child to merge"
                        p = v
            elif parents[m[1]] == parents[m[0]]:
                if len(m) > 2:
                    p = parents[m[1]]
                    for v in m[2 : len(m)]:
                        if p != parents[v]:
                            print(m, [parents[i] for i in m])
                            assert False and "Not a sibling to merge"
            else:
                assert False and "No siblings, no parent child to merge"

        print("Nb of merges :", nbmerges)
        print("Percentage filtered :", 100 * filtered / float(len(pointList)))
        if nbmerges == 0:
            break
        pointList, parents, radii = merge_nodes(
            merges, pointList, parents, radii, weights
        )
        print("recompute weights")
        weights = carried_length(pointList, parents)
        weights += 1
        avgradius = average_radius(firstPointList, pointList, parents)
        print("average distance to points :", avgradius)
        # print 'weights', weights.log()
        print("recompute radii")
        radii = estimate_radii_from_pipemodel(
            pointList, parents, weights.log(), avgradius / 10, 2.5
        )
    return pointList, parents, radii


def livny_method_mtg(
    mtg,
    startfrom,
    pointList,
    nbcontractionsteps=3,
    maxfiltering=10,
    filter_short_branch=False,
    angle_between_trunk_and_lateral=60,
):
    """
    Reconstruct a tree skeleton using Livny's method and add it to an MTG.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object to add the reconstructed tree to.
    startfrom: int
        Starting node id in the MTG.
    pointList: list of Vector3
        Input point cloud.
    nbcontractionsteps: int
        Number of contraction iterations.
    maxfiltering: int
        Maximum number of node merging passes.
    filter_short_branch: bool
        If True, remove branches with no children.
    angle_between_trunk_and_lateral: float
        Angle threshold in degrees for edge type determination.

    Returns
    ~~~~~~~
    openalea.mtg.MTG
        MTG of the reconstructed tree.
    """
    from .mtgmanip import pgltree2mtg

    connect_all_points = False if mtg.nb_vertices(mtg.max_scale()) > 1 else True
    rootpos = Vector3(mtg.property("position")[startfrom])
    root = len(pointList)
    pointList.append(rootpos)
    positions, parents, radii = livny_method(
        pointList, root, connect_all_points, nbcontractionsteps, maxfiltering
    )
    del pointList[root]
    return pgltree2mtg(
        mtg,
        startfrom,
        parents,
        positions,
        radii,
        filter_short_branch,
        angle_between_trunk_and_lateral,
    )
