from leadgen.generator import make_pack_id


def test_make_pack_id_all_fields():
    pack_id = make_pack_id(
        country="usa",
        state="florida",
        county="palm beach county",
        city="boca raton",
        niche="restaurants",
        limit=50,
    )
    assert pack_id == "usa_florida_palm_beach_county_boca_raton_restaurants_50"


def test_make_pack_id_skips_missing():
    pack_id = make_pack_id(
        country="jamaica",
        state=None,
        county=None,
        city="kingston",
        niche=None,
        limit=25,
    )
    assert pack_id == "jamaica_kingston_25"
