#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tiszta függvények tesztje — futtatás: python3 test_fetch_pdfs.py"""
from fetch_pdfs import (source_for, table_url, expected_header,
                        month_range, required_keywords)

# élőben igazolt horgonyok
assert source_for((2025, 3)) == (6093, 221, 6)      # Martie 2025
assert source_for((2026, 4)) == (6079, 1281, 23)    # Aprilie 2026
# vágás: 2026-01 még régi, 2026-02 már új
assert source_for((2026, 1))[0] == 6093
assert source_for((2026, 2))[0] == 6079
assert source_for((2024, 10)) == (6093, 221, 1)

assert table_url((2026, 4)) == ("https://homefile.ro/outgotable.html"
                                "#/association/6079/apartment/1281/month/23")

assert expected_header((2026, 3)) == "pe luna Martie, 2026"
assert expected_header((2025, 1)) == "pe luna Ianuarie, 2025"

r = month_range((2024, 10), (2026, 4))
assert r[0] == (2024, 10) and r[-1] == (2026, 4) and len(r) == 19

assert required_keywords((2025, 5)) == ["Restan"]
assert required_keywords((2026, 2)) == ["General", "RULMENT"]

print("OK — minden teszt zöld")
