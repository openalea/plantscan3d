from openalea.plantgl.all import *


def initialize_mtg(root, nodelabel="N"):
    """
    Initialize a new MTG with a single node at the given position.

    Parameters
    ~~~~~~~~~~
    root: Vector3
        Position of the root node.
    nodelabel: str
        Label for the nodes (default "N").

    Returns
    ~~~~~~~
    openalea.mtg.MTG
        New MTG with one node.
    """
    from openalea.mtg import MTG

    mtg = MTG()
    plantroot = mtg.root
    branchroot = mtg.add_component(plantroot, label="P")
    noderoot = mtg.add_component(branchroot, label=nodelabel)
    mtg.property("position")[noderoot] = root
    mtg.property("radius")[noderoot] = None
    assert len(mtg.property("position")) == 1
    return mtg


def mtg2pgltree(mtg):
    """
    Convert an MTG to a PlantGL tree representation.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object to convert.

    Returns
    ~~~~~~~
    tuple
        (nodes, parents, vertex2node) where nodes is a list of positions,
        parents is a list of parent indices, and vertex2node maps MTG
        vertex ids to list indices.
    """
    vertices = mtg.vertices(scale=mtg.max_scale())
    vertex2node = dict([(vid, i) for i, vid in enumerate(vertices)])
    positions = mtg.property("position")
    nodes = [positions[vid] for vid in vertices]
    parents = [
        vertex2node[mtg.parent(vid)] if mtg.parent(vid) else vertex2node[vid]
        for vid in vertices
    ]
    return nodes, parents, vertex2node


def pgltree2mtg(
    mtg,
    startfrom,
    parents,
    positions,
    radii=None,
    filter_short_branch=False,
    angle_between_trunk_and_lateral=60,
    nodelabel="N",
):
    """
    Convert a PlantGL tree representation back into an MTG.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object to add nodes to.
    startfrom: int
        Starting node id in the MTG.
    parents: list of int
        Parent indices for each node in the tree.
    positions: list of Vector3
        Positions of each node.
    radii: list of float or None
        Radii of each node. If None, no radius property is set.
    filter_short_branch: bool
        If True, remove branches with no children.
    angle_between_trunk_and_lateral: float
        Angle threshold in degrees to determine edge type between
        trunk and lateral branches.
    nodelabel: str
        Label for the nodes (default "N").

    Returns
    ~~~~~~~
    openalea.mtg.MTG
        MTG with the tree added.
    """
    from math import acos, degrees

    rootpos = Vector3(mtg.property("position")[startfrom])
    if norm(positions[0] - rootpos) > 1e-3:
        if len(mtg.children(startfrom)) > 0:
            edge_type = "+"
        else:
            edge_type = "<"
        startfrom = mtg.add_child(
            parent=startfrom,
            position=positions[0],
            label=nodelabel,
            edge_type=edge_type,
        )

    children, root = determine_children(parents)
    clength = subtrees_size(children, root)

    mchildren = list(children[root])
    npositions = mtg.property("position")
    removed = []
    if len(mchildren) >= 2 and filter_short_branch:
        mchildren = [c for c in mchildren if len(children[c]) > 0]
        if len(mchildren) != len(children[root]):
            removed = list(set(children[root]) - set(mchildren))

    mchildren.sort(key=lambda x: -clength[x])
    toprocess = [
        (c, startfrom, "<" if i == 0 else "+") for i, c in enumerate(mchildren)
    ]
    while len(toprocess) > 0:
        nid, parent, edge_type = toprocess.pop(0)
        pos = positions[nid]
        parameters = dict(
            parent=parent, label=nodelabel, edge_type=edge_type, position=pos
        )
        if radii:
            parameters["radius"] = radii[nid]
        mtgnode = mtg.add_child(**parameters)
        mchildren = list(children[nid])
        if len(mchildren) > 0:
            if len(mchildren) >= 2 and filter_short_branch:
                mchildren = [c for c in mchildren if len(children[c]) > 0]
                if len(mchildren) != len(children[nid]):
                    removed = list(set(children[nid]) - set(mchildren))
            if len(mchildren) > 0:
                mchildren.sort(key=lambda x: -clength[x])
                first_edge_type = "<"
                langle = degrees(
                    acos(
                        dot(
                            direction(pos - npositions[parent]),
                            direction(positions[mchildren[0]] - pos),
                        )
                    )
                )
                if langle > angle_between_trunk_and_lateral:
                    first_edge_type = "+"
                edges_types = [first_edge_type] + [
                    "+" for i in range(len(mchildren) - 1)
                ]
                toprocess += [(c, mtgnode, e) for c, e in zip(mchildren, edges_types)]
    print("Remove short nodes ", ",".join(map(str, removed)))
    return mtg


def gaussian_weight(x, var):
    """
    Compute a Gaussian weight at a given value.

    Parameters
    ~~~~~~~~~~
    x: float
        Input value.
    var: float
        Variance of the Gaussian distribution.

    Returns
    ~~~~~~~
    float
        Gaussian weight exp(-x²/(2*var)) / sqrt(2*pi*var²).
    """
    from math import exp, pi, sqrt

    return exp(-(x**2) / (2 * var)) / sqrt(2 * pi * var * var)


