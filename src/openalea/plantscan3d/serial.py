# -*- coding: utf-8 -*-
from openalea.plantgl.all import *
from openalea.plantgl.codec.asc import *
from openalea.mtg.io import *


def getpointset(fn):
    """
    Read a point set from a PlantGL scene file.

    Parameters
    ~~~~~~~~~~
    fn: str
        Path to the scene file.

    Returns
    ~~~~~~~
    tuple
        (pointList, translation) from the first shape in the scene.
    """
    scene = Scene(fn)
    points = scene[0].geometry.geometry.pointList
    tr = scene[0].geometry.translation
    return points, tr

def quantisefunc(fn=None, qfunc=None):
    """
    Create a QuantisedFunction from a scene file or a function.

    Parameters
    ~~~~~~~~~~
    fn: str or None
        Path to a scene file.
    qfunc: object or None
        A function object to quantise.

    Returns
    ~~~~~~~
    openalea.plantgl.codec.QuantisedFunction
        Quantised version of the curve geometry.
    """
    if fn: s = Scene(fn)
    else : s = Scene([qfunc])
    curve = s[0].geometry
    curve = curve.deepcopy()
    
    return QuantisedFunction(curve) 
    
    
import pickle as pickle
def readfile(fn, mode='rb'):
    """
    Load a pickled object from a file.

    Parameters
    ~~~~~~~~~~
    fn: str
        Path to the file.
    mode: str
        File open mode (default 'rb').

    Returns
    ~~~~~~~
    object
        Unpickled object.
    """
    f = open(fn,mode)
    obj = pickle.load(f)
    f.close()
    return obj

def writefile(fn, obj):
    """
    Pickle an object to a file.

    Parameters
    ~~~~~~~~~~
    fn: str
        Path to the output file.
    obj: object
        Object to pickle.
    """
    f = open(fn,'wb')
    pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
    f.close()

    
def writeAscPoints(fn, points):
    """
    Write points to an ASCII PlantGL scene file.

    Parameters
    ~~~~~~~~~~
    fn: str
        Path to the output file.
    points: list of Vector3
        Points to write.
    """
    scene = Scene([Shape(PointSet(points), Material(ambient=(0,0,0)))])
    AscCodec().write(fn, scene)
  
def writeXYZ(fn, points):
    """
    Write points to a XYZ text file.

    Parameters
    ~~~~~~~~~~
    fn: str
        Path to the output file.
    points: list of Vector3
        Points to write, one per line as "x y z".
    """
    space = ' '
    newline = '\n'
    f = open(fn, 'w')
  
    s = str()
    for p in points:
        s += str(p.x) + space + str(p.y) + space + str(p.z) + newline
    
    f.write(s)
    f.close()

def max_heigth(g, scale = None):
    """
    Compute the maximum height (depth) of the MTG.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object.
    scale: int or None
        Scale to consider. If None, the maximum scale is used.

    Returns
    ~~~~~~~
    int
        Maximum number of successive nodes from root to leaf.
    """
    import openalea.mtg.traversal as traversal
    result = 0
    if scale is None:
        scale = g.max_scale()
    for r in g.roots(scale):
        mvalue = {}
        for vid in traversal.post_order(g, r):
            mvalue[vid] = max([mvalue[c]+1 for c in g.children(vid)]+[1])
        result = max(mvalue[r], result)
    return result

def max_order(g, scale = None):
    """
    Compute the maximum branching order of the MTG.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        MTG object.
    scale: int or None
        Scale to consider. If None, the maximum scale is used.

    Returns
    ~~~~~~~
    int
        Maximum number of successive lateral branches (edge_type '+')
        from root to leaf.
    """
    import openalea.mtg.traversal as traversal
    result = 0
    if scale is None:
        scale = g.max_scale()
    for r in g.roots(scale):
        mvalue = {}
        for vid in traversal.post_order(g, r):
            mvalue[vid] = max([mvalue[c]+(1 if g.edge_type(vid) == '+' else 0) for c in g.children(vid)]+[1])
        result = max(mvalue[r], result)
    return result

    
