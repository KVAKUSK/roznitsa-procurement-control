from scripts.matcher import Product, evaluate_analogue, rank_candidates


def test_processed_cheese_is_not_analogue_for_curd_cheese():
    requested = Product("Сыр творожный", category="сыр творожный", packaging="ванна", mass_g=140)
    candidate = Product("Сыр плавленый", category="сыр плавленый", packaging="ванна", mass_g=140)
    result = evaluate_analogue(requested, candidate)
    assert not result.allowed


def test_red_beans_are_not_white_beans_in_tomato():
    requested = Product("Фасоль красная", category="фасоль красная", packaging="ж/б", mass_g=400)
    candidate = Product("Фасоль белая в томатном соусе", category="фасоль белая в томатном соусе", packaging="ж/б", mass_g=400)
    result = evaluate_analogue(requested, candidate)
    assert not result.allowed


def test_mashed_potato_72g_prefers_close_mass_over_40g():
    requested = Product("Картофельное пюре", category="пюре", packaging="мягкая пачка", mass_g=72, brand="Big Lunch")
    close = Product("Картофельное пюре", category="пюре", packaging="мягкая пачка", mass_g=70, brand="Big Lunch")
    far = Product("Картошечка", category="пюре", packaging="мягкая пачка", mass_g=40, brand="Другая")

    close_result = evaluate_analogue(requested, close)
    far_result = evaluate_analogue(requested, far)

    assert close_result.allowed and far_result.allowed
    assert close_result.score > far_result.score
    assert any("Масса отличается" in r for r in far_result.reasons)


def test_different_category_is_rejected_even_if_brand_and_weight_match():
    requested = Product("Мохито", category="газированный напиток", packaging="ж/б", mass_g=450, brand="Черноголовка")
    candidate = Product("Минеральная вода", category="минеральная вода", packaging="пэт", mass_g=450, brand="Черноголовка")
    result = evaluate_analogue(requested, candidate)
    assert not result.allowed


def test_same_brand_line_flavor_ranks_first():
    requested = Product("Лапша кимчи", category="лапша", packaging="пачка", mass_g=120, brand="Nongshim", line="Shin", flavor="кимчи")
    exactish = Product("Лапша кимчи", category="лапша", packaging="пачка", mass_g=120, brand="Nongshim", line="Shin", flavor="кимчи")
    other = Product("Лапша острая", category="лапша", packaging="пачка", mass_g=120, brand="Samyang", line="Buldak", flavor="острая")
    ranked = rank_candidates(requested, [other, exactish])
    assert ranked[0][0] == exactish
