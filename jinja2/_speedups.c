/**
 * jinja2._speedups
 * ~~~~~~~~~~~~~~~~
 *
 * This module implements a few functions in C for better performance.
 *
 * :copyright: 2008 by Armin Ronacher.
 * :license: BSD.
 */

#include <Python.h>


static const char *samp = "&amp;", *slt = "&lt;", *sgt = "&gt;", *sqt = "&quot;";
static Py_UNICODE *amp, *lt, *gt, *qt;
static PyObject* markup;


static int
init_constants(void)
{
	amp = ((PyUnicodeObject*)PyUnicode_DecodeASCII(samp, 5, NULL))->str;
	lt = ((PyUnicodeObject*)PyUnicode_DecodeASCII(slt, 4, NULL))->str;
	gt = ((PyUnicodeObject*)PyUnicode_DecodeASCII(sgt, 4, NULL))->str;
	qt = ((PyUnicodeObject*)PyUnicode_DecodeASCII(sqt, 6, NULL))->str;
	
	PyObject *module = PyImport_ImportModule("jinja2.utils");
	if (!module)
		return 0;
	markup = PyObject_GetAttrString(module, "Markup");
	Py_DECREF(module);

	return 1;
}

static PyObject*
escape_unicode(PyUnicodeObject *in)
{
	PyUnicodeObject *out;
	Py_UNICODE *outp;

	/* First we need to figure out how long the escaped string will be */
	int len = 0, erepl = 0, repl = 0;
	Py_UNICODE *inp = in->str;
	while (*(inp) || in->length > inp - in->str)
		switch (*inp++) {
		case '&':
			len += 5;
			erepl++;
			break;
		case '"':
			len += 6;
			erepl++;
			break;
		case '<':
		case '>':
			len += 4;
			erepl++;
			break;
		default:
			len++;
		}

	/* Do we need to escape anything at all? */
	if (!erepl) {
		Py_INCREF(in);
		return (PyObject*)in;
	}

	out = (PyUnicodeObject*)PyUnicode_FromUnicode(NULL, len);
	if (!out)
		return NULL;

	outp = out->str;
	inp = in->str;
	while (*(inp) || in->length > inp - in->str) {
		/* copy rest of string if we have replaced everything */
		if (repl == erepl) {
			Py_UNICODE_COPY(outp, inp, in->length - (inp - in->str));
			break;
		}
		/* regular replacements */
		switch (*inp) {
		case '&':
			Py_UNICODE_COPY(outp, amp, 5);
			outp += 5;
			repl++;
			break;
		case '"':
			Py_UNICODE_COPY(outp, qt, 6);
			outp += 6;
			repl++;
			break;
		case '<':
			Py_UNICODE_COPY(outp, lt, 4);
			outp += 4;
			repl++;
			break;
		case '>':
			Py_UNICODE_COPY(outp, gt, 4);
			outp += 4;
			repl++;
			break;
		default:
			*outp++ = *inp;
		};
		++inp;
	}

	return (PyObject*)out;
}


static PyObject*
escape(PyObject *self, PyObject *args)
{
	PyObject *text = NULL, *s = NULL, *rv = NULL;
	if (!PyArg_UnpackTuple(args, "escape", 1, 1, &text))
		return NULL;

	/* we don't have to escape integers, bools or floats */
	if (PyInt_CheckExact(text) || PyLong_CheckExact(text) ||
	    PyFloat_CheckExact(text) || PyBool_Check(text) ||
	    text == Py_None) {
		args = PyTuple_New(1);
		if (!args) {
			Py_DECREF(s);
			return NULL;
		}
		PyTuple_SET_ITEM(args, 0, text);
		return PyObject_CallObject(markup, args);
	}

	/* if the object has an __html__ method that performs the escaping */
	PyObject *html = PyObject_GetAttrString(text, "__html__");
	if (html) {
		rv = PyObject_CallObject(html, NULL);
		Py_DECREF(html);
		return rv;
	}

	/* otherwise make the object unicode if it isn't, then escape */
	PyErr_Clear();
	if (!PyUnicode_Check(text)) {
		PyObject *unicode = PyObject_Unicode(text);
		if (!unicode)
			return NULL;
		s = escape_unicode((PyUnicodeObject*)unicode);
		Py_DECREF(unicode);
	}
	else
		s = escape_unicode((PyUnicodeObject*)text);

	/* convert the unicode string into a markup object. */
	args = PyTuple_New(1);
	if (!args) {
		Py_DECREF(s);
		return NULL;
	}
	PyTuple_SET_ITEM(args, 0, (PyObject*)s);
	rv = PyObject_CallObject(markup, args);
	Py_DECREF(args);
	return rv;
}


static PyObject *
tb_set_next(PyObject *self, PyObject *args)
{
	PyTracebackObject *tb, *old;
	PyObject *next;

	if (!PyArg_ParseTuple(args, "O!O:tb_set_next", &PyTraceBack_Type, &tb, &next))
		return NULL;
	if (next == Py_None)
		next = NULL;
	else if (!PyTraceBack_Check(next)) {
		PyErr_SetString(PyExc_TypeError,
				"tb_set_next arg 2 must be traceback or None");
		return NULL;
	}
	else
		Py_INCREF(next);

	old = tb->tb_next;
	tb->tb_next = (PyTracebackObject*)next;
	Py_XDECREF(old);

	Py_INCREF(Py_None);
	return Py_None;
}


static PyMethodDef module_methods[] = {
	{"escape", (PyCFunction)escape, METH_VARARGS,
	 "escape(s) -> string\n\n"
	 "Convert the characters &, <, >, and \" in string s to HTML-safe\n"
	 "sequences. Use this if you need to display text that might contain\n"
	 "such characters in HTML."},
	{"tb_set_next", (PyCFunction)tb_set_next, METH_VARARGS,
	 "Set the tb_next member of a traceback object."},
	{NULL, NULL, 0, NULL}		/* Sentinel */
};


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
init_speedups(void)
{
	if (!init_constants())
		return;

	Py_InitModule3("jinja2._speedups", module_methods, "");
}
