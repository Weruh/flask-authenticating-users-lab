#!/usr/bin/env python3

from flask import Flask, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User, ArticlesSchema, UserSchema

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

class ClearSession(Resource):

    def get(self):
        session.pop('page_views', None)
        session.pop('user_id', None)

        return {}, 204

    delete = get

class Login(Resource):

    def post(self):
        data = request.get_json(silent=True) or {}
        username = data.get('username')
        user = User.query.filter_by(username=username).first() if username else None

        if user is None:
            return {'error': 'Invalid username'}, 401

        # Flask stores this identifier in its signed session cookie.
        session['user_id'] = user.id
        return UserSchema().dump(user), 200

class Logout(Resource):

    def delete(self):
        session.pop('user_id', None)
        return '', 204

class CheckSession(Resource):

    def get(self):
        user_id = session.get('user_id')
        user = db.session.get(User, user_id) if user_id is not None else None

        if user is None:
            # Discard an identifier whose user has since been deleted.
            session.pop('user_id', None)
            return {}, 401

        return UserSchema().dump(user), 200

class IndexArticle(Resource):
    
    def get(self):
        articles = [ArticlesSchema().dump(article) for article in Article.query.all()]
        return articles, 200

class ShowArticle(Resource):

    def get(self, id):
        session['page_views'] = 0 if not session.get('page_views') else session.get('page_views')
        session['page_views'] += 1

        if session['page_views'] <= 3:

            article = Article.query.filter(Article.id == id).first()
            if article is None:
                return {'error': 'Article not found'}, 404
            article_json = ArticlesSchema().dump(article)

            return article_json, 200

        return {'error': 'Maximum pageview limit reached'}, 401

api.add_resource(ClearSession, '/clear')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
