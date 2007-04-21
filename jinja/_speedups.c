/**
 * jinja._speedups
 * ~~~~~~~~~~~~~~~
 *
 * This module implements the BaseContext, a c implementation of the
 * Context baseclass. If this extension is not compiled the datastructure
 * module implements a class in python.
 *
 * Note that if you change semantics here you have to edit the _native.py
 * to in order to support those changes for jinja setups without the
 * speedup module too.
 *
 * TODO:
 * 	- implement a cgi.escape replacement in this module
 *
 * :copyright: 2007 by Armin Ronacher.
 * :license: BSD, see LICENSE for more details.
 */

#include <Python.h>
#include <structmember.h>

/* Set by init_constants to real values */
static PyObject *Undefined, *Deferred, *TemplateRuntimeError;
static Py_UNICODE *amp, *lt, *gt, *qt;

/**
 * Internal struct used by BaseContext to store the
 * stacked namespaces.
 */
struct StackLayer {
	PyObject *dict;			/* current value, a dict */
	struct StackLayer *prev;	/* lower struct layer or NULL */
};

/**
 * BaseContext python class.
 */
typedef struct {
	PyObject_HEAD
	struct StackLayer *globals;	/* the dict for the globals */
	struct StackLayer *initial;	/* initial values */
	struct StackLayer *current;	/* current values */
	long stacksize;			/* current size of the stack */
	int silent;			/* boolean value for silent failure */
} BaseContext;

/**
 * Called by init_speedups in order to retrieve references
 * to some exceptions and classes defined in jinja python modules
 */
static int
init_constants(void)
{
	PyObject *datastructure = PyImport_ImportModule("jinja.datastructure");
	if (!datastructure)
		return 0;
	PyObject *exceptions = PyImport_ImportModule("jinja.exceptions");
	if (!exceptions) {
		Py_DECREF(datastructure);
		return 0;
	}
	Undefined = PyObject_GetAttrString(datastructure, "Undefined");
	Deferred = PyObject_GetAttrString(datastructure, "Deferred");
	TemplateRuntimeError = PyObject_GetAttrString(exceptions, "TemplateRuntimeError");

	amp = ((PyUnicodeObject*)PyUnicode_DecodeASCII("&amp;", 5, NULL))->str;
	lt = ((PyUnicodeObject*)PyUnicode_DecodeASCII("&lt;", 4, NULL))->str;
	gt = ((PyUnicodeObject*)PyUnicode_DecodeASCII("&gt;", 4, NULL))->str;
	qt = ((PyUnicodeObject*)PyUnicode_DecodeASCII("&#34;", 5, NULL))->str;

	Py_DECREF(datastructure);
	Py_DECREF(exceptions);
	return 1;
}

/**
 * SGML/XML escape something.
 *
 * XXX: this is awefully slow for non unicode objects because they
 * 	get converted to unicode first.
 */
static PyObject*
escape(PyObject *self, PyObject *args)
{
	PyUnicodeObject *in, *out;
	Py_UNICODE *outp;
	int i, len;

	int quotes = 0;
	PyObject *text = NULL;

	if (!PyArg_ParseTuple(args, "O|b", &text, &quotes))
		return NULL;
	in = (PyUnicodeObject*)PyObject_Unicode(text);
	if (!in)
		return NULL;

	/* First we need to figure out how long the escaped string will be */
	len = 0;
	for (i = 0;i < in->length; i++) {
		switch (in->str[i]) {
			case '&':
				len += 5;
				break;
			case '"':
				len += quotes ? 5 : 1;
				break;
			case '<':
			case '>':
				len += 4;
				break;
			default:
				len++;
		}
	}

	/* Do we need to escape anything at all? */
	if (len == in->length) {
		Py_INCREF(in);
		return (PyObject*)in;
	}
	out = (PyUnicodeObject*)PyUnicode_FromUnicode(NULL, len);
	if (!out) {
		return NULL;
	}

	outp = out->str;
	for (i = 0;i < in->length; i++) {
		switch (in->str[i]) {
			case '&':
				Py_UNICODE_COPY(outp, amp, 5);
				outp += 5;
				break;
			case '"':
				if (quotes) {
					Py_UNICODE_COPY(outp, qt, 5);
					outp += 5;
				}
				else
					*outp++ = in->str[i];
				break;
			case '<':
				Py_UNICODE_COPY(outp, lt, 4);
				outp += 4;
				break;
			case '>':
				Py_UNICODE_COPY(outp, gt, 4);
				outp += 4;
				break;
			default:
				*outp++ = in->str[i];
		};
	}

	return (PyObject*)out;
}

