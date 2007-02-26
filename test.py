from jinja.environment import Environment

e = Environment()

def test(x):
    for pos, token, data in e.lexer.tokenize(x):
        print '%-8d%-30r%-40r' % (pos, token, data)
