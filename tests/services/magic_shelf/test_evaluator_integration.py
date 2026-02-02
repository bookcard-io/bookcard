# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

from bookcard.models.core import (
    Author,
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from bookcard.models.magic_shelf_rules import (
    GroupRule,
    JoinType,
    Rule,
    RuleField,
    RuleOperator,
)
from bookcard.services.magic_shelf.evaluator import BookRuleEvaluator


@pytest.fixture(name="engine")
def fixture_engine() -> Engine:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def fixture_session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@pytest.fixture
def sample_data(session: Session) -> dict[str, int | None]:
    # Book 1: Blank ISBN
    book1 = Book(title="Blank ISBN Book", isbn="")
    session.add(book1)

    # Book 2: Genre Horror
    book2 = Book(title="Horror Book", isbn="123")
    tag_horror = Tag(name="Horror")
    session.add(tag_horror)
    session.add(book2)
    session.commit()  # Commit to get IDs
    session.add(BookTagLink(book=book2.id, tag=tag_horror.id))

    # Book 3: Highly rated recent
    book3 = Book(
        title="Good Recent Book",
        isbn="456",
        pubdate=datetime.now(UTC),
    )
    rating5 = Rating(rating=5)
    session.add(rating5)
    session.add(book3)
    session.commit()
    session.add(BookRatingLink(book=book3.id, rating=rating5.id))

    # Book 4: Title with #, no series
    book4 = Book(title="Book #4", isbn="789")
    session.add(book4)

    # Book 5: Control (Title with #, HAS series)
    book5 = Book(title="Book #5 with Series", isbn="101")
    series1 = Series(name="Some Series")
    session.add(series1)
    session.add(book5)
    session.commit()
    session.add(BookSeriesLink(book=book5.id, series=series1.id))

    # Book 6: Multiple Authors (King, Straub)
    book6 = Book(title="The Talisman", isbn="999")
    author1 = Author(name="Stephen King")
    author2 = Author(name="Peter Straub")
    session.add(author1)
    session.add(author2)
    session.add(book6)
    session.commit()
    session.add(BookAuthorLink(book=book6.id, author=author1.id))
    session.add(BookAuthorLink(book=book6.id, author=author2.id))

    # Book 7: Publisher and Language
    book7 = Book(title="French Book", isbn="888")
    pub = Publisher(name="Gallimard")
    lang = Language(lang_code="fr")
    session.add(pub)
    session.add(lang)
    session.add(book7)
    session.commit()
    session.add(BookPublisherLink(book=book7.id, publisher=pub.id))
    session.add(BookLanguageLink(book=book7.id, lang_code=lang.id))

    # Book 8: Identifiers
    book8 = Book(title="Book with DOI", isbn="777")
    session.add(book8)
    session.commit()
    ident = Identifier(book=book8.id, type="doi", val="10.1000/182")
    session.add(ident)

    # Book 9: Old low rated book
    book9 = Book(
        title="Old Bad Book",
        isbn="666",
        pubdate=datetime(1990, 1, 1, tzinfo=UTC),
    )
    rating1 = Rating(rating=1)
    session.add(rating1)
    session.add(book9)
    session.commit()
    session.add(BookRatingLink(book=book9.id, rating=rating1.id))

    session.commit()

    # Book 10: SciFi, Rating 5, Year 2025 (Recent)
    book10 = Book(
        title="SciFi Hit",
        isbn="1010",
        pubdate=datetime.now(UTC),
    )
    rating5_2 = Rating(rating=5)
    session.add(rating5_2)
    session.add(book10)
    session.commit()
    session.add(BookRatingLink(book=book10.id, rating=rating5_2.id))
    tag_scifi = Tag(name="SciFi")
    session.add(tag_scifi)
    session.commit()
    session.add(BookTagLink(book=book10.id, tag=tag_scifi.id))

    # Book 11: Horror, Rating 2, Year 1980, Author King
    book11 = Book(
        title="Old King Horror",
        isbn="1111",
        pubdate=datetime(1980, 1, 1, tzinfo=UTC),
    )
    rating2 = Rating(rating=2)
    session.add(rating2)
    session.add(book11)
    session.commit()
    session.add(BookRatingLink(book=book11.id, rating=rating2.id))
    # Reuse Horror tag and King author if possible, but creating new instances for simplicity in test data
    # (Assuming unique constraints aren't enforced in this in-memory setup or we use get_or_create logic,
    # but here we just create new ones or fetch existing if we were careful.
    # To be safe and avoid unique constraint errors if they exist, let's reuse.)
    # Actually, let's just create new ones with same names if unique constraints allow,
    # or better, fetch the ones we created earlier.
    # For simplicity in this test fixture, I'll just create new objects.
    # If unique constraints bite, we'll see.
    # The models define `name` but don't explicitly show `unique=True` in the snippet provided earlier,
    # but usually tags/authors are unique.
    # Let's try to query them to be safe.
    tag_horror_ref = session.exec(select(Tag).where(Tag.name == "Horror")).first()
    author_king_ref = session.exec(
        select(Author).where(Author.name == "Stephen King")
    ).first()

    # If they don't exist (because of test execution order or whatever), create them.
    if not tag_horror_ref:
        tag_horror_ref = Tag(name="Horror")
        session.add(tag_horror_ref)
    if not author_king_ref:
        author_king_ref = Author(name="Stephen King")
        session.add(author_king_ref)

    session.commit()
    session.add(BookTagLink(book=book11.id, tag=tag_horror_ref.id))
    session.add(BookAuthorLink(book=book11.id, author=author_king_ref.id))

    # Book 12: Romance (Control)
    book12 = Book(title="Romance Novel", isbn="1212")
    tag_romance = Tag(name="Romance")
    session.add(tag_romance)
    session.add(book12)
    session.commit()
    session.add(BookTagLink(book=book12.id, tag=tag_romance.id))

    # Book 13: Horror, Rating 2, Year 1980, Author Orwell (Control)
    book13 = Book(
        title="Old Orwell Horror",
        isbn="1313",
        pubdate=datetime(1980, 1, 1, tzinfo=UTC),
    )
    author_orwell = Author(name="George Orwell")
    session.add(author_orwell)
    session.add(book13)
    session.commit()
    session.add(BookRatingLink(book=book13.id, rating=rating2.id))  # Reuse rating 2
    session.add(BookTagLink(book=book13.id, tag=tag_horror_ref.id))  # Reuse Horror
    session.add(BookAuthorLink(book=book13.id, author=author_orwell.id))

    # Book 14: Title="UniqueTitle"
    book14 = Book(title="UniqueTitle", isbn="1414")
    session.add(book14)

    # Book 15: Author="SpecificAuthor"
    book15 = Book(title="Other Title", isbn="1515")
    author_specific = Author(name="SpecificAuthor")
    session.add(author_specific)
    session.add(book15)
    session.commit()
    session.add(BookAuthorLink(book=book15.id, author=author_specific.id))

    session.commit()

    # Refresh to ensure relationships are loaded if needed (though we query via links usually)
    return {
        "book1": book1.id,
        "book2": book2.id,
        "book3": book3.id,
        "book4": book4.id,
        "book5": book5.id,
        "book6": book6.id,
        "book7": book7.id,
        "book8": book8.id,
        "book9": book9.id,
        "book10": book10.id,
        "book11": book11.id,
        "book12": book12.id,
        "book13": book13.id,
        "book14": book14.id,
        "book15": book15.id,
    }


def test_blank_isbn(session: Session, sample_data: dict[str, int | None]) -> None:
    evaluator = BookRuleEvaluator()
    rule = Rule(field=RuleField.ISBN, operator=RuleOperator.IS_EMPTY)
    group = GroupRule(rules=[rule])

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()

    assert len(results) == 1
    assert results[0] == sample_data["book1"]


def test_genre_horror(session: Session, sample_data: dict[str, int | None]) -> None:
    evaluator = BookRuleEvaluator()
    rule = Rule(field=RuleField.TAG, operator=RuleOperator.CONTAINS, value="Horror")
    group = GroupRule(rules=[rule])

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()

    # Book 2, Book 11, Book 13 have Horror tag
    assert len(results) == 3
    ids = set(results)
    assert sample_data["book2"] in ids
    assert sample_data["book11"] in ids
    assert sample_data["book13"] in ids


def test_highly_rated_recent(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    evaluator = BookRuleEvaluator()

    # Rating > 4
    rule_rating = Rule(
        field=RuleField.RATING, operator=RuleOperator.GREATER_THAN, value=4
    )

    # Pubdate > yesterday
    yesterday = datetime.now(UTC) - timedelta(days=1)
    rule_pubdate = Rule(
        field=RuleField.PUBDATE,
        operator=RuleOperator.GREATER_THAN,
        value=yesterday.isoformat(),
    )

    group = GroupRule(rules=[rule_rating, rule_pubdate], join_type=JoinType.AND)

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()

    # Book 3 and Book 10 match
    assert len(results) == 2
    ids = set(results)
    assert sample_data["book3"] in ids
    assert sample_data["book10"] in ids


def test_title_hash_no_series(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    evaluator = BookRuleEvaluator()

    # Title contains "#"
    rule_title = Rule(field=RuleField.TITLE, operator=RuleOperator.CONTAINS, value="#")

    # Series is empty (Intended: No Series)
    rule_series = Rule(field=RuleField.SERIES, operator=RuleOperator.IS_EMPTY)

    group = GroupRule(rules=[rule_title, rule_series], join_type=JoinType.AND)

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()

    # Should match book4 (Has #, No Series)
    # Should NOT match book5 (Has #, Has Series)
    assert len(results) == 1
    assert results[0] == sample_data["book4"]


def test_multiple_authors_or_logic(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test OR logic with multiple authors."""
    evaluator = BookRuleEvaluator()

    # Author contains King OR Author contains Straub
    rule1 = Rule(field=RuleField.AUTHOR, operator=RuleOperator.CONTAINS, value="King")
    rule2 = Rule(field=RuleField.AUTHOR, operator=RuleOperator.CONTAINS, value="Straub")

    group = GroupRule(rules=[rule1, rule2], join_type=JoinType.OR)

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()

    # Should match book6 (The Talisman)
    assert len(results) >= 1
    assert sample_data["book6"] in set(results)


def test_publisher_and_language(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test filtering by Publisher AND Language."""
    evaluator = BookRuleEvaluator()

    rule_pub = Rule(
        field=RuleField.PUBLISHER, operator=RuleOperator.EQUALS, value="Gallimard"
    )
    rule_lang = Rule(field=RuleField.LANGUAGE, operator=RuleOperator.EQUALS, value="fr")

    group = GroupRule(rules=[rule_pub, rule_lang], join_type=JoinType.AND)

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()

    assert len(results) == 1
    assert results[0] == sample_data["book7"]


def test_identifier_lookup(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test filtering by Identifier value."""
    evaluator = BookRuleEvaluator()

    rule = Rule(
        field=RuleField.IDENTIFIER, operator=RuleOperator.CONTAINS, value="10.1000"
    )
    group = GroupRule(rules=[rule])

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()

    assert len(results) == 1
    assert results[0] == sample_data["book8"]


def test_nested_complex_logic(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test (Old AND Low Rated) OR (New AND High Rated)."""
    evaluator = BookRuleEvaluator()

    # Group 1: Old AND Low Rated
    cutoff_old = datetime(2000, 1, 1, tzinfo=UTC)
    g1_date = Rule(
        field=RuleField.PUBDATE,
        operator=RuleOperator.LESS_THAN,
        value=cutoff_old.isoformat(),
    )
    g1_rate = Rule(field=RuleField.RATING, operator=RuleOperator.LESS_THAN, value=3)
    group1 = GroupRule(rules=[g1_date, g1_rate], join_type=JoinType.AND)

    # Group 2: New AND High Rated
    cutoff_new = datetime.now(UTC) - timedelta(days=365)
    g2_date = Rule(
        field=RuleField.PUBDATE,
        operator=RuleOperator.GREATER_THAN,
        value=cutoff_new.isoformat(),
    )
    g2_rate = Rule(field=RuleField.RATING, operator=RuleOperator.GREATER_THAN, value=4)
    group2 = GroupRule(rules=[g2_date, g2_rate], join_type=JoinType.AND)

    # Root: Group 1 OR Group 2
    root = GroupRule(rules=[group1, group2], join_type=JoinType.OR)

    ids_stmt = evaluator.build_matching_book_ids_stmt(root)
    results = session.exec(ids_stmt).all()

    # Should match:
    # Old/Low: Book 9, Book 11, Book 13
    # New/High: Book 3, Book 10
    ids = set(results)
    assert len(ids) == 5
    assert sample_data["book9"] in ids
    assert sample_data["book11"] in ids
    assert sample_data["book13"] in ids
    assert sample_data["book3"] in ids
    assert sample_data["book10"] in ids
    assert sample_data["book1"] not in ids


def test_starts_with_ends_with(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test STARTS_WITH and ENDS_WITH operators."""
    evaluator = BookRuleEvaluator()

    # Starts with "Blank"
    rule1 = Rule(
        field=RuleField.TITLE, operator=RuleOperator.STARTS_WITH, value="Blank"
    )
    group1 = GroupRule(rules=[rule1])

    # Ends with "Book"
    rule2 = Rule(field=RuleField.TITLE, operator=RuleOperator.ENDS_WITH, value="Book")
    group2 = GroupRule(rules=[rule2])

    # Test Starts With
    stmt1 = evaluator.build_matching_book_ids_stmt(group1)
    res1 = session.exec(stmt1).all()
    assert sample_data["book1"] in set(res1)

    # Test Ends With (Multiple books end with "Book")
    stmt2 = evaluator.build_matching_book_ids_stmt(group2)
    res2 = session.exec(stmt2).all()
    ids = set(res2)
    assert sample_data["book1"] in ids
    assert sample_data["book2"] in ids
    assert sample_data["book3"] in ids
    assert sample_data["book9"] in ids


def test_in_operator(session: Session, sample_data: dict[str, int | None]) -> None:
    """Test IN operator."""
    evaluator = BookRuleEvaluator()

    # Title IN ["Horror Book", "Old Bad Book"]
    rule = Rule(
        field=RuleField.TITLE,
        operator=RuleOperator.IN,
        value=["Horror Book", "Old Bad Book"],
    )
    group = GroupRule(rules=[rule])

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()

    ids = set(results)
    assert len(ids) == 2
    assert sample_data["book2"] in ids
    assert sample_data["book9"] in ids


def test_not_empty_related(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test IS_NOT_EMPTY on related field (Has Series)."""
    evaluator = BookRuleEvaluator()

    rule = Rule(field=RuleField.SERIES, operator=RuleOperator.IS_NOT_EMPTY)
    group = GroupRule(rules=[rule])

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()

    # Should match book5 (Has Series)
    ids = set(results)
    assert sample_data["book5"] in ids
    assert sample_data["book4"] not in ids  # No series


def test_not_operators(session: Session, sample_data: dict[str, int | None]) -> None:
    """Test NOT_EQUALS, NOT_CONTAINS, NOT_IN."""
    evaluator = BookRuleEvaluator()

    # Test NOT_EQUALS: Title != "Blank ISBN Book"
    rule1 = Rule(
        field=RuleField.TITLE,
        operator=RuleOperator.NOT_EQUALS,
        value="Blank ISBN Book",
    )
    group1 = GroupRule(rules=[rule1])
    stmt1 = evaluator.build_matching_book_ids_stmt(group1)
    res1 = session.exec(stmt1).all()
    ids1 = set(res1)
    assert sample_data["book1"] not in ids1
    assert sample_data["book2"] in ids1

    # NOT_CONTAINS: Title does not contain "Book"
    # "The Talisman" (book6) is the only one without "Book" in title in sample data
    rule2 = Rule(
        field=RuleField.TITLE, operator=RuleOperator.NOT_CONTAINS, value="Book"
    )
    group2 = GroupRule(rules=[rule2])
    stmt2 = evaluator.build_matching_book_ids_stmt(group2)
    res2 = session.exec(stmt2).all()
    ids2 = set(res2)
    assert sample_data["book6"] in ids2
    assert sample_data["book1"] not in ids2

    # NOT_IN: Title NOT IN ["Horror Book"]
    rule3 = Rule(
        field=RuleField.TITLE, operator=RuleOperator.NOT_IN, value=["Horror Book"]
    )
    group3 = GroupRule(rules=[rule3])
    stmt3 = evaluator.build_matching_book_ids_stmt(group3)
    res3 = session.exec(stmt3).all()
    ids3 = set(res3)
    assert sample_data["book2"] not in ids3
    assert sample_data["book1"] in ids3


def test_deeply_nested_logic(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test deeply nested logic: (Horror OR SciFi) AND ((High Rated AND Recent) OR (Old AND (King OR Straub)))."""
    evaluator = BookRuleEvaluator()

    # Part 1: Genre = Horror OR Genre = SciFi
    g1_horror = Rule(
        field=RuleField.TAG, operator=RuleOperator.CONTAINS, value="Horror"
    )
    g1_scifi = Rule(field=RuleField.TAG, operator=RuleOperator.CONTAINS, value="SciFi")
    group1 = GroupRule(rules=[g1_horror, g1_scifi], join_type=JoinType.OR)

    # Part 2a: High Rated (>4) AND Recent (>2020)
    g2a_rating = Rule(
        field=RuleField.RATING, operator=RuleOperator.GREATER_THAN, value=4
    )
    g2a_date = Rule(
        field=RuleField.PUBDATE,
        operator=RuleOperator.GREATER_THAN,
        value=datetime(2020, 1, 1, tzinfo=UTC).isoformat(),
    )
    group2a = GroupRule(rules=[g2a_rating, g2a_date], join_type=JoinType.AND)

    # Part 2b: Old (<1990) AND (Author=King OR Author=Straub)
    g2b_date = Rule(
        field=RuleField.PUBDATE,
        operator=RuleOperator.LESS_THAN,
        value=datetime(1990, 1, 1, tzinfo=UTC).isoformat(),
    )
    g2b_king = Rule(
        field=RuleField.AUTHOR, operator=RuleOperator.CONTAINS, value="King"
    )
    g2b_straub = Rule(
        field=RuleField.AUTHOR, operator=RuleOperator.CONTAINS, value="Straub"
    )
    group2b_authors = GroupRule(rules=[g2b_king, g2b_straub], join_type=JoinType.OR)
    group2b = GroupRule(rules=[g2b_date, group2b_authors], join_type=JoinType.AND)

    # Part 2: 2a OR 2b
    group2 = GroupRule(rules=[group2a, group2b], join_type=JoinType.OR)

    # Root: Group 1 AND Group 2
    root = GroupRule(rules=[group1, group2], join_type=JoinType.AND)

    ids_stmt = evaluator.build_matching_book_ids_stmt(root)
    results = session.exec(ids_stmt).all()
    ids = set(results)

    # Expect:
    # Book 10: SciFi, 5, 2025 -> Matches G1(SciFi) AND G2a(High/Recent). -> MATCH
    # Book 11: Horror, 2, 1980, King -> Matches G1(Horror) AND G2b(Old/King). -> MATCH
    # Book 13: Horror, 2, 1980, Orwell -> Matches G1(Horror) but FAILS G2 (Not High/Recent, Not King/Straub). -> NO MATCH
    # Book 12: Romance -> Fails G1. -> NO MATCH
    # Book 2: Horror, No Rating/Date -> Fails G2. -> NO MATCH

    assert sample_data["book10"] in ids
    assert sample_data["book11"] in ids
    assert sample_data["book13"] not in ids
    assert sample_data["book12"] not in ids
    assert sample_data["book2"] not in ids


def test_mixed_direct_and_related_or(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test OR logic mixing direct fields and related fields."""
    evaluator = BookRuleEvaluator()

    # Title="UniqueTitle" OR Author="SpecificAuthor"
    rule1 = Rule(
        field=RuleField.TITLE, operator=RuleOperator.EQUALS, value="UniqueTitle"
    )
    rule2 = Rule(
        field=RuleField.AUTHOR, operator=RuleOperator.EQUALS, value="SpecificAuthor"
    )
    group = GroupRule(rules=[rule1, rule2], join_type=JoinType.OR)

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()
    ids = set(results)

    # Book 14: Title="UniqueTitle" -> Match
    # Book 15: Author="SpecificAuthor" -> Match
    # Book 1: Title="Blank ISBN Book" -> No Match
    assert sample_data["book14"] in ids
    assert sample_data["book15"] in ids
    assert sample_data["book1"] not in ids


def test_in_operator_related_field(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test IN operator on a related field (Author)."""
    evaluator = BookRuleEvaluator()

    # Author IN ["Stephen King", "Peter Straub"]
    rule = Rule(
        field=RuleField.AUTHOR,
        operator=RuleOperator.IN,
        value=["Stephen King", "Peter Straub"],
    )
    group = GroupRule(rules=[rule])

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()
    ids = set(results)

    # Book 6: King & Straub -> Match
    # Book 11: King -> Match
    # Book 13: Orwell -> No Match
    assert sample_data["book6"] in ids
    assert sample_data["book11"] in ids
    assert sample_data["book13"] not in ids


def test_empty_group_behavior(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test that an empty group returns all books (True)."""
    evaluator = BookRuleEvaluator()
    group = GroupRule(rules=[])

    ids_stmt = evaluator.build_matching_book_ids_stmt(group)
    results = session.exec(ids_stmt).all()

    # Should return all books
    assert len(results) == len(sample_data)


def test_boundary_operators(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test GREATER_THAN_OR_EQUALS and LESS_THAN_OR_EQUALS."""
    evaluator = BookRuleEvaluator()

    # Rating >= 5 (Should match book3 with rating 5)
    rule1 = Rule(
        field=RuleField.RATING, operator=RuleOperator.GREATER_THAN_OR_EQUALS, value=5
    )
    group1 = GroupRule(rules=[rule1])
    stmt1 = evaluator.build_matching_book_ids_stmt(group1)
    res1 = session.exec(stmt1).all()
    ids1 = set(res1)
    assert sample_data["book3"] in ids1

    # Rating <= 1 (Should match book9 with rating 1)
    rule2 = Rule(
        field=RuleField.RATING, operator=RuleOperator.LESS_THAN_OR_EQUALS, value=1
    )
    group2 = GroupRule(rules=[rule2])
    stmt2 = evaluator.build_matching_book_ids_stmt(group2)
    res2 = session.exec(stmt2).all()
    ids2 = set(res2)
    assert sample_data["book9"] in ids2
