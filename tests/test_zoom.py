from pdfr.pdf_document import DEFAULT_ZOOM, MAX_ZOOM, MIN_ZOOM, clamp_zoom, zoom_in, zoom_out


def test_clamp_zoom_keeps_value_in_supported_range() -> None:
    assert clamp_zoom(0.01) == MIN_ZOOM
    assert clamp_zoom(99.0) == MAX_ZOOM
    assert clamp_zoom(DEFAULT_ZOOM) == DEFAULT_ZOOM


def test_zoom_helpers_move_in_expected_direction() -> None:
    assert zoom_in(DEFAULT_ZOOM) > DEFAULT_ZOOM
    assert zoom_out(DEFAULT_ZOOM) < DEFAULT_ZOOM
