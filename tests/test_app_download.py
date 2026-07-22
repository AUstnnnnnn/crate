from crate.app import progress_to_fraction


def test_progress_fraction():
    assert progress_to_fraction(
        {"status": "downloading", "downloaded_bytes": 50, "total_bytes": 100}
    ) == 0.5


def test_progress_fraction_estimate():
    assert progress_to_fraction(
        {"status": "downloading", "downloaded_bytes": 25,
         "total_bytes_estimate": 100}
    ) == 0.25


def test_progress_finished():
    assert progress_to_fraction({"status": "finished"}) == 1.0


def test_progress_unknown_is_zero():
    assert progress_to_fraction({"status": "downloading"}) == 0.0
