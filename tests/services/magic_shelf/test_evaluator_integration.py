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
    }


def test_blank_isbn(session: Session, sample_data: dict[str, int | None]) -> None:
    evaluator = BookRuleEvaluator()
    rule = Rule(field=RuleField.ISBN, operator=RuleOperator.IS_EMPTY)
    group = GroupRule(rules=[rule])

    filter_expr = evaluator.build_filter(group)
    stmt = select(Book).where(filter_expr)
    results = session.exec(stmt).all()

    assert len(results) == 1
    assert results[0].id == sample_data["book1"]


def test_genre_horror(session: Session, sample_data: dict[str, int | None]) -> None:
    evaluator = BookRuleEvaluator()
    rule = Rule(field=RuleField.TAG, operator=RuleOperator.CONTAINS, value="Horror")
    group = GroupRule(rules=[rule])

    filter_expr = evaluator.build_filter(group)
    stmt = select(Book).where(filter_expr)
    results = session.exec(stmt).all()

    assert len(results) == 1
    assert results[0].id == sample_data["book2"]


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

    filter_expr = evaluator.build_filter(group)
    stmt = select(Book).where(filter_expr)
    results = session.exec(stmt).all()

    assert len(results) == 1
    assert results[0].id == sample_data["book3"]


def test_title_hash_no_series(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    evaluator = BookRuleEvaluator()

    # Title contains "#"
    rule_title = Rule(field=RuleField.TITLE, operator=RuleOperator.CONTAINS, value="#")

    # Series is empty (Intended: No Series)
    rule_series = Rule(field=RuleField.SERIES, operator=RuleOperator.IS_EMPTY)

    group = GroupRule(rules=[rule_title, rule_series], join_type=JoinType.AND)

    filter_expr = evaluator.build_filter(group)
    stmt = select(Book).where(filter_expr)
    results = session.exec(stmt).all()

    # Should match book4 (Has #, No Series)
    # Should NOT match book5 (Has #, Has Series)
    assert len(results) == 1
    assert results[0].id == sample_data["book4"]


def test_multiple_authors_or_logic(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test OR logic with multiple authors."""
    evaluator = BookRuleEvaluator()

    # Author contains King OR Author contains Straub
    rule1 = Rule(field=RuleField.AUTHOR, operator=RuleOperator.CONTAINS, value="King")
    rule2 = Rule(field=RuleField.AUTHOR, operator=RuleOperator.CONTAINS, value="Straub")

    group = GroupRule(rules=[rule1, rule2], join_type=JoinType.OR)

    filter_expr = evaluator.build_filter(group)
    stmt = select(Book).where(filter_expr)
    results = session.exec(stmt).all()

    # Should match book6 (The Talisman)
    assert len(results) >= 1
    assert any(b.id == sample_data["book6"] for b in results)


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

    filter_expr = evaluator.build_filter(group)
    stmt = select(Book).where(filter_expr)
    results = session.exec(stmt).all()

    assert len(results) == 1
    assert results[0].id == sample_data["book7"]


def test_identifier_lookup(
    session: Session, sample_data: dict[str, int | None]
) -> None:
    """Test filtering by Identifier value."""
    evaluator = BookRuleEvaluator()

    rule = Rule(
        field=RuleField.IDENTIFIER, operator=RuleOperator.CONTAINS, value="10.1000"
    )
    group = GroupRule(rules=[rule])

    filter_expr = evaluator.build_filter(group)
    stmt = select(Book).where(filter_expr)
    results = session.exec(stmt).all()

    assert len(results) == 1
    assert results[0].id == sample_data["book8"]


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

    filter_expr = evaluator.build_filter(root)
    stmt = select(Book).where(filter_expr)
    results = session.exec(stmt).all()

    # Should match book9 (Old Bad) and book3 (Good Recent)
    ids = {b.id for b in results}
    assert sample_data["book9"] in ids
    assert sample_data["book3"] in ids
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
    expr1 = evaluator.build_filter(group1)
    res1 = session.exec(select(Book).where(expr1)).all()
    assert any(b.id == sample_data["book1"] for b in res1)

    # Test Ends With (Multiple books end with "Book")
    expr2 = evaluator.build_filter(group2)
    res2 = session.exec(select(Book).where(expr2)).all()
    ids = {b.id for b in res2}
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

    filter_expr = evaluator.build_filter(group)
    stmt = select(Book).where(filter_expr)
    results = session.exec(stmt).all()

    ids = {b.id for b in results}
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

    filter_expr = evaluator.build_filter(group)
    stmt = select(Book).where(filter_expr)
    results = session.exec(stmt).all()

    # Should match book5 (Has Series)
    ids = {b.id for b in results}
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
    expr1 = evaluator.build_filter(group1)
    res1 = session.exec(select(Book).where(expr1)).all()
    ids1 = {b.id for b in res1}
    assert sample_data["book1"] not in ids1
    assert sample_data["book2"] in ids1

    # NOT_CONTAINS: Title does not contain "Book"
    # "The Talisman" (book6) is the only one without "Book" in title in sample data
    rule2 = Rule(
        field=RuleField.TITLE, operator=RuleOperator.NOT_CONTAINS, value="Book"
    )
    group2 = GroupRule(rules=[rule2])
    expr2 = evaluator.build_filter(group2)
    res2 = session.exec(select(Book).where(expr2)).all()
    # book6 is "The Talisman"
    assert any(b.id == sample_data["book6"] for b in res2)
    # book1 is "Blank ISBN Book"
    assert not any(b.id == sample_data["book1"] for b in res2)

    # NOT_IN: Title NOT IN ["Horror Book"]
    rule3 = Rule(
        field=RuleField.TITLE, operator=RuleOperator.NOT_IN, value=["Horror Book"]
    )
    group3 = GroupRule(rules=[rule3])
    expr3 = evaluator.build_filter(group3)
    res3 = session.exec(select(Book).where(expr3)).all()
    ids3 = {b.id for b in res3}
    assert sample_data["book2"] not in ids3
    assert sample_data["book1"] in ids3


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
    expr1 = evaluator.build_filter(group1)
    res1 = session.exec(select(Book).where(expr1)).all()
    ids1 = {b.id for b in res1}
    assert sample_data["book3"] in ids1

    # Rating <= 1 (Should match book9 with rating 1)
    rule2 = Rule(
        field=RuleField.RATING, operator=RuleOperator.LESS_THAN_OR_EQUALS, value=1
    )
    group2 = GroupRule(rules=[rule2])
    expr2 = evaluator.build_filter(group2)
    res2 = session.exec(select(Book).where(expr2)).all()
    ids2 = {b.id for b in res2}
    assert sample_data["book9"] in ids2
