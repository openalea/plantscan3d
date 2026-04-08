Cleaning Point cloud
####################

This section explain how to use the tools to clean a point cloud and segment it.
All algorithms not delete directly the points but select its with the selection system of PlanScan3d (see also: :ref:`selection-doc-ref`).

.. image:: /images/treatment/treatment.png
    :scale: 40

Soil Selection
--------------

The goal of this algorithm is to select the points that belongs to the soil and not keep the weed that do up to the soil (**Points -> Selection -> Soil**).
To do that, we select a percent of points that are on the top of the scan (see below: the first parameter) and we go down through the point's neighborhood.
For each point, we check its height and test if it is below a threshold (see below: the second parameter).

.. image:: /images/treatment/soil_param.png
    :scale: 50

The parameters of this algorithm are :
    * Top height percent : this parameter is the percent of the height of the scan that will be taken as start points. The default value is 10% but you can change it if you want but not exceed 70% because it's possible that the algorithm will keep the weed as start.
    * Bottom threshold : this parameter control the height were the algorithm will stop go down, this parameter is estimated with the barycenter of the scan. We recommend to keep the value that is calculated.

.. image:: /images/treatment/soil.png
    :scale: 40

You can notice that a few points above the soil are select, this is normal because there is isolated points.

+--------------------------------------------+-----------------------------------------------+
| Before                                     | After                                         |
+============================================+===============================================+
| .. image:: /images/treatment/treatment.png | .. image:: /images/treatment/soil_deleted.png |
+--------------------------------------------+-----------------------------------------------+

You can also test this algorithm in a python script (See: :download:`point cloud used of this example </scans_example/winter.ply>`)

.. code-block:: python

    from openalea.plantgl.all import *

    scene = Scene('winter.ply')
    points = scene[0].geometry.pointList
    topPercent = 10
    minZ = points[points.getZMinIndex()].z
    bottomThreshold = minZ + (points.getCenter().z - minZ) * 0.5

    soil_indexes = select_soil(points, IndexArray(0), topPercent, bottomThreshold)

    soil_points, other_points = points.split_subset(soil_indexes)
    shape1 = Shape(PointSet(soil_points), Material('red', Color3.RED))
    shape2 = Shape(PointSet(other_points), Material('blue', Color3.BLUE))

    Viewer.display(Scene([shape1, shape2]))

Wires Selection
---------------

The second step of the treatment pipeline is the clean of the wires.
The first things to do is to remove noise of the LIDAR, we calculate the densities of all points according of there neighborhood (**Points -> Density -> K-Density**).

.. image:: /images/treatment/k_density_param.png
    :scale: 50

The parameter of the k density is:
    * k is the number of neighborhood that is calculate for one point. We recommend to use the default number (16 neighborhood).

.. image:: /images/treatment/k_density.png
    :scale: 40

The next step is to remove the points that have a low density, so we use the filter min algorithm (**Points -> Filter -> Filter Min Density**).

.. image:: /images/treatment/filter_min_param.png
    :scale: 50

The single parameter of this algorithm is the percent of the low densities that will be deleted.
The default value is 5 percent but I recommend to set 3 or 2 percent because 5 percent could delete too much points and the algorithm to select the wire could fail.

+-------------------------------------------------+----------------------------------------------------+
| Before                                          | After                                              |
+=================================================+====================================================+
| .. image:: /images/treatment/isolate_points.png | .. image:: /images/treatment/no_isolate_points.png |
+-------------------------------------------------+----------------------------------------------------+

You can also test this algorithm in a python script (See: :download:`point cloud used of this example </scans_example/winter_step_01.ply>`)

.. code-block:: python

    from openalea.plantgl.all import *

    scene = Scene('winter_step_01.ply')
    points = scene[0].geometry.pointList
    k = 16
    densityratio = 3

    kclosests = k_closest_points_from_ann(points, k)
    densities = densities_from_k_neighborhood(points, kclosests, k)

    filter_indexes = filter_min_densities(densities, densityratio)

    isolate_points, other_points = points.split_subset(filter_indexes)
    shape1 = Shape(PointSet(isolate_points), Material('red', Color3.RED))
    shape2 = Shape(PointSet(other_points), Material('blue', Color3.BLUE))

    Viewer.display(Scene([shape1, shape2]))

The next step is to select two extremities of the wire with the selection tool and validate the selection with the action (**Points -> Selection -> Use selection for wire algorithm**).

.. image:: /images/treatment/wire_select_1.png
    :scale: 30

.. image:: /images/treatment/wire_select_2.png
    :scale: 30

Next start the wire algorithm (Points -> Selection -> Wire).
The algorithm calculate the shortest path between the extremities passing to the neighborhood and add a barycenter for each points of this path according to their neighborhood (see below: the first parameter).
Next the algorithm estimate radii of the wire for each barycenters (see below: the second parameter) and take the points that is inside a cylinder between two barycenters with the radius.

.. image:: /images/treatment/wire_param.png
    :scale: 50

The parameters of this algorithm are:
    * Barycenter radius value : this value is the radius of the neighborhood for each point on the path.
    * Get radii value : this is the radius of the neighborhood for each barycenters.

.. image:: /images/treatment/wire_seleted.png
    :scale: 40

+---------------------------------------+------------------------------------------+
| Before                                | After                                    |
+=======================================+==========================================+
| .. image:: /images/treatment/wire.png | .. image:: /images/treatment/no_wire.png |
+---------------------------------------+------------------------------------------+

