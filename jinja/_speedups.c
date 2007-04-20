/**
 * jinja._speedups
 * ~~~~~~~~~~~~~~~
 *
 * This module implements the BaseContext, a c implementation of the
 * Context baseclass. If this extension is not compiled the datastructure
 * module implements a class in python.
 *
 * :copyright: 2007 by Armin Ronacher.
 * :license: BSD, see LICENSE for more details.
 */

#include <Python.h>
#include <structmember.h>

static PyObject *Undefined, *TemplateRuntimeError;
static PyTypeObject *DeferredType;

struct StackLayer {
	PyObject *dict;			/* current value, a dict */
	struct StackLayer *prev;	/* lower struct layer or NULL */
};

typedef struct {
	PyObject_HEAD
	struct StackLayer *globals;	/* the dict for the globals */
	struct StackLayer *initial;	/* initial values */
	struct StackLayer *current;	/* current values */
	long stacksize;			/* current size of the stack */
	int silent;			/* boolean value for silent failure */
} BaseContext;

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
	PyObject *deferred = PyObject_GetAttrString(datastructure, "Deferred");
	DeferredType = deferred->ob_type;
	TemplateRuntimeError = PyObject_GetAttrString(exceptions, "TemplateRuntimeError");
	Py_DECREF(datastructure);
	Py_DECREF(exceptions);
	return 1;
}

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
	Py_INCREF(self->current->dict);
	self->current->prev = self->initial;

	self->stacksize = 3;
	return 0;
}

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
	struct StackLayer *new = malloc(sizeof(struct StackLayer));
	new->dict = value;
	new->prev = self->current;
	self->current = new;
	self->stacksize++;
	Py_INCREF(value);
	return value;
}

static PyObject*
BaseContext_getstack(BaseContext *self, void *closure)
{
	PyObject *result = PyList_New(self->stacksize);
	if (!result)
		return NULL;
	struct StackLayer *current = self->current;
	int idx = 0;
	while (current) {
		PyList_SetItem(result, idx++, current->dict);
		Py_INCREF(current->dict);
		current = current->prev;
	}
	PyList_Reverse(result);
	return result;
}

static PyObject*
BaseContext_getcurrent(BaseContext *self, void *closure)
{
	Py_INCREF(self->current->dict);
	return self->current->dict;
}

static PyObject*
BaseContext_getinitial(BaseContext *self, void *closure)
{
	Py_INCREF(self->initial->dict);
	return self->initial->dict;
}

static PyObject*
BaseContext_getglobals(BaseContext *self, void *closure)
{
	Py_INCREF(self->globals->dict);
	return self->globals->dict;
}

static int
BaseContext_readonly(BaseContext *self, PyObject *value, void *closure)
{
	PyErr_SetString(PyExc_AttributeError, "can't set attribute");
	return -1;
}

static PyObject*
BaseContext_getitem(BaseContext *self, PyObject *item)
{
	if (!PyString_Check(item)) {
		Py_INCREF(Py_False);
		return Py_False;
	}

	/* disallow access to internal jinja values */
	char *name = PyString_AS_STRING(item);
	if (strlen(name) >= 2 && name[0] == ':' && name[1] == ':') {
		Py_INCREF(Py_False);
		return Py_False;
	}

	PyObject *result;
	struct StackLayer *current = self->current;
	while (current) {
		result = PyDict_GetItemString(current->dict, name);
		if (!result) {
			current = current->prev;
			continue;
		}
		Py_INCREF(result);
		if (PyObject_TypeCheck(result, DeferredType)) {
			PyObject *args = PyTuple_New(2);
			if (!args || !PyTuple_SetItem(args, 0, (PyObject*)self) ||
			    !PyTuple_SetItem(args, 1, item))
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

	if (self->silent) {
		Py_INCREF(Undefined);
		return Undefined;
	}
	PyErr_Format(TemplateRuntimeError, "'%s' is not defined", name);
	return NULL;
}

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

static int
BaseContext_setitem(BaseContext *self, PyObject *item, PyObject *value)
{
	char *name = PyString_AS_STRING(item);
	if (!value)
		return PyDict_DelItemString(self->current->dict, name);
	return PyDict_SetItemString(self->current->dict, name, value);
}

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
	 "Pop the highest layer from the stack"},
	{"push", (PyCFunction)BaseContext_push, METH_VARARGS,
	 "Push one layer to the stack"},
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