def writeMTGfile(fn, g, properties=[('XX','REAL'), ('YY','REAL'), ('ZZ','REAL'), ('radius','REAL')]):
    """
    Write an MTG to an MTG file format.

    Parameters
    ~~~~~~~~~~
    fn: str
        Path to the output file.
    g: openalea.mtg.MTG
        MTG object to write.
    properties: list of tuple
        List of (property_name, type) pairs to include.
        Defaults to position and radius properties.
    """
    if properties == []:
      properties = [(p, 'REAL') for p in g.property_names() if p not in ['edge_type', 'index', 'label']]
    nb_tab = max_order(g)
    str = write_mtg(g, properties, nb_tab=nb_tab+1)
    f = open(fn, 'w')
    f.write(str)
    f.close()
  

def convertToStdMTG(g):
  """
  Convert an MTG with a 'position' property to separate XX, YY, ZZ properties.

  Parameters
  ~~~~~~~~~~
  g: openalea.mtg.MTG
      MTG object with a Vector3 'position' property.

  Returns
  ~~~~~~~
  openalea.mtg.MTG
      New MTG with XX, YY, ZZ scalar properties instead of 'position'.
  """
  from copy import deepcopy
  newg = deepcopy(g)
  
  pdic = newg.property('position')
  xx = {}
  yy = {}
  zz = {}
  
  for i,v in pdic.items():
      xx[i] = v.x
      yy[i] = v.y
      zz[i] = v.z
  
  newg.add_property('XX')
  newg.add_property('YY')
  newg.add_property('ZZ')
  newg.property('XX').update(xx)
  newg.property('YY').update(yy)
  newg.property('ZZ').update(zz)
  del newg.properties()['position']
  return newg


def convertToMyMTG(mtg):
    """
    Convert an MTG with XX, YY, ZZ properties back to a Vector3 'position' property.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object with XX, YY, ZZ scalar properties.

    Returns
    ~~~~~~~
    openalea.mtg.MTG
        The same MTG with a 'position' property added and scalar properties removed.
    """
    from copy import deepcopy
    g = deepcopy(mtg)

    position = {}

    XXpropname = 'XX' if 'XX' in g.properties() else 'X'
    YYpropname = 'YY' if 'YY' in g.properties() else 'Y'
    ZZpropname = 'ZZ' if 'ZZ' in g.properties() else 'Z'

    XX = g.property(XXpropname)
    YY = g.property(YYpropname)
    ZZ = g.property(ZZpropname)    

    for i,x in XX.items():
        position[i] = Vector3(x,YY[i],ZZ[i])

    for propname in [XXpropname, YYpropname, ZZpropname]:
        del g.properties()[propname]

    mtg.property('position').update(position)
    
    return mtg

def complete_lines(mtg):
    """
    Propagate '_line' property values upward to parent nodes that lack them.

    Parameters
    ~~~~~~~~~~
    mtg: openalea.mtg.MTG
        MTG object with a '_line' property.
    """
    lines = mtg.property('_line')
    nlines = dict(lines)
    for vid, line in list(lines.items()):
        while mtg.parent(vid) and lines.get(mtg.parent(vid)) == None:              
            vid = mtg.parent(vid)
            nlines[vid] = line
    lines.update(nlines)

  
