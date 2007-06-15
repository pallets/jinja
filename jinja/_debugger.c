/**
 * Jinja Extended Debugger
 * ~~~~~~~~~~~~~~~~~~~~~~~
 *
 * this module allows the jinja debugger to set the tb_next flag
 * on traceback objects. This is required to inject a traceback into
 * another one.
 *
 * :copyright: 2007 by Armin Ronacher.
 * :license: BSD, see LICENSE for more details.
 */

#include <Python.h>


/**
 * set the tb_next attribute of a traceback object
 */
PyObject*
tb_set_next(PyObject *self, PyObject *args)
{
	PyObject *tb, *next;

	if (!PyArg_ParseTuple(args, "OO", &tb, &next))
		return NULL;
	if (!(PyTraceBack_Check(tb) && (PyTraceBack_Check(next) || next == Py_None))) {
		PyErr_SetString(PyExc_TypeError, "traceback object required.");
		return NULL;
	}

	((PyTracebackObject*)tb)->tb_next = next;

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
	PyObject *module = Py_InitModule3("_debugger", module_methods, "");
	if (!module)
		return;
}
