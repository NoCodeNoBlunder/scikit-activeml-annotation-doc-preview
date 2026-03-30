.. _Admin Guide:

Admin Guide
============
This guide covers the annotation process from the administrator's perspective.
The admin is responsible for the initial setup and defining the available
configuration options of the active learning pipeline, including:

- which datasets are available for annotation
- how datasets are preprocessed and embedded
- which query strategies are used to select the most informative samples
- the machine learning models used for active learning

.. contents::
   :local:

Setup and Configuration
-----------------------

Adding a Dataset
~~~~~~~~~~~~~~~~~
A new dataset is made available for annotation by installing it to the
``datasets`` directory. It should contain raw human-interpretable files. The
tool assumes that each sample will be represented by exactly one file. For
example one ``.png`` file per visual sample or one ``.txt`` file per textual
sample. To view the supported formats for each modality see
:ref:`supported-formats`.

For the tool to pickup the newly added dataset, a ``.yaml`` configuration file
has to be added to ``config/dataset``, referencing that dataset.

.. literalinclude:: ../../config/dataset/cifar10.yaml
    :caption: Example of yaml config file for the CIRAR-10 dataset.
    :language: yaml


For a full description of all required keys see:
:class:`~skactiveml_annotation.hydra_schema.DatasetConfig`.

.. _supported-formats:

Supported Formats
^^^^^^^^^^^^^^^^^
The tool converts all files to a browser-compatible format at load time, so the
annotator always receives a renderable file regardless of the source format.

.. list-table::
   :header-rows: 1
   :widths: 15 55 30

   * - Modality
     - Supported Formats
     - Notes
   * - Image
     - All file formats supported by `Pillow <https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html>`_
     - Converted to PNG at load time.
   * - Audio
     - All file formats and codecs supported by `librosa <https://librosa.org/doc/latest/ioformats.html>`_
     - Converted to WAV at load time.
   * - Text
     - Raw text (``.txt``) and Markdown (``.md``)
     - Rendered via `dcc.Markdown <https://dash.plotly.com/dash-core-components/markdown>`_.

.. note::

   Audio format and codec support depends on the backends available to librosa
   (e.g. ``soundfile``, ``audioread``, ``ffmpeg``). See the
   `librosa IO documentation <https://librosa.org/doc/latest/ioformats.html>`_ for details.


Configuring an Embedding Method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Machine learning models rarely operate on raw data directly. Instead, samples
are typically preprocessed and embedded into a feature representation that
captures the semantic structure of the data.


Configuring an embedding method requires:

1. An ``EmbeddingAdapter`` implementing the interface defined by
   :class:`~skactiveml_annotation.embedding.base.EmbeddingBaseAdapter`.
   The preconfigured adapters in ``skactiveml_annotation/embedding/`` can be
   used as a reference.
2. A ``.yaml`` configuration file placed in ``config/embedding/``
   referencing the implemented adapter:

.. literalinclude:: ../../config/embedding/dinov2_vits14.yaml
   :language: yaml
   :caption: Example embedding configuration for DINOv2 ViT-S/14 visual embedding.

For a full description of all supported keys see
:class:`~skactiveml_annotation.hydra_schema.EmbeddingConfig`.


Available Query Strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All pool-based active learning strategies for classification provided by
`scikit-activeml <https://scikit-activeml.github.io/latest/generated/strategy_overview.html>`_
are supported. A query strategy is configured by placing a ``.yaml`` file
in ``config/query_strategy/``.

.. literalinclude:: ../../config/query_strategy/uncertainty_sampling.yaml
   :language: yaml
   :caption: Example query strategy configuration for Uncertainty Sampling.

For a full description of all supported keys see
:class:`~skactiveml_annotation.hydra_schema.QueryStrategyConfig`.


Possible Classifiers
~~~~~~~~~~~~~~~~~~~~~~
Any `scikit-learn-compatible <https://scikit-learn.org/stable/supervised_learning.html>`_
classifier can be configured as the machine learning model,
including deep learning models via
`skorch <https://skorch.readthedocs.io/en/stable/>`_. A model is configured
by placing a ``.yaml`` file in ``config/model/``.

.. literalinclude:: ../../config/model/logistic_regression.yaml
   :language: yaml
   :caption: Example model configuration for Logistic Regression.

.. note::

   Not all scikit-learn compatible classifiers implement ``predict_proba``.
   For classifiers that do not, the predicted class probabilities will not
   be available to the annotator during annotation.

For a full description of all supported keys see
:class:`~skactiveml_annotation.hydra_schema.ModelConfig`.

Output
-------
TODO:
