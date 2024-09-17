import module_collecter

EXPECTED_SUBMODULES = [
    "tests.helper.some_package.other",
    "tests.helper.some_package.crkinge",
    "tests.helper.some_package.subpackage",
    "tests.helper.some_package.subpackage.more_subpackage",
    "tests.helper.some_package.subpackage.more_subpackage.vendpor",
    "tests.helper.some_package.subpackage.more_subpackage.vendpor.cringe",
    "tests.helper.some_package.subpackage.more_subpackage.more_stuff",
    "tests.helper.some_package.subpackage.more_subpackage.more_stuff.nope",
]

def test_collect_modules():
    from tests.helper import some_package
    from tests.helper.some_package import crkinge as c
    from tests.helper.some_package import subpackage as more_subpackage
    results = module_collecter.collect_modules(some_package)
    assert results.origin is some_package
    assert list(results.submodules) == EXPECTED_SUBMODULES
