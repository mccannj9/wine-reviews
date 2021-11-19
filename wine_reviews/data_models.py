from sqlalchemy.orm import declarative_base

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date
)

wine_reviews_base = declarative_base()

class WineReviews(wine_reviews_base):
    __tablename__ = "wine_reviews"

    id = Column(Integer, primary_key=True)
    alcohol = Column(Float)
    appellation = Column(String)
    author_name = Column(String)
    bottle_size = Column(Float)
    category = Column(String)
    date_published = Column(Date)
    designation = Column(String)
    link = Column(String)
    price = Column(Float)
    price_per_milliliter = Column(Float)
    rating = Column(Integer)
    review_body = Column(String)
    sha512_hash = Column(String)
    title = Column(String)
    variety = Column(String)
    vintage = Column(Integer)
    winery = Column(String)
