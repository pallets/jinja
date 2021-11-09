def test_template_hash(env):
    template = env.parse("hash test")
    hash(template)
