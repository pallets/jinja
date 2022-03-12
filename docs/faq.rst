Frequently Asked Questions
==========================


Why is it called Jinja?
-----------------------

"Jinja" is a Japanese `Shinto shrine`_, or temple, and temple and
template share a similar English pronunciation. It is not named after
the `city in Uganda`_.

.. _Shinto shrine: https://en.wikipedia.org/wiki/Shinto_shrine
.. _city in Uganda: https://en.wikipedia.org/wiki/Jinja%2C_Uganda


How fast is Jinja?
------------------

Jinja is relatively fast among template engines because it compiles and
caches template code to Python code, so that the template does not need
to be parsed and interpreted each time. Rendering a template becomes as
close to executing a Python function as possible.

Jinja also makes extensive use of caching. Templates are cached by name
after loading, so future uses of the template avoid loading. The
template loading itself uses a bytecode cache to avoid repeated
compiling. The caches can be external to persist across restarts.
Templates can also be precompiled and loaded as fast Python imports.

We dislike benchmarks because they don't reflect real use. Performance
depends on many factors. Different engines have different default
configurations and tradeoffs that make it unclear how to set up a useful
comparison. Often, database access, API calls, and data processing have
a much larger effect on performance than the template engine.


Isn't it a bad idea to put logic in templates?
----------------------------------------------

Without a doubt you should try to remove as much logic from templates as
possible. With less logic, the template is easier to understand, has
fewer potential side effects, and is faster to compile and render. But a
template without any logic means processing must be done in code before
rendering. A template engine that does that is shipped with Python,
called :class:`string.Template`, and while it's definitely fast it's not
convenient.

Jinja's features such as blocks, statements, filters, and function calls
make it much easier to write expressive templates, with very few
restrictions. Jinja doesn't allow arbitrary Python code in templates, or
every feature available in the Python language. This keeps the engine
easier to maintain, and keeps templates more readable.

Some amount of logic is required in templates to keep everyone happy.
Too much logic in the template can make it complex to reason about and
maintain. It's up to you to decide how your application will work and
balance how much logic you want to put in the template.


Why is HTML escaping not the default?
-------------------------------------

Jinja provides a feature that can be enabled to escape HTML syntax in
rendered templates. However, it is disabled by default.

Jinja is a general purpose template engine, it is not only used for HTML
documents. You can generate plain text, LaTeX, emails, CSS, JavaScript,
configuration files, etc. HTML escaping wouldn't make sense for any of
these document types.

While automatic escaping means that you are less likely have an XSS
problem, it also requires significant extra processing during compiling
and rendering, which can reduce performance. Jinja uses MarkupSafe for
escaping, which provides optimized C code for speed, but it still
introduces overhead to track escaping across methods and formatting.
