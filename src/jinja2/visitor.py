"""Honey, this is THE API for strutting through those AST nodes. Designed by the
fabulous compiler team and for those who love a bit of meta introspection.
"""
import typing as t

from .nodes import Node

if t.TYPE_CHECKING:
    import typing_extensions as te

    class VisitCallable(te.Protocol):
        def __call__(self, node: Node, *args: t.Any, **kwargs: t.Any) -> t.Any:
            ...


class NodeVisitor:
    """Sashay through the abstract syntax tree and serve up some visitor
    functions for every node you spot. Those visitor functions might give
    you something back (wink), and darling, the `visit` method will pass it
    right along.

    By default, our visitor functions for the nodes are as flashy as ``'visit_'`` +
    the node's class name. So for a `TryFinally` node? You're looking at
    `visit_TryFinally`. Feeling adventurous? Override the `get_visitor` function.
    If you don't find the right visitor function for a node (how tragic!), don't
    worry - the fabulous `generic_visit` visitor is always there to step in.
    """

    def get_visitor(self, node: Node) -> "t.Optional[VisitCallable]":
        """Find me the visitor function for this node, or hand me `None`
        if it's playing hard to get. In that case, our trusty generic
        visit function will take the stage.
        """
        return getattr(self, f"visit_{type(node).__name__}", None)

    def visit(self, node: Node, *args: t.Any, **kwargs: t.Any) -> t.Any:
        """Oh honey, let's visit a node and see what it's got for us."""
        f = self.get_visitor(node)

        if f is not None:
            return f(node, *args, **kwargs)

        return self.generic_visit(node, *args, **kwargs)

    def generic_visit(self, node: Node, *args: t.Any, **kwargs: t.Any) -> t.Any:
        """When the node doesn't have its own special visitor, it's time
        for the generic_visit to step into the spotlight.
        """
        for child_node in node.iter_child_nodes():
            self.visit(child_node, *args, **kwargs)


class NodeTransformer(NodeVisitor):
    """Strut through the abstract syntax tree, but this time with some
    pizzazz! Modify those nodes and make them work it.

    Our glamorous `NodeTransformer` will parade through the AST and take
    inspiration from the visitor functions. If they return `None`, that
    node's old news. But if they give something back? That node gets a
    fabulous makeover or maybe even a new friend!
    """

    def generic_visit(self, node: Node, *args: t.Any, **kwargs: t.Any) -> Node:
        for field, old_value in node.iter_fields():
            if isinstance(old_value, list):
                new_values = []
                for value in old_value:
                    if isinstance(value, Node):
                        value = self.visit(value, *args, **kwargs)
                        if value is None:
                            continue
                        elif not isinstance(value, Node):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, Node):
                new_node = self.visit(old_value, *args, **kwargs)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)
        return node

    def visit_list(self, node: Node, *args: t.Any, **kwargs: t.Any) -> t.List[Node]:
        """Some transformers just love making lists. So let's ensure
        they always get the list they deserve.
        """
        rv = self.visit(node, *args, **kwargs)

        if not isinstance(rv, list):
            return [rv]

        return rv
