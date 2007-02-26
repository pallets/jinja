from jinja import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader(['.'], suffix='')
)
env.filters['odd?'] = lambda c, x: x % 2 == 1
env.filters['even?'] = lambda x, x: x % 2 == 0

t = env.get_template('index.html')
print t.render(
    users=[
        dict(username='foo', user_id=1),
        dict(username='bar', user_id=2)
    ]
)
