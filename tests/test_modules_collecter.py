import module_collecter

EXPECTED_SUBMODULES = [
    "tests.helper.some_package",
    "tests.helper.some_package.crkinge",
    "tests.helper.some_package.other",
    "tests.helper.some_package.subpackage.more_subpackage",
    "tests.helper.some_package.subpackage.more_subpackage.more_stuff.nope",
    "tests.helper.some_package.subpackage.more_subpackage.vendpor.cringe",
]

def test_collect_modules():
    from tests.helper import some_package
    # from tests.helper.some_package import crkinge as c
    results = module_collecter.collect_modules(some_package, verbose=True)
    # from tests.helper.some_package import subpackage as more_subpackage
    assert results.origin is not None and results.origin.fullname == some_package.__name__
    assert sorted(results.submodules) == EXPECTED_SUBMODULES
