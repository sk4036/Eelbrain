************
Introduction
************

.. currentmodule:: eelbrain


There are three primary data-objects:

* :class:`Factor` for categorial variables
* :class:`Var` for scalar variables
* :class:`NDVar` for multidimensional data (e.g. a variable measured at
  different time points)

Multiple variables belonging to the same dataset can be grouped in a 
:class:`Dataset` object.


Factor
======

A :class:`Factor` is a container for one-dimensional, categorial data: Each 
case is described by a string label. The most obvious way to initialize a 
:class:`Factor` is a list of strings::

    >>> A = Factor(['a', 'a', 'a', 'a', 'b', 'b', 'b', 'b'], name='A')

Since Factor initialization simply iterates over the given data, the 
same Factor can be initialized with::

    >>> Factor('aaaabbbb', name='A')
    Factor(['a', 'a', 'a', 'a', 'b', 'b', 'b', 'b'], name='A')
 
There are other shortcuts to initialize factors  (see also 
the :class:`Factor` class documentation)::

    >>> A = Factor(['a', 'b', 'c'], repeat=4, name='A')
    >>> A
    Factor(['a', 'a', 'a', 'a', 'b', 'b', 'b', 'b', 'c', 'c', 'c', 'c'], name='A')

Indexing works like for arrays::

    >>> A[0]
    'a'
    >>> A[0:6]
    Factor(['a', 'a', 'a', 'a', 'b', 'b'], name='A')

All values present in a Factor are accessible in its 
:attr:`Factor.cells` attribute::

    >>> A.cells
    ('a', 'b', 'c')

Based on the Factor's cell values, boolean indexes can be generated::

    >>> A == 'a'
    array([ True,  True,  True,  True, False, False, False, False, False,
           False, False, False], dtype=bool)
    >>> A.isany('a', 'b')
    array([ True,  True,  True,  True,  True,  True,  True,  True, False,
           False, False, False], dtype=bool)
    >>> A.isnot('a', 'b')
    array([False, False, False, False, False, False, False, False,  True,
            True,  True,  True], dtype=bool)

Interaction effects can be constructed from multiple factors with the ``%``
operator::

    >>> B = Factor(['d', 'e'], repeat=2, tile=3, name='B')
    >>> B
    Factor(['d', 'd', 'e', 'e', 'd', 'd', 'e', 'e', 'd', 'd', 'e', 'e'], name='B')
    >>> i = A % B

Interaction effects are in many ways interchangeable with factors in places 
where a categorial model is required::
 
    >>> i.cells
    (('a', 'd'), ('a', 'e'), ('b', 'd'), ('b', 'e'), ('c', 'd'), ('c', 'e'))
    >>> i == ('a', 'd')
    array([ True,  True, False, False, False, False, False, False, False,
           False, False, False], dtype=bool)


Var
===

The :class:`Var` class is basically a container to associate one-dimensional
:py:class:`numpy.ndarray` objects with a name. While simple operations can be
performed on the object directly, for any more complex operations on the data
the corresponding :py:class:`numpy.ndarray` can be retrieved in the 
:attr:`Var.x` attribute::

    >>> Y = Var(np.random.rand(10), name='Y')
    >>> Y
    Var([0.185, 0.285, 0.105, 0.916, 0.76, 0.888, 0.288, 0.0165, 0.901, 0.72], name='Y')
    >>> Y[5:]
    Var([0.888, 0.288, 0.0165, 0.901, 0.72], name='Y')
    >>> Y + 1
    Var([1.18, 1.28, 1.11, 1.92, 1.76, 1.89, 1.29, 1.02, 1.9, 1.72], name='Y+1')
    >>> Y.x
    array([ 0.18454728,  0.28479396,  0.10546204,  0.91619036,  0.76006963,
            0.88807645,  0.28807859,  0.01645504,  0.90112081,  0.71991843])

