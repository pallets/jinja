/**
 * Jinja Extended Debugger
 * ~~~~~~~~~~~~~~~~~~~~~~~
 *
 * this module allows the jinja debugger to set the tb_next flag
 * on traceback objects. This is required to inject a traceback into
 * another one.
 *
 * For better windows support (not everybody has a visual studio 2003
 * at home) it would be a good thing to have a ctypes implementation, but
 * because the struct is not exported there is currently no sane way.
 *
 * :copyright: 2007 by Armin Ronacher.
 * :license: BSD, see LICENSE for more details.
 */

#include <Python.h>


/**
 * set the tb_next attribute of a traceback object
 */
static PyObject *
tb_set_next(PyObject *self, PyObject *args)
{
	PyTracebackObject *tb, *old;
	PyObject *next;

	if (!PyArg_ParseTuple(args, "O!O:tb_set_next", &PyTraceBack_Type, &tb, &next))
		return NULL;
	if (next == Py_None) {
		next = NULL;
	} else if (!PyTraceBack_Check(next)) {
		PyErr_SetString(PyExc_TypeError,
				"tb_set_next arg 2 must be traceback or None");
		return NULL;
	} else {
		Py_INCREF(next);
	}

	old = tb->tb_next;
	tb->tb_next = (PyTracebackObject *)next;
	Py_XDECREF(old);

	Py_INCREF(Py_None);
	return Py_None;
}


static PyMethodDef module_methods[] = {
	{"tb_set_next", (PyCFunction)tb_set_next, METH_VARARGS,
	 "Set the tb_next member of a traceback object."},
	{NULL, NULL, 0, NULL}		/* Sentinel */
};

#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
init_debugger(void)
{
	PyObject *module = Py_InitModule3("jinja._debugger", module_methods, "");
	if (!module)
		return;
}