/**
 * Deallocator for BaseContext.
 *
 * Frees the memory for the stack layers before freeing the object.
 */
static void
BaseContext_dealloc(BaseContext *self)
{
	struct StackLayer *current = self->current, *tmp;
	while (current) {
		tmp = current;
		Py_XDECREF(current->dict);
		current->dict = NULL;
		current = tmp->prev;
		PyMem_Free(tmp);
	}
	self->ob_type->tp_free((PyObject*)self);
}

/**
 * Initializes the BaseContext.
 *
 * Like the native python class it takes a flag telling the context
 * to either fail silently with Undefined or raising a TemplateRuntimeError.
 * The other two arguments are the global namespace and the initial
 * namespace which usually contains the values passed to the render
 * function of the template. Both must be dicts.
 */
static int
BaseContext_init(BaseContext *self, PyObject *args, PyObject *kwds)
{
	PyObject *silent = NULL, *globals = NULL, *initial = NULL;

	static char *kwlist[] = {"silent", "globals", "initial", NULL};
	if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOO", kwlist,
					 &silent, &globals, &initial))
		return -1;
	if (!PyDict_Check(globals) || !PyDict_Check(initial)) {
		PyErr_SetString(PyExc_TypeError, "stack layers must be a dicts.");
		return -1;
	}

	self->silent = PyObject_IsTrue(silent);

	self->globals = PyMem_Malloc(sizeof(struct StackLayer));
	self->globals->dict = globals;
	Py_INCREF(globals);
	self->globals->prev = NULL;

	self->initial = PyMem_Malloc(sizeof(struct StackLayer));
	self->initial->dict = initial;
	Py_INCREF(initial);
	self->initial->prev = self->globals;

	self->current = PyMem_Malloc(sizeof(struct StackLayer));
	self->current->dict = PyDict_New();
	if (!self->current->dict)
		return -1;
	self->current->prev = self->initial;

	self->stacksize = 3;
	return 0;
}

/**
 * Pop the highest layer from the stack and return it
 */
static PyObject*
BaseContext_pop(BaseContext *self)
{
	if (self->stacksize <= 3) {
		PyErr_SetString(PyExc_IndexError, "stack too small.");
		return NULL;
	}
	PyObject *result = self->current->dict;
	struct StackLayer *tmp = self->current;
	self->current = tmp->prev;
	PyMem_Free(tmp);
	self->stacksize--;
	return result;
}

/**
 * Push a new layer to the stack and return it. If no parameter
 * is provided an empty dict is created. Otherwise the dict passed
 * to it is used as new layer.
 */
static PyObject*
BaseContext_push(BaseContext *self, PyObject *args)
{
	PyObject *value = NULL;
	if (!PyArg_ParseTuple(args, "|O:push", &value))
		return NULL;
	if (!value) {
		value = PyDict_New();
		if (!value)
			return NULL;
	}
	else if (!PyDict_Check(value)) {
		PyErr_SetString(PyExc_TypeError, "dict required.");
		return NULL;
	}
	else
		Py_INCREF(value);
	struct StackLayer *new = PyMem_Malloc(sizeof(struct StackLayer));
	new->dict = value;
	new->prev = self->current;
	self->current = new;
	self->stacksize++;
	Py_INCREF(value);
	return value;
}

/**
 * Getter that creates a list representation of the internal
 * stack. Used for compatibility with the native python implementation.
 */