You can also test this algorithm in a python script (See: :download:`point cloud used of this example </scans_example/winter_step_02.ply>`)

.. code-block:: python

    from openalea.plantgl.all import *
    import numpy

    scene = Scene('winter_step_02.ply')
    points = scene[0].geometry.pointList
    Ymin, Ymax = points.getYMinAndMaxIndex()
    bariRadius = 0.04
    radiiValue = 0.05

    kclosest_wire = IndexArray(0)
    wire_path = get_shortest_path(points, kclosest_wire, Ymin, Ymax)
    newpoint, baricenters = add_baricenter_points_of_path(points, kclosest_wire, wire_path, bariRadius)

    kclosest = k_closest_points_from_ann(newpoint, 20, True)

    radii = get_radii_of_path(newpoint, kclosest, baricenters, radiiValue)
    radius = numpy.average(radii)

    indexes = select_wire_from_path(newpoint, baricenters, radius, radii)
    wire_indexes = Index([])

    for i in indexes:
        if i not in baricenters:
            wire_indexes.append(i)

    wire_points, other_points = points.split_subset(wire_indexes)
    shape1 = Shape(PointSet(wire_points), Material('red', Color3.RED))
    shape2 = Shape(PointSet(other_points), Material('blue', Color3.BLUE))

    Viewer.display(Scene([shape1, shape2]))

Pole Selection
--------------

The pole selection (**Points -> Selection -> Pole**) is based on the RANSAC algorithm.
Using the graphical interface, you will be asked the click on each pole you want to select. When you're done, press Escape to leave the selection mode.
Selecting a point allows the RANSAC algortihm to concentrate on a specific area of the point cloud, therefore significantly decreasing the computation time.

.. image:: /images/treatment/pole_start_selection.png

.. image:: /images/treatment/pole_select_pole.png

This algorithm constructs cylinders between two randomly chosen points. Each of these cylinders must pass through the previously selected point.
Then, it counts the number of points inside and compute a score with it. This step is repeated 10.000 times.
Finally, the algorithm selects the cylinder with the best score.

.. image:: /images/treatment/pole_pole_selected.png

+---------------------------------------------------+-----------------------------------------------------+
| Before                                            | After                                               |
+===================================================+=====================================================+
| .. image:: /images/treatment/pole_select_pole.png | .. image:: /images/treatment/pole_pole_selected.png |
+---------------------------------------------------+-----------------------------------------------------+

You can also use this algorithm in a Python script (See: :download:`point cloud used of this example </scans_example/winter_step_03.ply>`)

The parameters are:
    * The radius of the cylinder created by the Ransac.
    * The percent of tolerance inside and outside the cylinder to take the points.
    * The number of cylinders generated before take the best one. This parameters impact the processing time.

.. code-block:: python

    from openalea.plantgl.all import *

    scene = Scene('winter_step_03.ply')
    points = scene[0].geometry.pointList
    poleRadius = 0.175
    tolerance = float(60) / 100
    iteration = 10000

    pole_indexes, score = select_pole_points_mt(self.points.pointList, poleRadius, iteration, tolerance)
    print 'score = ' + str(score)

    pole_points, other_points = points.split_subset(pole_indexes)
    shape1 = Shape(PointSet(pole_points), Material('red', Color3.RED))
    shape2 = Shape(PointSet(other_points), Material('blue', Color3.BLUE))

    Viewer.display(Scene([shape1, shape2]))

Point cloud Segmentation
------------------------

Here we segment the point cloud to get the trees separately (**Points -> Segment**).
You can change to the next tree the next action (**Points -> Next Segmented Tree**).
This algorithm is only base on the connex components so it not efficient.

========================================== ========================================== ========================================== ========================================== ==========================================
Tree1                                      Tree2                                      Tree3                                      Tree4                                      Tree5
========================================== ========================================== ========================================== ========================================== ==========================================
.. image:: /images/treatment/segment_1.png .. image:: /images/treatment/segment_2.png .. image:: /images/treatment/segment_3.png .. image:: /images/treatment/segment_4.png .. image:: /images/treatment/segment_5.png
========================================== ========================================== ========================================== ========================================== ==========================================

You can also test this algorithm in a python script (See: :download:`point cloud used of this example </scans_example/winter_step_04.ply>`)

.. code-block:: python

    from openalea.plantgl.all import *
    import random

    scene = Scene('winter_step_04.ply')
    points = scene[0].geometry.pointList

    kclosest = k_closest_points_from_ann(points, 10, True)
    connexsIndex = get_all_connex_components(points, kclosest)

    connexPoints = []  # type: List[Point3Array]
    for c in connexsIndex:
        if len(c) < 10000:
            continue
        connexPoints.append(points.split_subset(c)[0])

    mats = []  # type: List[pglsg.Material]
    while len(mats) != len(connexPoints):
        r = random.randrange(0, 256)
        g = random.randrange(0, 256)
        b = random.randrange(0, 256)
        color = Color3(r, g, b)
        inmats = False
        for m in mats:
            if m.ambient == color:
                inmats = True
                break
        if not inmats:
            mats.append(Material("mat" + str(len(mats)), color))

    shapes = []  # type: List[pglsg.Shape]
    for i in range(len(connexPoints)):
        shapes.append(Shape(PointSet(connexPoints[i]), mats[i]))

    Viewer.display(Scene(shapes))