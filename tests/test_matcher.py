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

    ranked = rank_candidates(requested, [far, close])

    assert ranked[0][0] == close
    assert far not in [item[0] for item in ranked]


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


def test_meat_snack_never_matches_breadcrumb_snack():
    requested = Product("Кнуты классические 70 г", category="мясной снек", packaging="в/у", mass_g=70, brand="Атяшево")
    candidate = Product("Сухарики телятина с аджикой 80 г", category="сухарики", packaging="м/у", mass_g=80, brand="Крутец")
    result = evaluate_analogue(requested, candidate)
    assert not result.allowed


def test_baguette_never_matches_croissant():
    requested = Product("Багет мини 130 г", category="багет", packaging="замороженный", mass_g=130, brand="Хлебный Дом")
    candidate = Product("Круассан шоколадный 180 г", category="круассан", packaging="замороженный", mass_g=180, brand="Яшкино")
    result = evaluate_analogue(requested, candidate)
    assert not result.allowed


def test_chan_ramen_120g_prefers_other_brand_close_ramen_over_doshirak_90g():
    requested = Product("Доширак Чан Рамэн 120 г", category="лапша рамен", packaging="пачка", mass_g=120, brand="Доширак", line="Чан Рамэн")
    lexical_brand_match = Product("Доширак лапша 90 г", category="лапша рамен", packaging="пачка", mass_g=90, brand="Доширак")
    samyang_120 = Product("Samyang рамен острая говядина 120 г", category="лапша рамен", packaging="пачка", mass_g=120, brand="Samyang")
    ottogi_120 = Product("Ottogi Jin Ramen Hot 120 г", category="лапша рамен", packaging="пачка", mass_g=120, brand="Ottogi", line="Jin Ramen")

    ranked = rank_candidates(requested, [lexical_brand_match, samyang_120, ottogi_120])
    ranked_products = [item[0] for item in ranked]

    assert lexical_brand_match not in ranked_products
    assert samyang_120 in ranked_products
    assert ottogi_120 in ranked_products


def test_big_lunch_90g_drops_75g_when_exact_mass_exists():
    requested = Product("Big Lunch 90 г", category="лапша", packaging="лоток", mass_g=90, brand="Big Lunch")
    exact = Product("Бизнес Ланч 90 г", category="лапша", packaging="лоток", mass_g=90, brand="Big Lunch")
    far = Product("Big Lunch 75 г", category="лапша", packaging="пачка", mass_g=75, brand="Big Lunch")

    ranked = rank_candidates(requested, [far, exact])

    assert ranked[0][0] == exact
    assert far in [item[0] for item in ranked]  # 75 г is within ±20%, so it remains a fallback.