static PyObject*
BaseContext_getstack(BaseContext *self, void *closure)
{
	PyObject *result = PyList_New(self->stacksize);
	if (!result)
		return NULL;
	struct StackLayer *current = self->current;
	int idx = 0;
	while (current) {
		Py_INCREF(current->dict);
		PyList_SetItem(result, idx++, current->dict);
		current = current->prev;
	}
	PyList_Reverse(result);
	return result;
}

/**
 * Getter that returns a reference to the current layer in the context.
 */
static PyObject*
BaseContext_getcurrent(BaseContext *self, void *closure)
{
	Py_INCREF(self->current->dict);
	return self->current->dict;
}

/**
 * Getter that returns a reference to the initial layer in the context.
 */
static PyObject*
BaseContext_getinitial(BaseContext *self, void *closure)
{
	Py_INCREF(self->initial->dict);
	return self->initial->dict;
}

/**
 * Getter that returns a reference to the global layer in the context.
 */
static PyObject*
BaseContext_getglobals(BaseContext *self, void *closure)
{
	Py_INCREF(self->globals->dict);
	return self->globals->dict;
}

/**
 * Generic setter that just raises an exception to notify the user
 * that the attribute is read-only.
 */
static int
BaseContext_readonly(BaseContext *self, PyObject *value, void *closure)
{
	PyErr_SetString(PyExc_AttributeError, "can't set attribute");
	return -1;
}

/**
 * Implements the context lookup.
 *
 * This works exactly like the native implementation but a lot
 * faster. It disallows access to internal names (names that start
 * with "::") and resolves Deferred values.
 */
static PyObject*
BaseContext_getitem(BaseContext *self, PyObject *item)
{
	if (!PyString_Check(item))
		goto missing;

	/* disallow access to internal jinja values */
	char *name = PyString_AS_STRING(item);
	if (name[0] == ':' && name[1] == ':')
		goto missing;

	PyObject *result;
	struct StackLayer *current = self->current;
	while (current) {
		result = PyDict_GetItemString(current->dict, name);
		if (!result) {
			current = current->prev;
			continue;
		}
		Py_INCREF(result);
		if (PyObject_IsInstance(result, Deferred)) {
			PyObject *args = PyTuple_New(2);
			if (!args || PyTuple_SetItem(args, 0, (PyObject*)self) ||
			    PyTuple_SetItem(args, 1, item))
				return NULL;

			PyObject *resolved = PyObject_CallObject(result, args);
			if (!resolved)
				return NULL;

			/* never touch the globals */
			Py_DECREF(result);
			Py_INCREF(resolved);
			PyObject *namespace;
			if (current == self->globals)
				namespace = self->initial->dict;
			else
				namespace = current->dict;
			PyDict_SetItemString(namespace, name, resolved);
			return resolved;
		}
		return result;
	}

missing:
	if (self->silent) {
		Py_INCREF(Undefined);
		return Undefined;
	}
	PyErr_Format(TemplateRuntimeError, "'%s' is not defined", name);
	return NULL;
}

/**
 * Check if the context contains a given value.
 */
static int
BaseContext_contains(BaseContext *self, PyObject *item)
{
	if (!PyString_Check(item))
		return 0;

	char *name = PyString_AS_STRING(item);
	if (strlen(name) >= 2 && name[0] == ':' && name[1] == ':')
		return 0;

	struct StackLayer *current = self->current;
	while (current) {
		if (!PyMapping_HasKeyString(current->dict, name)) {
			current = current->prev;
			continue;
		}
		return 1;
	}

	return 0;
}

/**
 * Set an value in the highest layer or delete one.
 */
static int
BaseContext_setitem(BaseContext *self, PyObject *item, PyObject *value)
{
	char *name = PyString_AS_STRING(item);
	if (!value)
		return PyDict_DelItemString(self->current->dict, name);
	return PyDict_SetItemString(self->current->dict, name, value);
}

/**
 * Size of the stack.
 */
static PyObject*
BaseContext_length(BaseContext *self)
{
	return PyInt_FromLong(self->stacksize);
}


