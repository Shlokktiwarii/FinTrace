def test_fintrace_package_is_importable() -> None:
    import fintrace

    assert fintrace.__name__ == "fintrace"