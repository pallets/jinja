import pickle


def test_environment(env):
    env = pickle.loads(pickle.dumps(env))
    assert env.from_string("x={{ x }}").render(x=42) == "x=42"