static PyGetSetDef BaseContext_getsetters[] = {
	{"stack", (getter)BaseContext_getstack, (setter)BaseContext_readonly,
	 "a read only copy of the internal stack", NULL},
	{"current", (getter)BaseContext_getcurrent, (setter)BaseContext_readonly,
	 "reference to the current layer on the stack", NULL},
	{"initial", (getter)BaseContext_getinitial, (setter)BaseContext_readonly,
	 "reference to the initial layer on the stack", NULL},
	{"globals", (getter)BaseContext_getglobals, (setter)BaseContext_readonly,
	 "reference to the global layer on the stack", NULL},
	{NULL}				/* Sentinel */
};

static PyMemberDef BaseContext_members[] = {
	{NULL}				/* Sentinel */
};

static PyMethodDef BaseContext_methods[] = {
	{"pop", (PyCFunction)BaseContext_pop, METH_NOARGS,
	 "ctx.pop() -> dict\n\n"
	 "Pop the last layer from the stack and return it."},
	{"push", (PyCFunction)BaseContext_push, METH_VARARGS,
	 "ctx.push([layer]) -> layer\n\n"
	 "Push one layer to the stack. Layer must be a dict "
	 "or omitted."},
	{NULL}				/* Sentinel */
};

static PySequenceMethods BaseContext_as_sequence[] = {
	0,				/* sq_length */
	0,				/* sq_concat */
	0,				/* sq_repeat */
	0,				/* sq_item */
	0,				/* sq_slice */
	0,				/* sq_ass_item */
	0,				/* sq_ass_slice */
	BaseContext_contains,		/* sq_contains */
	0,				/* sq_inplace_concat */
	0				/* sq_inplace_repeat */
};

static PyMappingMethods BaseContext_as_mapping[] = {
	(lenfunc)BaseContext_length,
	(binaryfunc)BaseContext_getitem,
	(objobjargproc)BaseContext_setitem
};

static PyTypeObject BaseContextType = {
	PyObject_HEAD_INIT(NULL)
	0,				/* ob_size */
	"jinja._speedups.BaseContext",	/* tp_name */
	sizeof(BaseContext),		/* tp_basicsize */
	0,				/* tp_itemsize */
	(destructor)BaseContext_dealloc,/* tp_dealloc */
	0,				/* tp_print */
	0,				/* tp_getattr */
	0,				/* tp_setattr */
	0,				/* tp_compare */
	0,				/* tp_repr */
	0,				/* tp_as_number */
	&BaseContext_as_sequence,	/* tp_as_sequence */
	&BaseContext_as_mapping,	/* tp_as_mapping */
	0,				/* tp_hash */
	0,				/* tp_call */
	0,				/* tp_str */
	0,				/* tp_getattro */
	0,				/* tp_setattro */
	0,				/* tp_as_buffer */
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
	"",				/* tp_doc */
	0,				/* tp_traverse */
	0,				/* tp_clear */
	0,				/* tp_richcompare */
	0,				/* tp_weaklistoffset */
	0,				/* tp_iter */
	0,				/* tp_iternext */
	BaseContext_methods,		/* tp_methods */
	BaseContext_members,		/* tp_members */
	BaseContext_getsetters,		/* tp_getset */
	0,				/* tp_base */
	0,				/* tp_dict */
	0,				/* tp_descr_get */
	0,				/* tp_descr_set */
	0,				/* tp_dictoffset */
	(initproc)BaseContext_init,	/* tp_init */
	0,				/* tp_alloc */
	PyType_GenericNew		/* tp_new */
};

static PyMethodDef module_methods[] = {
	{"escape", (PyCFunction)escape, METH_VARARGS,
	 "escape(s, quotes=False) -> string\n\n"
	 "SGML/XML a string."},
	{NULL, NULL, 0, NULL}		/* Sentinel */
};

#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
init_speedups(void)
{
	PyObject *module;

	if (PyType_Ready(&BaseContextType) < 0)
		return;

	if (!init_constants())
		return;

	module = Py_InitModule3("_speedups", module_methods, "");
	if (!module)
		return;

	Py_INCREF(&BaseContextType);
	PyModule_AddObject(module, "BaseContext", (PyObject*)&BaseContextType);
}
