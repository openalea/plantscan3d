Install and run
################

This part explain how to install Plantscan3d.

.. _selection-doc-ref:

Anaconda
~~~~~~~~

OpenAlea is distributed through Anaconda. So first we have to install
it. All information for installation is available from the `Anaconda
documentation website <https://docs.anaconda.com/anaconda/install/>`__. Then, we
will use Anaconda navigator, a GUI for managing Anaconda environments.

Environment 
~~~~~~~~~~~~

Open Anaconda navigator. This can take a while (10
seconds to 1 minute). Then, go to “Environments”. Click on the
``Create`` button : |image-create| Name it ``openalea`` and create it. It
will create an isolated environment with an installation of python
(*e.g.* Python 3.7). We now have to import the different packages for
plantscan3d. The packages are bundled in two channels, the one from
conda-forge, and the one from Frédéric Boudon. Add a channel by
clicking on the channels button: |image-channels| Then, click on ``Add…``, and
add these two channels (just copy/paste it as is):  

* https://anaconda.org/fredboudon
* conda-forge

Click on update index: |image-update|

Then click on the ribbon named ``Installed``, and replace by
``Not Installed``. Search plantscan3d, check the box and click on apply
(twice). The package will be installed along with all its dependencies.

And that’s it !


Run
~~~~~~~~

To run Plantscan3D, open your openalea environment, and click on the
play button: |image-play2| which is located on the “environments” panel:

|image-play|

Choose “open a terminal”, and type the following command:

.. code:: shell

   plantscan3D



.. |image-create| image:: /images/installation/create.png
            :height: 15px
            :width: 50px

.. |image-channels| image:: /images/installation/channels.png

.. |image-update| image:: /images/installation/update.png

.. |image-play2| image:: /images/installation/play2.png

.. |image-play| image:: /images/installation/play.png