.. Note::
    Note however that the :attr:`Var.x` attribute is not intended to be 
    replaced; rather, a new :class:`Var` object should be created for a new 
    array.


NDVar
=====

:class:`NDVar` objects are containers for multidimensional data, and manage the
description of the dimensions along with the data. :class:`NDVars` are often
derived from some import function, for example :func:`load.fiff.stc_ndvar`.
As an example, consider single trial data from the :mod:`mne` sample dataset::

    >>> ds = datasets.get_mne_sample(src='ico')
    >>> src = ds['src']
    >>> src
    <NDVar 'src': 145 case, 5120 source, 76 time>

This representation shows that ``src`` contains 145 trials of data, with
5120 sources and 76 time points. :class:`NDVars` offer :mod:`numpy`
functionality that takes into account the dimensions. Through the
:meth:`NDVar.sub` method, indexing can be done using meaningful descriptions,
such as selecting data for only the left hemisphere::

    >>> src.sub(source='lh')
    <NDVar 'src': 145 case, 2559 source, 76 time>

Through several methods data can be aggregated, for example a mean over time::

    >>> src.mean('time')
    <NDVar 'src': 145 case, 5120 source>

Or a root mean square over sources::

    >>> src.rms('source')
    <NDVar 'src': 145 case, 76 time>

As with a :class:`Var`, the corresponding :class:`numpy.ndarray` can always be
accessed in the :attr:`NDVar.x` attribute::

    >>> type(src.x)
    numpy.ndarray
    >>> src.x.shape
    (145, 5120, 76)

:class:`NDVar` objects can be constructed from an array and corresponding
dimension objects, for example::

    >>> frequency = Scalar('frequency', [1, 2, 3, 4])
    >>> time = UTS(0, 0.01, 50)
    >>> data = numpy.random.normal(0, 1, (4, 50))
    >>> NDVar(data, (frequency, time))
    <NDVar: 4 frequency, 50 time>

A case dimension can be added by including the bare :class:`Case` class::

    >>> data = numpy.random.normal(0, 1, (10, 4, 50))
    >>> NDVar(data, (Case, frequency, time))
    <NDVar: 10 case, 4 frequency, 50 time>


Dataset
=======

The :class:`Dataset` class is a subclass of :py:class:`collections.OrderedDict` 
from which it inherits much of its behavior.
Its intended purpose is to be a vessel for variable objects (:class:`Factor`,
:class:`Var` and :class:`NDVar`) describing the same cases.
As a dictionary, its keys are strings and its values are data-objects.

The :class:`Dataset` class interacts with data-objects' :attr:`.name`
attribute:

* A :class:`Dataset` initialized with a list of data-objects automatically uses
  their names as keys::

        >>> A = Factor('aabb', name='A')
        >>> B = Factor('cdcd', name='B')
        >>> ds = Dataset((A, B))
        >>> print ds
        A   B
        -----
        a   c
        a   d
        b   c
        b   d
        >>> ds['A']
        Factor(['a', 'a', 'b', 'b'], name='A')

* When an unnamed data-object is assigned to a :class:`Dataset`, the
  data-object is automatically assigned its key as a name::
        
        >>> ds['Y'] = Var([2,1,4,2])
        >>> print ds
        A   B   Y
        ---------
        a   c   2
        a   d   1
        b   c   4
        b   d   2
        >>> ds['Y']
        Var([2, 1, 4, 2], name='Y')

The "official" string representation of a :class:`Dataset` contains information
on the variables stored in it::

    >>> ds
    <Dataset n_cases=4 {'A':F, 'B':F, 'Y':V}>

``n_cases=4`` indicates that the Dataset contains four cases (rows). The 
subsequent dictionary-like representation shows the keys and the types of the 
corresponding values (``F``:   :class:`Factor`, ``V``:   :class:`Var`,
``Vnd``: :class:`NDVar`).
If a variable's name does not match its key in the Dataset, this is also 
indicated::

    >>> ds['C'] = Factor('qwer', name='another_name')
    >>> ds
    <Dataset n_cases=4 {'A':F, 'B':F, 'Y':V, 'C':<F 'another_name'>}>

