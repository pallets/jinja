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
 * :copyright: 2007 by Armin Ronacher.
 * :license: BSD, see LICENSE for more details.
 */

#include <Python.h>
#include <structmember.h>

/* Set by init_constants to real values */
static PyObject *Deferred;

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
	PyObject *undefined_singleton;	/* the singleton returned on missing values */
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
	Deferred = PyObject_GetAttrString(datastructure, "Deferred");
	Py_DECREF(datastructure);
	return 1;
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
 * Like the native python class it takes a reference to the undefined
 * singleton which will be used for undefined values.
 * The other two arguments are the global namespace and the initial
 * namespace which usually contains the values passed to the render
 * function of the template. Both must be dicts.
 */
static int
BaseContext_init(BaseContext *self, PyObject *args, PyObject *kwds)
{
	PyObject *undefined = NULL, *globals = NULL, *initial = NULL;

	if (!PyArg_ParseTuple(args, "OOO", &undefined, &globals, &initial))
		return -1;
	if (!PyDict_Check(globals) || !PyDict_Check(initial)) {
		PyErr_SetString(PyExc_TypeError, "stack layers must be dicts.");
		return -1;
	}

	self->current = PyMem_Malloc(sizeof(struct StackLayer));
	self->current->prev = NULL;
	self->current->dict = PyDict_New();
	if (!self->current->dict)
		return -1;

	self->initial = PyMem_Malloc(sizeof(struct StackLayer));
	self->initial->prev = NULL;
	self->initial->dict = initial;
	Py_INCREF(initial);
	self->current->prev = self->initial;

	self->globals = PyMem_Malloc(sizeof(struct StackLayer));
	self->globals->prev = NULL;
	self->globals->dict = globals;
	Py_INCREF(globals);
	self->initial->prev = self->globals;

	self->undefined_singleton = undefined;
	Py_INCREF(undefined);

	self->stacksize = 3;
	return 0;
}

/**
 * Pop the highest layer from the stack and return it
 */
static PyObject*
BaseContext_pop(BaseContext *self)
{
	PyObject *result;
	struct StackLayer *tmp = self->current;

	if (self->stacksize <= 3) {
		PyErr_SetString(PyExc_IndexError, "stack too small.");
		return NULL;
	}
	result = self->current->dict;
	assert(result);
	self->current = tmp->prev;
	PyMem_Free(tmp);
	self->stacksize--;
	/* Took the reference to result from the struct. */
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
	struct StackLayer *new;

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
	new = PyMem_Malloc(sizeof(struct StackLayer));
	if (!new) {
		Py_DECREF(value);
		return NULL;
	}
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
	int idx = 0;
	struct StackLayer *current = self->current;
	PyObject *result = PyList_New(self->stacksize);
	if (!result)
		return NULL;
	while (current) {
		Py_INCREF(current->dict);
		PyList_SET_ITEM(result, idx++, current->dict);
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
 * Implements the context lookup.
 *
 * This works exactly like the native implementation but a lot
 * faster. It disallows access to internal names (names that start
 * with "::") and resolves Deferred values.
 */
static PyObject*
BaseContext_getitem(BaseContext *self, PyObject *item)
{
	PyObject *result;
	char *name = NULL;
	int isdeferred;
	struct StackLayer *current = self->current;
	
	/* allow unicode keys as long as they are ascii keys */
	if (PyUnicode_CheckExact(item)) {
		item = PyUnicode_AsASCIIString(item);
		if (!item)
			goto missing;
	}
	else if (!PyString_Check(item))
		goto missing;

	/* disallow access to internal jinja values */
	name = PyString_AS_STRING(item);
	if (name[0] == ':' && name[1] == ':')
		goto missing;

	while (current) {
		/* GetItemString just builds a new string from "name" again... */
		result = PyDict_GetItem(current->dict, item);
		if (!result) {
			current = current->prev;
			continue;
		}
		isdeferred = PyObject_IsInstance(result, Deferred);
		if (isdeferred == -1)
			return NULL;
		else if (isdeferred) {
			PyObject *namespace;
			PyObject *resolved = PyObject_CallFunctionObjArgs(
						result, self, item, NULL);
			if (!resolved)
				return NULL;

			/* never touch the globals */
			if (current == self->globals)
				namespace = self->initial->dict;
			else
				namespace = current->dict;
			if (PyDict_SetItem(namespace, item, resolved) < 0)
				return NULL;
			Py_INCREF(resolved);
			return resolved;
		}
		Py_INCREF(result);
		return result;
	}

missing:
	Py_INCREF(self->undefined_singleton);
	return self->undefined_singleton;
}

/**
 * Check if the context contains a given value.
 */
static int
BaseContext_contains(BaseContext *self, PyObject *item)
{
	char *name;
	struct StackLayer *current = self->current;

	/* allow unicode objects as keys as long as they are ASCII */
	if (PyUnicode_CheckExact(item)) {
		item = PyUnicode_AsASCIIString(item);
		if (!item)
			return 0;
	}
	else if (!PyString_Check(item))
		return 0;

	name = PyString_AS_STRING(item);
	if (name[0] == ':' && name[1] == ':')
		return 0;

	while (current) {
		/* XXX: for 2.4 and newer, use PyDict_Contains */
		if (!PyMapping_HasKey(current->dict, item)) {
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
	/* allow unicode objects as keys as long as they are ASCII */
	if (PyUnicode_CheckExact(item)) {
		item = PyUnicode_AsASCIIString(item);
		if (!item) {
			PyErr_Clear();
			goto error;
		}
	}
	else if (!PyString_Check(item))
		goto error;
	if (!value)
		return PyDict_DelItem(self->current->dict, item);
	return PyDict_SetItem(self->current->dict, item, value);

error:
	PyErr_SetString(PyExc_TypeError, "expected string argument");
	return -1;
}


static PyGetSetDef BaseContext_getsetters[] = {
	{"stack", (getter)BaseContext_getstack, NULL,
	 "a read only copy of the internal stack", NULL},
	{"current", (getter)BaseContext_getcurrent, NULL,
	 "reference to the current layer on the stack", NULL},
	{"initial", (getter)BaseContext_getinitial, NULL,
	 "reference to the initial layer on the stack", NULL},
	{"globals", (getter)BaseContext_getglobals, NULL,
	 "reference to the global layer on the stack", NULL},
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
	(objobjproc)BaseContext_contains,		/* sq_contains */
	0,				/* sq_inplace_concat */
	0				/* sq_inplace_repeat */
};

static PyMappingMethods BaseContext_as_mapping[] = {
	NULL,
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
	BaseContext_as_sequence,	/* tp_as_sequence */
	BaseContext_as_mapping,		/* tp_as_mapping */
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
	0,				/* tp_members */
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
