"""The guardrails: anything the LLM writes must come from the source item."""

from checks import check_names, check_numbers, check_quotes, check_text

SOURCE = (
    "OpenAI working on new $30B raise at $1.25T valuation ahead of IPO. "
    "Should OpenAI command an over $1 trillion valuation, it would break records."
)


def test_numbers_from_the_source_pass():
    assert check_numbers("OpenAI is raising $30B at a $1.25T valuation.", SOURCE) == []


def test_invented_number_is_caught():
    assert check_numbers("OpenAI is raising $40B.", SOURCE) == ["number '40' is not in the source"]


def test_thousands_separators_are_ignored():
    assert check_numbers("It has 1,200 staff.", "It has 1200 staff.") == []


def test_exact_quote_passes_and_curly_quotes_match_straight_ones():
    assert check_quotes('It would "break records".', SOURCE) == []
    assert check_quotes("It would “break records”.", SOURCE) == []


def test_reworded_quote_is_caught():
    assert check_quotes('It would "smash every record".', SOURCE)


def test_invented_name_is_caught():
    assert check_names("OpenAI is backed by Microsoft.", SOURCE) == ["name 'Microsoft' is not in the source"]


def test_capitalized_words_at_sentence_start_are_skipped():
    assert check_names("The company wants money. Big news for investors.", SOURCE) == []


def test_common_acronyms_are_not_treated_as_names():
    assert check_names("OpenAI says its AI and API plans will change.", SOURCE) == []


def test_check_text_combines_every_check():
    problems = check_text('OpenAI raised $40B, says "smash every record", with Microsoft.', SOURCE)
    assert len(problems) == 3