from openalea.plantgl.all import *
def convertStdMTGWithNode(g, useHeuristic = True, 
                             invertCoord = False, 
                             propagate_parent = False):
    """
    Convert a standard MTG (with XX, YY, ZZ properties) to an MTG with a
    Vector3 'position' property, handling interpolation and heuristics.

    Parameters
    ~~~~~~~~~~
    g: openalea.mtg.MTG
        Standard MTG object with XX, YY, ZZ scalar properties and '_line'.
    useHeuristic: bool
        If True, use a heuristic to estimate positions for nodes that
        could not be otherwise positioned.
    invertCoord: bool
        If True, negate the Z coordinate.
    propagate_parent: bool
        If True, propagate parent positions when a node's complex root
        has coordinates but the node itself does not.

    Returns
    ~~~~~~~
        None. The MTG is modified in-place with a 'position' property.
    """
    from openalea.mtg import MTG

    XXpropname = 'XX' if 'XX' in g.properties() else 'X'
    YYpropname = 'YY' if 'YY' in g.properties() else 'Y'
    ZZpropname = 'ZZ' if 'ZZ' in g.properties() else 'Z'

    XX = g.property(XXpropname)
    YY = g.property(YYpropname)
    ZZ = g.property(ZZpropname)

    lines = g.property('_line')
    complete_lines(g)

    positions = dict()

    scale = g.max_scale()
    dointerpolation = False

    def toVector3(vtx): return Vector3(XX[vtx],YY[vtx], -ZZ[vtx] if invertCoord else ZZ[vtx])

    for vtx in g.vertices(scale):
        v = None
        if vtx in XX:
            v = toVector3(vtx)
            positions[vtx] = v

        for i in range(scale+1, 0, -1):
            cpx = g.complex_at_scale(vtx, scale=i)
            if vtx in g.component_roots_at_scale(cpx, scale=scale) and cpx in XX:
                v = toVector3(cpx)
                parent =  g.parent(vtx)
                if (g.edge_type(vtx) == '+') and (not parent in XX) and (len(g.children(parent)) == 1 or propagate_parent):
                    positions[parent] = v
                else:
                    positions[vtx] = v
                    

    notpositionned =  set(g.vertices(scale)) - set(positions.keys())
    if len(notpositionned) > 0:
        print('interpolate positions')
        positionned = list(positions.keys())

        components = dict()
        cparent = dict()
        for vtx in positionned:
            ancestors = g.Ancestors(vtx, EdgeType = '<')
            if len(ancestors) == 0: continue
            if ancestors[0] == vtx: ancestors.pop(0)
            if len(ancestors) == 0: continue

            if g.parent(ancestors[-1]):
                ancestors.append(g.parent(ancestors[-1]))
            if g.parent(ancestors[-1]):
                ancestors.append(g.parent(ancestors[-1]))

            for i,p in enumerate(ancestors):
                if p in positions:
                    break
            else:
                continue
                i = None

            posi = positions[vtx]            
            if not i is None:
                axe = ancestors[:i]
                posj = positions[ancestors[i]]
                cparent[vtx] = ancestors[i]
            else:
                axe = ancestors
                posj = None
                cparent[vtx] = ancestors[-1]

            components[vtx] = (posi, posj, axe)

        a = [(vtx, lines[vtx], info[2]) for vtx, info in list(components.items())]
        a.sort(key=lambda v:v[1])

        for vtx, info in list(components.items()):
            posi, posj, axe = info
            nbseg = len(axe)+1

            for i,v in enumerate(axe,1):
                positions[v] = posi * ((nbseg-i)/float(nbseg)) + posj * (i/float(nbseg))


    notpositionned =  set(g.vertices(scale)) - set(positions.keys())
    #print notpositionned
    #print [g.property('_line').get(vid) for vid in notpositionned]
    if len(notpositionned) > 0 and useHeuristic:
        print('use heuristic for', list(notpositionned))
        groups = []
        while len(notpositionned) > 0:
            seed = notpositionned.pop()
            group = [seed]
            p = g.parent(seed)
            while p in notpositionned:
                notpositionned.discard(p)
                group.insert(0,p)
            c = seed
            while True:
                ch = g.children(c)
                if len(ch) > 1:
                    raise ValueError('Cannot determine coordinates for branch starting at:'+str(seed)+' at lines '+str(lines.get(seed)))
                if len(ch) == 1:
                    c = ch[0]
                    #assert c in notpositionned
                    if not c in notpositionned: break
                    notpositionned.discard(c)
                    group.append(c)
                else: break
            groups.append(group)
        for group in groups:
            p = g.parent(group[0])
            initpos = positions[p]
            parentdir = initpos - positions[g.parent(p)]
            length = parentdir.normalize()
            latdir = parentdir.anOrthogonalVector()
            for i,vid in enumerate(group,1):
                positions[vid] = initpos + i * length * latdir

    if 'Diameter' in g.property_names():
        g.property('radius').update(dict([(vid,d/2.) for vid,d in list(g.property('Diameter').items())]))
    g.property('position').update(positions)



