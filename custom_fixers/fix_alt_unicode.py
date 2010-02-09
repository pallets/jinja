from lib2to3 import fixer_base
from lib2to3.fixer_util import Name, BlankLine


class FixAltUnicode(fixer_base.BaseFix):
    PATTERN = """
    func=funcdef< 'def' name=NAME
                  parameters< '(' NAME ')' > any+ >
    """

    run_order = 5

    def transform(self, node, results):
        name = results['name']

        # rename __unicode__ to __str__
        if name.value == '__unicode__':
            name.replace(Name('__str__', prefix=name.prefix))

        # get rid of other __str__'s
        elif name.value == '__str__':
            next = BlankLine()
            next.prefix = results['func'].prefix
            return next
