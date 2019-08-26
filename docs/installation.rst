Installation
=================

Current Releases of mss is based on  *python 3*.

.. image:: https://anaconda.org/conda-forge/mss/badges/installer/conda.svg



mss-1.7.6 was the last version with python2* support.


Install distributed version by conda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Anaconda <https://www.continuum.io/why-anaconda>`_ provides an enterprise-ready data analytics
platform that empowers companies to adopt a modern open data science analytics architecture.

The Mission Support Web Map Service (mss) is available as anaconda package on the channel.

`conda-forge <https://anaconda.org/conda-forge/mss>`_

The conda-forge packages are based on defaults and other conda-forge packages.
This channel conda-forge has builds for osx-64, linux-64, win-64


The conda-forge `github organization <https://conda-forge.github.io/>`_ uses various automated continuos integration
build processes.


conda-forge channel
+++++++++++++++++++++

Please add the channel conda-forge to your defaults::

  $ conda config --add channels conda-forge
  $ conda config --add channels defaults

The last channel added gets on top of the list. This gives the order:
First search in default packages then in conda-forge.

You must install mss into a new environment to ensure the most recent
versions for dependencies (On the Anaconda Prompt on Windows, you have to 
leave out the 'source' here and below). ::

   $ conda create -n mssenv mss python=3
   $ conda activate mssenv
   $ mss

For updating an existing MSS installation to the current version, it is best to install
it into a new environment. If an existing environment shall be updated, it is important
to update all packages in this environment. ::

   $ conda activate mssenv
   $ conda update --all
   $ mss

For further details :ref:`mss-configuration`

Server based installation using miniconda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a wms server setup you may want to have a dedicated user running mswms or the apache2 wsgi script.
We suggest to create a mss user.

* create a mss user on your system
* login as mss user
* create a *src* directory in /home/mss
* cd src
* get `miniconda <http://conda.pydata.org/miniconda.html>`_ for Python 3
* set execute bit on install script
* execute script, enable environment in .bashrc
* login again or export PATH="/home/mss/miniconda3/bin:$PATH"
* python --version should tell Python 3.X.X
* conda install -c conda-forge mss

For a simple test you could start the builtin standalone server by *mswms*.
It should tell::

 serving on http://127.0.0.1:8081

Pointing a browser to
`<http://localhost:8081/?service=WMS&request=GetCapabilities&version=1.1.1>`_
shows the generated XML data the mss app will use.

If you want to look on some data, we provide a demo data set by the program :ref:`demodata`.

For further configuration see :ref:`apache-deployment` or :ref:`mswms-deployment`.


Installation based on Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since 1.7.4 mss is on the `docker hub <https://hub.docker.com/r/dreimark/mss/>`_.

Build settings are based on the stable branch. Our latest is any update in the stable repo.

You can start server and client by loading the image ::

 $ xhost +local:docker
 $ docker run -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix dreimark/mss:latest  /bin/bash
 $ mss &
 $ mswms


If you want both server and ciient interact ::

 $  xhost +local:docker
 $  docker run -d --net=host -ti --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix dreimark/mss:latest mss

 $ docker run -d --net=host  dreimark/mss:latest:latest
 $ curl "http://localhost/?service=WMS&request=GetCapabilities&version=1.1.1"

