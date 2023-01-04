import csv
import os
from reviews.models import CustomUser, Genre, Category, Title, Review, Comment, GenreTitle


def run():
    """Заполняем данные моделей информацией из CSV таблиц."""
    with open('./static/data/users.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            p = CustomUser(
                id=row['id'],
                username=row['username'],
                email=row['email'],
                role=row['role'],
                bio=row['bio'],
                first_name=row['first_name'],
                last_name=row['last_name']
            )
            p.save()
        print("=====USERS ADDED====")

    with open('./static/data/category.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            p = Category(
                name=row['name'],
                slug=row['slug']
            )
            p.save()
        print("=====CATEGORY ADDED====")

    with open('./static/data/genre.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            p = Genre(
                name=row['name'],
                slug=row['slug']
            )
            p.save()
        print("=====GENRE ADDED====")


    with open('./static/data/titles.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            category = Category.objects.get(id=row['category'])

            p = Title(
                id=row['id'],
                name=row['name'],
                year=row['year'],
                category=category
            )
            p.save()
        print("=====TITLE ADDED====")


    with open('./static/data/genre_title.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            genre = Genre.objects.get(id=row['genre_id'])
            title = Title.objects.get(id=row['title_id'])
            p = GenreTitle(
                genre=genre,
                title=title
            )
            p.save()
        print("=====GENRE-TITLE ADDED====")


    with open('./static/data/review.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            title = Title.objects.get(id=row['title_id'])
            author = CustomUser.objects.get(id=row['author'])

            p = Review(
                id=row['id'],
                text=row['text'],
                title=title,
                author=author,
                score=row['score'],
                pub_date=row['pub_date']
            )
            p.save()
        print("=====REVIEWS ADDED====")


    with open('./static/data/comments.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            review = Review.objects.get(id=row['review_id'])
            author = CustomUser.objects.get(id=row['author'])

            p = Comment(
                id=row['id'],
                text=row['text'],
                review=review,
                author=author,
                pub_date=row['pub_date']
            )
            p.save()
        print("=====COMMENTS ADDED====")