def gaussian_filter(mtg, propname, considerapicalonly=True):
    """
    Apply a Gaussian filter to smooth a property along the MTG.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object.
    propname: str
        Name of the property to filter.
    considerapicalonly: bool
        If True, only consider apical (edge_type "<") children.
        Default to True.

    Returns
    ~~~~~~~
        None. The property is updated in-place.
    """
    prop = mtg.property(propname)
    nprop = dict()
    gw0 = gaussian_weight(0, 1)
    gw1 = gaussian_weight(1, 1)
    for vid, value in list(prop.items()):
        nvalues = [value * gw0]
        parent = mtg.parent(vid)
        if parent and parent in prop:
            nvalues.append(prop[parent] * gw1)
        children = mtg.children(vid)
        if considerapicalonly:
            children = [child for child in children if mtg.edge_type(child) == "<"]
        for child in children:
            if child in prop:
                nvalues.append(prop[child] * gw1)

        nvalue = sum(nvalues[1:], nvalues[0]) / sum([gw0 + (len(nvalues) - 1) * gw1])
        nprop[vid] = nvalue

    prop.update(nprop)


def threshold_filter(mtg, propname):
    """
    Apply a threshold filter to a property, preventing values from
    increasing along the traversal from root to leaves.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object.
    propname: str
        Name of the property to filter.

    Returns
    ~~~~~~~
        None. The property is updated in-place.
    """
    from openalea.mtg.traversal import iter_mtg2

    prop = mtg.property(propname)
    nprop = dict()
    for vid in iter_mtg2(mtg, mtg.root):
        if vid in prop:
            parent = mtg.parent(vid)
            if parent and parent in prop:
                pvalue = nprop.get(parent, prop[parent])
                if pvalue < prop[vid]:
                    nprop[vid] = pvalue

    prop.update(nprop)


def get_first_param_value(mtg, propname):
    """
    Get the first non-None property value at the maximum scale.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object.
    propname: str
        Name of the property.

    Returns
    ~~~~~~~
    object or None
        First non-None property value found at the maximum scale,
        or None if no such value exists.
    """
    from openalea.mtg.traversal import iter_mtg2

    scale = mtg.max_scale()

    prop = mtg.property(propname)
    for vid in iter_mtg2(mtg, mtg.root):
        if vid in prop and mtg.scale(vid) == scale and prop[vid] is not None:
            return prop[vid]


def pipemodel(mtg, rootradius=None, leafradius=None, root=None):
    """
    Uses the pipemodel algorithm to estimate the radius of each node of the MTG.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object to be processed.
    rootradius: float | None
        Radius of the root node. If None, the radius of the first node is used.
        Default to None.
    leafradius: float | None
        Radius of the leaf nodes. If None, it is estimated as 1/100 of the root radius.
        Default to None.
    root: int | None
        Id of the root node. If None, the root node is selected automatically.

    Returns
    ~~~~~~~
        MTG with a new or updated radius property computed using the pipe model algorithm.
    """
    from math import log

    from openalea.mtg.traversal import post_order2

    if root is None:
        roots = mtg.roots(scale=mtg.max_scale())
        assert len(roots) == 1
        root = roots[0]
    if rootradius is None:
        if "radius" not in mtg.properties():
            raise KeyError("Property 'radius' is not defined in the MTG.")
        rootradius = mtg.property("radius")[root]
    if leafradius is None:
        leafradius = rootradius / 100.0

    vertices = list(post_order2(mtg, root))

    leaves = [vid for vid in vertices if len(mtg.children(vid)) == 0]
    # pipeexponent = log(len(leaves)) / (log(rootradius) - log(leafradius))
    # print pipeexponent
    # invpipeexponent = 1./ pipeexponent

    radiusprop = dict()
    for vid in leaves:
        radiusprop[vid] = leafradius

    nbelems = dict()
    for vid in leaves:
        nbelems[vid] = 1
    for vid in vertices:
        if vid not in nbelems:
            nbelems[vid] = sum([nbelems[child] for child in mtg.children(vid)]) + 1

    print(root, nbelems[root])

    # pipeexponent = log(nbelems[root]) / (log(rootradius) - log(leafradius))
    pipeexponent = (log(rootradius) - log(leafradius)) / log(nbelems[root])
    print(pipeexponent)
    # invpipeexponent = 1.0 / pipeexponent

    for vid in vertices:
        if vid not in radiusprop:
            radiusprop[vid] = leafradius * (nbelems[vid] ** pipeexponent)

    # for vid in post_order2(mtg, root):
    #    if not vid in radiusprop:
    #        rad = pow(sum([pow(radiusprop[child], pipeexponent) for child in mtg.children(vid)]), invpipeexponent)
    #        radiusprop[vid] = rad

    return radiusprop
