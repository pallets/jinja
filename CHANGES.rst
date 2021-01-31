.. currentmodule:: jinja2

Version 2.11.3
--------------

Released 2021-01-31

-   Improve the speed of the ``urlize`` filter by reducing regex
    backtracking. Email matching requires a word character at the start
    of the domain part, and only word characters in the TLD. :pr:`1343`


Version 2.11.2
--------------

Released 2020-04-13

-   Fix a bug that caused callable objects with ``__getattr__``, like
    :class:`~unittest.mock.Mock` to be treated as a
    :func:`contextfunction`. :issue:`1145`
-   Update ``wordcount`` filter to trigger :class:`Undefined` methods
    by wrapping the input in :func:`soft_unicode`. :pr:`1160`
-   Fix a hang when displaying tracebacks on Python 32-bit.
    :issue:`1162`
-   Showing an undefined error for an object that raises
    ``AttributeError`` on access doesn't cause a recursion error.
    :issue:`1177`
-   Revert changes to :class:`~loaders.PackageLoader` from 2.10 which
    removed the dependency on setuptools and pkg_resources, and added
    limited support for namespace packages. The changes caused issues
    when using Pytest. Due to the difficulty in supporting Python 2 and
    :pep:`451` simultaneously, the changes are reverted until 3.0.
    :pr:`1182`
-   Fix line numbers in error messages when newlines are stripped.
    :pr:`1178`
-   The special ``namespace()`` assignment object in templates works in
    async environments. :issue:`1180`
-   Fix whitespace being removed before tags in the middle of lines when
    ``lstrip_blocks`` is enabled. :issue:`1138`
-   :class:`~nativetypes.NativeEnvironment` doesn't evaluate
    intermediate strings during rendering. This prevents early
    evaluation which could change the value of an expression.
    :issue:`1186`


Version 2.11.1
--------------

Released 2020-01-30

-   Fix a bug that prevented looking up a key after an attribute
    (``{{ data.items[1:] }}``) in an async template. :issue:`1141`


Version 2.11.0
--------------

Released 2020-01-27

-   Drop support for Python 2.6, 3.3, and 3.4. This will be the last
    version to support Python 2.7 and 3.5.
-   Added a new ``ChainableUndefined`` class to support getitem and
    getattr on an undefined object. :issue:`977`
