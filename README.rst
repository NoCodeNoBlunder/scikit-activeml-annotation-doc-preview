
.. intro_start

==========================================================================
scikit activeml annotation
==========================================================================

An easy to setup Data Annotation Tool based on Active Machine Learning
==========================================================================
|Doc| |PythonVersion| |Black|

.. |Doc| image:: https://img.shields.io/badge/docs-latest-green
   :target: https://scikit-activeml.github.io/latest/

.. |PythonVersion| image:: https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C3.13-blue.svg
   :target: https://pypi.org/project/scikit-activeml/

.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black


Machine learning models require a large amount of labeled data to achieve
high performance. For this reason humans still often need to annotate data
in a time consuming fashion. Active Machine Learning can help by dramatically
reducing the amount of data which requires human processing by only querying
the annotator to label the most informative samples. With this approach, only
a small percentage of the data has to be manually annotated without
compromising performance.

Given these advantages it makes sense to integrate Active Learning into
annotation workflows. However, while a handful of Data Annotation Tools
exist, they are often proprietary, difficult to setup, or only implement
Active Learning as an afterthought.
To ease these issues, **scikit activeml annotation** was
designed from the ground up to leverage Active Learning by building on top of
`scikit activeml <https://scikit-activeml.github.io/scikit-activeml/>`_,
which provides first class active learning support, including cutting edge
query strategies. **scikit activeml annotation** is written in python
to make it accessible to the machine learning community.

.. intro_end

.. overview_start

.. figure:: _static/images/annot_audio.png
   :alt: Audio annotation UI
   :target: _static/images/annot_audio.png

   Overview of the user interface for audio data annotation.

.. overview_end


.. installation_start

Installation
-------------
Clone the repository:

.. code-block:: bash

   git clone https://github.com/scikit-activeml/scikit-activeml-annotation
   cd yourrepo

Install the dependencies:

.. code-block:: bash

   pip install -r requirements.txt

.. installation_end


.. usage_start


Getting Started
----------------
scikit activeml annotation expects a configured annotation pipeline.
This section covers how to use one of the preconfigured options to get started quickly.
For custom setup see the Tutorial.

TODO

.. note::

   This demo requires additional dependencies including a CUDA-capable GPU.
   Install PyTorch with CUDA support following the `PyTorch installation guide <https://pytorch.org/get-started>`_,
   then install the remaining demo dependencies:

   .. code-block:: bash

      pip install -r requirements_demo.txt

.. The tool generally assumes the user will setup their own annotation pipeline.
.. However, to enable quicker start preconfigured options exist.
.. To see how to the preconfigured options continue reading here.
.. To see how to configure your own pipeline, take a look at the tutorial.
..
.. To get started quicker and enable testing of the tool preconfigured options exist.
.. To see how to configure your own options refer to the tutorial.
..
.. The tool generally assumes the user will setup their own active learning annotation
.. pipeline. Including the dataset that should be annotated, how the data should be embedded,
.. which query strategies and machine learning models should be available
.. for the annotator to use.
..
.. To get up to speed some preconfigured options are available that can be used to

.. usage_end
