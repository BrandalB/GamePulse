import pandas as pd
from gamepulse.portfolio import summarize_findings, make_case_study


def small_frames():
    games = pd.DataFrame([
        {'appid':1,'price':0,'review_count':110,'release_year':2020,'positive':100},
        {'appid':2,'price':10,'review_count':2,'release_year':2021,'positive':1},
        {'appid':3,'price':None,'review_count':0,'release_year':2021,'positive':0},
    ])
    genres = pd.DataFrame([
        {'appid':1,'genre':'Action'}, {'appid':1,'genre':'Indie'},
        {'appid':2,'genre':'Action'}, {'appid':3,'genre':'Indie'},
    ])
    return games, genres


def test_findings_have_correct_denominators():
    games, genres = small_frames()
    found = summarize_findings(games, genres)
    assert found[0]['value'] == '3'
    assert next(f for f in found if f['title']=='Free-to-play footprint')['value'] == '50.0%'
    assert next(f for f in found if f['title']=='Games with 100+ reviews')['value'] == '1'


def test_report_is_educational_and_contains_no_fake_sales():
    games, genres = small_frames()
    report = make_case_study(games, genres)
    assert '3 distinct Steam AppIDs' in report
    assert 'does not contain verified units sold' in report
    assert 'Write 2–3 sentences' in report


def test_empty_findings():
    assert summarize_findings(pd.DataFrame(), pd.DataFrame()) == []