-   Allow ``{%+`` syntax (with NOP behavior) when ``lstrip_blocks`` is
    disabled. :issue:`748`
-   Added a ``default`` parameter for the ``map`` filter. :issue:`557`
-   Exclude environment globals from
    :func:`meta.find_undeclared_variables`. :issue:`931`
-   Float literals can be written with scientific notation, like
    2.56e-3. :issue:`912`, :pr:`922`
-   Int and float literals can be written with the '_' separator for
    legibility, like 12_345. :pr:`923`
-   Fix a bug causing deadlocks in ``LRUCache.setdefault``. :pr:`1000`
-   The ``trim`` filter takes an optional string of characters to trim.
    :pr:`828`
-   A new ``jinja2.ext.debug`` extension adds a ``{% debug %}`` tag to
    quickly dump the current context and available filters and tests.
    :issue:`174`, :pr:`798, 983`
-   Lexing templates with large amounts of whitespace is much faster.
    :issue:`857`, :pr:`858`
-   Parentheses around comparisons are preserved, so
    ``{{ 2 * (3 < 5) }}`` outputs "2" instead of "False".
    :issue:`755`, :pr:`938`
-   Add new ``boolean``, ``false``, ``true``, ``integer`` and ``float``
    tests. :pr:`824`
-   The environment's ``finalize`` function is only applied to the
    output of expressions (constant or not), not static template data.
    :issue:`63`
-   When providing multiple paths to ``FileSystemLoader``, a template
    can have the same name as a directory. :issue:`821`
-   Always return :class:`Undefined` when omitting the ``else`` clause
    in a ``{{ 'foo' if bar }}`` expression, regardless of the
    environment's ``undefined`` class. Omitting the ``else`` clause is a
    valid shortcut and should not raise an error when using
    :class:`StrictUndefined`. :issue:`710`, :pr:`1079`
-   Fix behavior of ``loop`` control variables such as ``length`` and
    ``revindex0`` when looping over a generator. :issue:`459, 751, 794`,
    :pr:`993`
-   Async support is only loaded the first time an environment enables
    it, in order to avoid a slow initial import. :issue:`765`
-   In async environments, the ``|map`` filter will await the filter
    call if needed. :pr:`913`
-   In for loops that access ``loop`` attributes, the iterator is not
    advanced ahead of the current iteration unless ``length``,
    ``revindex``, ``nextitem``, or ``last`` are accessed. This makes it
    less likely to break ``groupby`` results. :issue:`555`, :pr:`1101`
-   In async environments, the ``loop`` attributes ``length`` and
    ``revindex`` work for async iterators. :pr:`1101`
-   In async environments, values from attribute/property access will
    be awaited if needed. :pr:`1101`
-   :class:`~loader.PackageLoader` doesn't depend on setuptools or
    pkg_resources. :issue:`970`
-   ``PackageLoader`` has limited support for :pep:`420` namespace
    packages. :issue:`1097`
-   Support :class:`os.PathLike` objects in
    :class:`~loader.FileSystemLoader` and :class:`~loader.ModuleLoader`.
    :issue:`870`
-   :class:`~nativetypes.NativeTemplate` correctly handles quotes
    between expressions. ``"'{{ a }}', '{{ b }}'"`` renders as the tuple
    ``('1', '2')`` rather than the string ``'1, 2'``. :issue:`1020`
-   Creating a :class:`~nativetypes.NativeTemplate` directly creates a
    :class:`~nativetypes.NativeEnvironment` instead of a default
    :class:`Environment`. :issue:`1091`
-   After calling ``LRUCache.copy()``, the copy's queue methods point to
    the correct queue. :issue:`843`
-   Compiling templates always writes UTF-8 instead of defaulting to the
    system encoding. :issue:`889`
-   ``|wordwrap`` filter treats existing newlines as separate paragraphs
    to be wrapped individually, rather than creating short intermediate
    lines. :issue:`175`
-   Add ``break_on_hyphens`` parameter to ``|wordwrap`` filter.
    :issue:`550`
-   Cython compiled functions decorated as context functions will be
    passed the context. :pr:`1108`
-   When chained comparisons of constants are evaluated at compile time,
    the result follows Python's behavior of returning ``False`` if any
    comparison returns ``False``, rather than only the last one.
    :issue:`1102`
-   Tracebacks for exceptions in templates show the correct line numbers
    and source for Python >= 3.7. :issue:`1104`
-   Tracebacks for template syntax errors in Python 3 no longer show
    internal compiler frames. :issue:`763`
-   Add a ``DerivedContextReference`` node that can be used by
    extensions to get the current context and local variables such as
    ``loop``. :issue:`860`
-   Constant folding during compilation is applied to some node types
    that were previously overlooked. :issue:`733`
-   ``TemplateSyntaxError.source`` is not empty when raised from an
    included template. :issue:`457`
-   Passing an ``Undefined`` value to ``get_template`` (such as through
    ``extends``, ``import``, or ``include``), raises an
    ``UndefinedError`` consistently. ``select_template`` will show the
    undefined message in the list of attempts rather than the empty
    string. :issue:`1037`
-   ``TemplateSyntaxError`` can be pickled. :pr:`1117`


Version 2.10.3
--------------

Released 2019-10-04

-   Fix a typo in Babel entry point in ``setup.py`` that was preventing
    installation.


Version 2.10.2
--------------

Released 2019-10-04

-   Fix Python 3.7 deprecation warnings.
-   Using ``range`` in the sandboxed environment uses ``xrange`` on
    Python 2 to avoid memory use. :issue:`933`
-   Use Python 3.7's better traceback support to avoid a core dump when
    using debug builds of Python 3.7. :issue:`1050`


Version 2.10.1
--------------

Released 2019-04-06

-   ``SandboxedEnvironment`` securely handles ``str.format_map`` in
    order to prevent code execution through untrusted format strings.
    The sandbox already handled ``str.format``.


Version 2.10
------------

Released 2017-11-08

-   Added a new extension node called ``OverlayScope`` which can be used
    to create an unoptimized scope that will look up all variables from
    a derived context.
-   Added an ``in`` test that works like the in operator. This can be
    used in combination with ``reject`` and ``select``.
-   Added ``previtem`` and ``nextitem`` to loop contexts, providing
    access to the previous/next item in the loop. If such an item does
    not exist, the value is undefined.
-   Added ``changed(*values)`` to loop contexts, providing an easy way
    of checking whether a value has changed since the last iteration (or
    rather since the last call of the method)
-   Added a ``namespace`` function that creates a special object which
    allows attribute assignment using the ``set`` tag. This can be used
    to carry data across scopes, e.g. from a loop body to code that
    comes after the loop.
-   Added a ``trimmed`` modifier to ``{% trans %}`` to strip linebreaks
    and surrounding whitespace. Also added a new policy to enable this
    for all ``trans`` blocks.
-   The ``random`` filter is no longer incorrectly constant folded and
    will produce a new random choice each time the template is rendered.
    :pr:`478`
-   Added a ``unique`` filter. :pr:`469`
-   Added ``min`` and ``max`` filters. :pr:`475`
-   Added tests for all comparison operators: ``eq``, ``ne``, ``lt``,
    ``le``, ``gt``, ``ge``. :pr:`665`
-   ``import`` statement cannot end with a trailing comma. :pr:`617`,
    :pr:`618`
-   ``indent`` filter will not indent blank lines by default. :pr:`685`
-   Add ``reverse`` argument for ``dictsort`` filter. :pr:`692`
-   Add a ``NativeEnvironment`` that renders templates to native Python
    types instead of strings. :pr:`708`
-   Added filter support to the block ``set`` tag. :pr:`489`
-   ``tojson`` filter marks output as safe to match documented behavior.
    :pr:`718`
-   Resolved a bug where getting debug locals for tracebacks could
    modify template context.
-   Fixed a bug where having many ``{% elif ... %}`` blocks resulted in
    a "too many levels of indentation" error. These blocks now compile
    to native ``elif ..:`` instead of ``else: if ..:`` :issue:`759`


Version 2.9.6
-------------

Released 2017-04-03

-   Fixed custom context behavior in fast resolve mode :issue:`675`


Version 2.9.5
-------------

Released 2017-01-28

-   Restored the original repr of the internal ``_GroupTuple`` because
    this caused issues with ansible and it was an unintended change.
    :issue:`654`
-   Added back support for custom contexts that override the old
    ``resolve`` method since it was hard for people to spot that this
    could cause a regression.
-   Correctly use the buffer for the else block of for loops. This
    caused invalid syntax errors to be caused on 2.x and completely
    wrong behavior on Python 3 :issue:`669`
-   Resolve an issue where the ``{% extends %}`` tag could not be used
    with async environments. :issue:`668`
-   Reduce memory footprint slightly by reducing our unicode database
    dump we use for identifier matching on Python 3 :issue:`666`
-   Fixed autoescaping not working for macros in async compilation mode.
    :issue:`671`


Version 2.9.4
-------------

Released 2017-01-10

-   Solved some warnings for string literals. :issue:`646`
-   Increment the bytecode cache version which was not done due to an
    oversight before.
-   Corrected bad code generation and scoping for filtered loops.
    :issue:`649`
-   Resolved an issue where top-level output silencing after known
    extend blocks could generate invalid code when blocks where
    contained in if statements. :issue:`651`
-   Made the ``truncate.leeway`` default configurable to improve
    compatibility with older templates.


Version 2.9.3
-------------

Released 2017-01-08

-   Restored the use of blocks in macros to the extend that was possible
    before. On Python 3 it would render a generator repr instead of the
    block contents. :issue:`645`
-   Set a consistent behavior for assigning of variables in inner scopes
    when the variable is also read from an outer scope. This now sets
    the intended behavior in all situations however it does not restore
    the old behavior where limited assignments to outer scopes was
    possible. For more information and a discussion see :issue:`641`
-   Resolved an issue where ``block scoped`` would not take advantage of
    the new scoping rules. In some more exotic cases a variable
    overriden in a local scope would not make it into a block.
-   Change the code generation of the ``with`` statement to be in line
    with the new scoping rules. This resolves some unlikely bugs in edge
    cases. This also introduces a new internal ``With`` node that can be
    used by extensions.


Version 2.9.2
-------------

Released 2017-01-08

-   Fixed a regression that caused for loops to not be able to use the
    same variable for the target as well as source iterator.
    :issue:`640`
-   Add support for a previously unknown behavior of macros. It used to
    be possible in some circumstances to explicitly provide a caller
    argument to macros. While badly buggy and unintended it turns out
    that this is a common case that gets copy pasted around. To not
    completely break backwards compatibility with the most common cases
    it's now possible to provide an explicit keyword argument for caller
    if it's given an explicit default. :issue:`642`


Version 2.9.1
-------------

Released 2017-01-07

-   Resolved a regression with call block scoping for macros. Nested
    caller blocks that used the same identifiers as outer macros could
    refer to the wrong variable incorrectly.


Version 2.9
-----------

Released 2017-01-07, codename Derivation

-   Change cache key definition in environment. This fixes a performance
    regression introduced in 2.8.
-   Added support for ``generator_stop`` on supported Python versions
    (Python 3.5 and later)
-   Corrected a long standing issue with operator precedence of math
    operations not being what was expected.
-   Added support for Python 3.6 async iterators through a new async
    mode.
-   Added policies for filter defaults and similar things.
-   Urlize now sets "rel noopener" by default.
-   Support attribute fallback for old-style classes in 2.x.
-   Support toplevel set statements in extend situations.
-   Restored behavior of Cycler for Python 3 users.
-   Subtraction now follows the same behavior as other operators on
    undefined values.
-   ``map`` and friends will now give better error messages if you
    forgot to quote the parameter.
-   Depend on MarkupSafe 0.23 or higher.
-   Improved the ``truncate`` filter to support better truncation in
    case the string is barely truncated at all.
-   Change the logic for macro autoescaping to be based on the runtime
    autoescaping information at call time instead of macro define time.
-   Ported a modified version of the ``tojson`` filter from Flask to
    Jinja and hooked it up with the new policy framework.
-   Block sets are now marked ``safe`` by default.
-   On Python 2 the asciification of ASCII strings can now be disabled
    with the ``compiler.ascii_str`` policy.
-   Tests now no longer accept an arbitrary expression as first argument
    but a restricted one. This means that you can now properly use
    multiple tests in one expression without extra parentheses. In
    particular you can now write ``foo is divisibleby 2 or foo is
    divisibleby 3`` as you would expect.
-   Greatly changed the scoping system to be more consistent with what
    template designers and developers expect. There is now no more magic
    difference between the different include and import constructs.
    Context is now always propagated the same way. The only remaining
    differences is the defaults for ``with context`` and ``without
    context``.
-   The ``with`` and ``autoescape`` tags are now built-in.
-   Added the new ``select_autoescape`` function which helps configuring
    better autoescaping easier.
-   Fixed a runtime error in the sandbox when attributes of async
    generators were accessed.


Version 2.8.1
-------------

Released 2016-12-29

-   Fixed the ``for_qs`` flag for ``urlencode``.
-   Fixed regression when applying ``int`` to non-string values.
-   SECURITY: if the sandbox mode is used format expressions are now
    sandboxed with the same rules as in Jinja. This solves various
    information leakage problems that can occur with format strings.


Version 2.8
-----------

Released 2015-07-26, codename Replacement

-   Added ``target`` parameter to urlize function.
-   Added support for ``followsymlinks`` to the file system loader.
-   The truncate filter now counts the length.
-   Added equalto filter that helps with select filters.
-   Changed cache keys to use absolute file names if available instead
    of load names.
-   Fixed loop length calculation for some iterators.
-   Changed how Jinja enforces strings to be native strings in Python 2
    to work when people break their default encoding.
-   Added ``make_logging_undefined`` which returns an undefined
    object that logs failures into a logger.
-   If unmarshalling of cached data fails the template will be reloaded
    now.
-   Implemented a block ``set`` tag.
-   Default cache size was increased to 400 from a low 50.
-   Fixed ``is number`` test to accept long integers in all Python
    versions.
-   Changed ``is number`` to accept Decimal as a number.
-   Added a check for default arguments followed by non-default
    arguments. This change makes ``{% macro m(x, y=1, z) %}`` a syntax
    error. The previous behavior for this code was broken anyway
    (resulting in the default value being applied to ``y``).
-   Add ability to use custom subclasses of
    ``jinja2.compiler.CodeGenerator`` and ``jinja2.runtime.Context`` by
    adding two new attributes to the environment
    (``code_generator_class`` and ``context_class``). :pr:`404`
-   Added support for context/environment/evalctx decorator functions on
    the finalize callback of the environment.
-   Escape query strings for urlencode properly. Previously slashes were
    not escaped in that place.
-   Add 'base' parameter to 'int' filter.


Version 2.7.3
-------------

Released 2014-06-06

-   Security issue: Corrected the security fix for the cache folder.
    This fix was provided by RedHat.


Version 2.7.2
-------------

Released 2014-01-10

-   Prefix loader was not forwarding the locals properly to inner
    loaders. This is now fixed.
-   Security issue: Changed the default folder for the filesystem cache
    to be user specific and read and write protected on UNIX systems.
    See `Debian bug 734747`_ for more information.

.. _Debian bug 734747: https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=734747


Version 2.7.1
-------------

Released 2013-08-07

-   Fixed a bug with ``call_filter`` not working properly on environment
    and context filters.
-   Fixed lack of Python 3 support for bytecode caches.
-   Reverted support for defining blocks in included templates as this
    broke existing templates for users.
-   Fixed some warnings with hashing of undefineds and nodes if Python
    is run with warnings for Python 3.
-   Added support for properly hashing undefined objects.
-   Fixed a bug with the title filter not working on already uppercase
    strings.


Version 2.7
-----------

Released 2013-05-20, codename Translation

-   Choice and prefix loaders now dispatch source and template lookup
    separately in order to work in combination with module loaders as
    advertised.
-   Fixed filesizeformat.
-   Added a non-silent option for babel extraction.
-   Added ``urlencode`` filter that automatically quotes values for URL
    safe usage with utf-8 as only supported encoding. If applications
    want to change this encoding they can override the filter.
-   Added ``keep-trailing-newline`` configuration to environments and
    templates to optionally preserve the final trailing newline.
-   Accessing ``last`` on the loop context no longer causes the iterator
    to be consumed into a list.
-   Python requirement changed: 2.6, 2.7 or >= 3.3 are required now,
    supported by same source code, using the "six" compatibility
    library.
-   Allow ``contextfunction`` and other decorators to be applied to
    ``__call__``.
-   Added support for changing from newline to different signs in the
    ``wordwrap`` filter.
-   Added support for ignoring memcache errors silently.
-   Added support for keeping the trailing newline in templates.
-   Added finer grained support for stripping whitespace on the left
    side of blocks.
-   Added ``map``, ``select``, ``reject``, ``selectattr`` and
    ``rejectattr`` filters.
-   Added support for ``loop.depth`` to figure out how deep inside a
    recursive loop the code is.
-   Disabled py_compile for pypy and python 3.


Version 2.6
-----------

Released 2011-07-24, codename Convolution

-   Internal attributes now raise an internal attribute error now
    instead of returning an undefined. This fixes problems when passing
    undefined objects to Python semantics expecting APIs.
-   Traceback support now works properly for PyPy. (Tested with 1.4)
-   Implemented operator intercepting for sandboxed environments. This
    allows application developers to disable builtin operators for
    better security. (For instance limit the mathematical operators to
    actual integers instead of longs)
-   Groupby filter now supports dotted notation for grouping by
    attributes of attributes.
-   Scoped blocks now properly treat toplevel assignments and imports.
    Previously an import suddenly "disappeared" in a scoped block.
-   Automatically detect newer Python interpreter versions before
    loading code from bytecode caches to prevent segfaults on invalid
    opcodes. The segfault in earlier Jinja versions here was not a
    Jinja bug but a limitation in the underlying Python interpreter. If
    you notice Jinja segfaulting in earlier versions after an upgrade
    of the Python interpreter you don't have to upgrade, it's enough to
    flush the bytecode cache. This just no longer makes this necessary,
    Jinja will automatically detect these cases now.
-   The sum filter can now sum up values by attribute. This is a
    backwards incompatible change. The argument to the filter previously
    was the optional starting index which defaults to zero. This now
    became the second argument to the function because it's rarely used.
-   Like sum, sort now also makes it possible to order items by
    attribute.
-   Like sum and sort, join now also is able to join attributes of
    objects as string.
-   The internal eval context now has a reference to the environment.
-   Added a mapping test to see if an object is a dict or an object with
    a similar interface.


Version 2.5.5
-------------

Released 2010-10-18

-   Built documentation is no longer part of release.


Version 2.5.4
-------------

Released 2010-10-17

-   Fixed extensions not loading properly with overlays.
-   Work around a bug in cpython for the debugger that causes segfaults
    on 64bit big-endian architectures.


Version 2.5.3
-------------

Released 2010-10-17

-   Fixed an operator precedence error introduced in 2.5.2. Statements
    like "-foo.bar" had their implicit parentheses applied around the
    first part of the expression ("(-foo).bar") instead of the more
    correct "-(foo.bar)".


Version 2.5.2
-------------

Released 2010-08-18

-   Improved setup.py script to better work with assumptions people
    might still have from it (``--with-speedups``).
-   Fixed a packaging error that excluded the new debug support.


Version 2.5.1
-------------

Released 2010-08-17

-   StopIteration exceptions raised by functions called from templates
    are now intercepted and converted to undefineds. This solves a lot
    of debugging grief. (StopIteration is used internally to abort
    template execution)
-   Improved performance of macro calls slightly.
-   Babel extraction can now properly extract newstyle gettext calls.
-   Using the variable ``num`` in newstyle gettext for something else
    than the pluralize count will no longer raise a :exc:`KeyError`.
-   Removed builtin markup class and switched to markupsafe. For
    backwards compatibility the pure Python implementation still exists
    but is pulled from markupsafe by the Jinja developers. The debug
    support went into a separate feature called "debugsupport" and is
    disabled by default because it is only relevant for Python 2.4
-   Fixed an issue with unary operators having the wrong precedence.


Version 2.5
-----------

Released 2010-05-29, codename Incoherence

-   Improved the sort filter (should have worked like this for a long
    time) by adding support for case insensitive searches.
-   Fixed a bug for getattribute constant folding.
-   Support for newstyle gettext translations which result in a nicer
    in-template user interface and more consistent catalogs.
-   It's now possible to register extensions after an environment was
    created.


Version 2.4.1
-------------

Released 2010-04-20

-   Fixed an error reporting bug for undefined.


Version 2.4
-----------

Released 2010-04-13, codename Correlation

-   The environment template loading functions now transparently pass
    through a template object if it was passed to it. This makes it
    possible to import or extend from a template object that was passed
    to the template.
-   Added a ``ModuleLoader`` that can load templates from
    precompiled sources. The environment now features a method to
    compile the templates from a configured loader into a zip file or
    folder.
-   The _speedups C extension now supports Python 3.
-   Added support for autoescaping toggling sections and support for
    evaluation contexts.
-   Extensions have a priority now.


Version 2.3.1
-------------

Released 2010-02-19

-   Fixed an error reporting bug on all python versions
-   Fixed an error reporting bug on Python 2.4


Version 2.3
-----------

Released 2010-02-10, codename 3000 Pythons

-   Fixes issue with code generator that causes unbound variables to be
    generated if set was used in if-blocks and other small identifier
    problems.
-   Include tags are now able to select between multiple templates and
    take the first that exists, if a list of templates is given.
-   Fixed a problem with having call blocks in outer scopes that have an
    argument that is also used as local variable in an inner frame
    :issue:`360`.
-   Greatly improved error message reporting :pr:`339`
-   Implicit tuple expressions can no longer be totally empty. This
    change makes ``{% if %}`` a syntax error now. :issue:`364`
-   Added support for translator comments if extracted via babel.
-   Added with-statement extension.
-   Experimental Python 3 support.


Version 2.2.1
-------------

Released 2009-09-14

-   Fixes some smaller problems for Jinja on Jython.


Version 2.2
-----------

Released 2009-09-13, codename Kong

-   Include statements can now be marked with ``ignore missing`` to skip
    non existing templates.
-   Priority of ``not`` raised. It's now possible to write ``not foo in
    bar`` as an alias to ``foo not in bar`` like in python. Previously
    the grammar required parentheses (``not (foo in bar)``) which was
    odd.
-   Fixed a bug that caused syntax errors when defining macros or using
    the ``{% call %}`` tag inside loops.
-   Fixed a bug in the parser that made ``{{ foo[1, 2] }}`` impossible.
-   Made it possible to refer to names from outer scopes in included
    templates that were unused in the callers frame :issue:`327`
-   Fixed a bug that caused internal errors if names where used as
    iteration variable and regular variable *after* the loop if that
    variable was unused *before* the loop. :pr:`331`
-   Added support for optional ``scoped`` modifier to blocks.
-   Added support for line-comments.
-   Added the ``meta`` module.
-   Renamed (undocumented) attribute "overlay" to "overlayed" on the
    environment because it was clashing with a method of the same name.
-   Speedup extension is now disabled by default.


Version 2.1.1
-------------

Released 2008-12-25

-   Fixed a translation error caused by looping over empty recursive
    loops.


Version 2.1
-----------

Released 2008-11-23, codename Yasuzō

-   Fixed a bug with nested loops and the special loop variable. Before
    the change an inner loop overwrote the loop variable from the outer
    one after iteration.
-   Fixed a bug with the i18n extension that caused the explicit
    pluralization block to look up the wrong variable.
-   Fixed a limitation in the lexer that made ``{{ foo.0.0 }}``
    impossible.
-   Index based subscribing of variables with a constant value returns
    an undefined object now instead of raising an index error. This was
    a bug caused by eager optimizing.
-   The i18n extension looks up ``foo.ugettext`` now followed by
    ``foo.gettext`` if an translations object is installed. This makes
    dealing with custom translations classes easier.
-   Fixed a confusing behavior with conditional extending. loops were
    partially executed under some conditions even though they were not
    part of a visible area.
-   Added ``sort`` filter that works like ``dictsort`` but for arbitrary
    sequences.
-   Fixed a bug with empty statements in macros.
-   Implemented a bytecode cache system.
-   The template context is now weakref-able
-   Inclusions and imports "with context" forward all variables now, not
    only the initial context.
-   Added a cycle helper called ``cycler``.
-   Added a joining helper called ``joiner``.
-   Added a ``compile_expression`` method to the environment that allows
    compiling of Jinja expressions into callable Python objects.
-   Fixed an escaping bug in urlize


Version 2.0
-----------

Released 2008-07-17, codename Jinjavitus

-   The subscribing of objects (looking up attributes and items) changed
    from slightly. It's now possible to give attributes or items a
    higher priority by either using dot-notation lookup or the bracket
    syntax. This also changed the AST slightly. ``Subscript`` is gone
    and was replaced with ``Getitem`` and ``Getattr``.
-   Added support for preprocessing and token stream filtering for
    extensions. This would allow extensions to allow simplified gettext
    calls in template data and something similar.
-   Added ``TemplateStream.dump``.
-   Added missing support for implicit string literal concatenation.
    ``{{ "foo" "bar" }}`` is equivalent to ``{{ "foobar" }}``
-   ``else`` is optional for conditional expressions. If not given it
    evaluates to ``false``.
-   Improved error reporting for undefined values by providing a
    position.
-   ``filesizeformat`` filter uses decimal prefixes now per default and
    can be set to binary mode with the second parameter.
-   Fixed bug in finalizer


Version 2.0rc1
--------------

Released 2008-06-09

-   First release of Jinja 2.