While indexing a Dataset with strings returns the corresponding data-objects,
:class:`numpy.ndarray`-like indexing on the Dataset can be used to access a
subset of cases::

    >>> ds2 = ds[2:]
    >>> print ds2
    A   B   Y   C
    -------------
    b   c   4   e
    b   d   2   r
    >>> ds2['A']
    Factor(['b', 'b'], name='A')

Together with the "informal" string representation (retrieved
by the ``print`` statement) this can be used to inspect the cases contained in
the Dataset::

    >>> print ds[0]
    A   B   Y   C
    -------------
    a   c   2   q
    >>> print ds[2:]
    A   B   Y   C
    -------------
    b   c   4   e
    b   d   2   r

This type of indexing also allows indexing based on the Dataset's variables::

    >>> print ds[A == 'a']
    A   B   Y   C
    -------------
    a   c   2   q
    a   d   1   w 


.. _statistics-example:

Example
=======

Below is a simple example using data objects (for more, see the
`statistics examples 
<https://github.com/christianbrodbeck/Eelbrain/tree/master/examples>`_)::

    >>> from eelbrain import *
    >>> import numpy as np
    >>> y = np.empty(21)
    >>> y[:14] = np.random.normal(0, 1, 14)
    >>> y[14:] = np.random.normal(1.5, 1, 7)
    >>> Y = Var(y, 'Y')
    >>> A = Factor('abc', 'A', repeat=7)
    >>> print Dataset((Y, A))
    Y           A
    -------------
    0.10967     a
    0.33562     a
    -0.33151    a
    1.3571      a
    -0.49722    a
    -0.24896    a
    1.0979      a
    -0.56123    b
    -0.51316    b
    -0.25942    b
    -0.6072     b
    -0.79173    b
    0.0019011   b
    2.1804      b
    2.5373      c
    1.7302      c
    -0.17581    c
    1.8922      c
    1.2734      c
    1.5961      c
    1.1518      c
    >>> print table.frequencies(A)
    cell   n
    --------
    a      7
    b      7
    c      7
    >>> print test.anova(Y, A)
                           SS   df               MS         F      p
    ----------------------------------------------------------------
    A                    8.76    2             4.38   5.75*     .012

    Residuals   13.7063612608   18   0.761464514489
    ----------------------------------------------------------------
    Total               22.47   20
    >>> print test.pairwise(Y, A, corr='Hochberg')

    Pairwise t-Tests (independent samples)

        b                  c
    ----------------------------------------
    a   t(12) = 0.71       t(12) = -2.79*
        p = .489           p = .016
        p(c) = .489        p(c) = .032
    b                      t(12) = -3.00*
                           p = .011
                           p(c) = .032
    (* Corrected after Hochberg, 1988)
    >>> t = test.pairwise(Y, A, corr='Hochberg')
    >>> print t.get_tex()
    \begin{center}
    \begin{tabular}{lll}
    \toprule
     & b & c \\
    \midrule
    a & $t_{12} = 0.71^{    \ \ \ \ }$ & $t_{12} = -2.79^{*   \ \ \ }$ \\
     & $p = .489$ & $p = .016$ \\
     & $p_{c} = .489$ & $p_{c} = .032$ \\
    b &  & $t_{12} = -3.00^{*   \ \ \ }$ \\
     &  & $p = .011$ \\
     &  & $p_{c} = .032$ \\
    \bottomrule
    \end{tabular}
    \end{center}
    >>> plot.Boxplot(Y, A, title="My Boxplot", ylabel="value", corr='Hochberg')


.. image:: images/statistics-example.png


Exporting Data
==============

:class:`Dataset` objects have different :meth:`Dataset.save` methods for
saving in various formats.
Iterators (such as :class:`Var` and :class:`Factor`) can be exported using the
:func:`save.txt` function.
