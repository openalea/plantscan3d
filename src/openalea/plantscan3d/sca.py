from openalea.plantgl.all import *

from .mtgmanip import pgltree2mtg


def adaptivespacecolonization_method(
    mtg,
    startfrom,
    pointList,
    densities,
    mingrowthlength,
    maxgrowthlength,
    growthlengthfunc,
    killradiusratio,
    perceptionradiusratio,
    min_nb_pt_per_bud,
    filter_short_branch=False,
    angle_between_trunk_and_lateral=60,
):
    """
    Reconstruct a tree skeleton using adaptive space colonization with density-dependent growth.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object to add the reconstructed tree to.
    startfrom: int
        Starting node id in the MTG.
    pointList: list of Vector3
        Input point cloud.
    densities: list of float
        Density values per point for adaptive growth length.
    mingrowthlength: float
        Minimum growth length.
    maxgrowthlength: float
        Maximum growth length.
    growthlengthfunc: callable
        Function mapping normalised density to a growth length factor.
    killradiusratio: float
        Ratio of growth length for the kill radius.
    perceptionradiusratio: float
        Ratio of growth length for the perception radius.
    min_nb_pt_per_bud: int
        Minimum number of points per bud.
    filter_short_branch: bool
        If True, remove branches with no children.
    angle_between_trunk_and_lateral: float
        Angle threshold in degrees for edge type determination.

    Returns
    ~~~~~~~
    openalea.mtg.MTG
        MTG of the reconstructed tree.
    """
    rootpos = Vector3(mtg.property("position")[startfrom])

    mindensity, maxdensity = densities.getMinAndMax()
    deltadensity = maxdensity - mindensity
    growthlengthfunc.clamped = False
    normeddensity = lambda x: growthlengthfunc(abs(x - mindensity) / deltadensity)

    deltabinlength = maxgrowthlength - mingrowthlength
    binlength = lambda x: mingrowthlength + deltabinlength * normeddensity(x)

    print(
        maxgrowthlength,
        maxgrowthlength * killradiusratio,
        maxgrowthlength * perceptionradiusratio,
    )

    class CustomSCA(SpaceColonization):
        def __init__(self, *args):
            SpaceColonization.__init__(self, *args)

        def node_buds_preprocess(self, nid):
            pos = self.node_position(nid)
            components = self.node_attractors(nid)
            # print nid, self.parents[nid], pos, components
            aid, aidist = findClosestFromSubset(pos, pointList, components)
            adensity = densities[aid]

            l = binlength(adensity)
            assert l >= mingrowthlength
            self.setLengths(l, killradiusratio, perceptionradiusratio)

    sc = CustomSCA(
        pointList,
        maxgrowthlength,
        maxgrowthlength * killradiusratio,
        maxgrowthlength * perceptionradiusratio,
        rootpos,
    )
    sc.min_nb_pt_per_bud = min_nb_pt_per_bud
    sc.run()

    nodes = sc.nodes
    parents = sc.parents

    pgltree2mtg(
        mtg,
        startfrom,
        parents,
        nodes,
        None,
        filter_short_branch,
        angle_between_trunk_and_lateral,
    )

    return mtg


def spacecolonization_method(
    mtg,
    startfrom,
    pointList,
    growthlength,
    killradiusratio,
    perceptionradiusratio,
    min_nb_pt_per_bud,
    filter_short_branch=False,
    angle_between_trunk_and_lateral=60,
):
    """
    Reconstruct a tree skeleton using space colonization.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object to add the reconstructed tree to.
    startfrom: int
        Starting node id in the MTG.
    pointList: list of Vector3
        Input point cloud.
    growthlength: float
        Growth length for each iteration.
    killradiusratio: float
        Ratio of growth length for the kill radius.
    perceptionradiusratio: float
        Ratio of growth length for the perception radius.
    min_nb_pt_per_bud: int
        Minimum number of points per bud.
    filter_short_branch: bool
        If True, remove branches with no children.
    angle_between_trunk_and_lateral: float
        Angle threshold in degrees for edge type determination.

    Returns
    ~~~~~~~
    openalea.mtg.MTG
        MTG of the reconstructed tree.
    """
    rootpos = Vector3(mtg.property("position")[startfrom])

    sc = SpaceColonization(
        pointList,
        growthlength,
        growthlength * killradiusratio,
        growthlength * perceptionradiusratio,
        rootpos,
    )
    sc.min_nb_pt_per_bud = min_nb_pt_per_bud
    sc.run()

    nodes = sc.nodes
    parents = sc.parents

    pgltree2mtg(
        mtg,
        startfrom,
        parents,
        nodes,
        None,
        filter_short_branch,
        angle_between_trunk_and_lateral,
    )

    return mtg

