__version__ = "0.0.3"
EXTENSION_NAME = "flask-jwt-persistency"


class JWTPersistency(object):
    """Wrapper class that integrates JWT Persistency Flask application.

    To use it, instantiate with an application:

        from flask import Flask
        from flask_jwt_extended import JWTManager
        from flask_sqlalchemy import SQLAlchemy

        app = Flask(__name__)
        jwt = JWTManager(app)
        db = SQLAlchemy(app)
        jwtp = JWTPersistency(app, jwt, db)

    :param app: The Flask application object.
    :param jwt: A JWTManager object from flask_jwt_extended lib.
    :param db: A SQLAlchemy object from flask_sqlalchemy lib.

    For a full working example please refer to examples folder.
    """

    def __init__(self, app=None, jwt=None, db=None):
        if app is not None and jwt is not None and db is not None:
            self.init_app(app, jwt, db)

    def init_app(self, app, jwt, db):
        """Initializes the application with the extension.

        :param Flask app: The Flask application object.
        """
        if not app.config["SQLALCHEMY_BINDS"]:
            app.config["SQLALCHEMY_BINDS"] = {}
        app.config["SQLALCHEMY_BINDS"]["jwtptokens"] = dict.get(
            app.config, "JWTP_DATABASE_URL", "sqlite:///jwtptokens.db")
        app.extensions = getattr(app, "extensions", {})
        app.extensions[EXTENSION_NAME] = self

        class Token(db.Model):
            __bind_key__ = 'jwtptokens'

            id = db.Column(db.Integer, primary_key=True)
            jti = db.Column(db.String(120), index=True, unique=True)
            identity = db.Column(db.String(120), index=True)
            revoked = db.Column(db.Boolean)

            @staticmethod
            def is_jti_blacklisted(jti):
                token = Token.query.filter_by(jti=jti).first()
                if token is None or token.revoked is True:
                    return True
                return False

            @staticmethod
            def set_jti_revoked_state(jti, state):
                token = Token.query.filter_by(jti=jti).first()
                if token:
                    token.revoked = state

        db.create_all(bind='jwtptokens')
        self.db = db
        self.Token = Token

        @jwt.token_in_blocklist_loader
        def check_if_token_in_blocklist(jwt_header, jwt_payload):
            jti = jwt_payload['jti']
            return Token.is_jti_blacklisted(jti)

    def new_token(self, jti, identity):
        """
        Persist the token generated for a certain '<identity>' in the database.
        Usage: 

        access_token = create_access_token(identity="username")
        jti = get_jti(encoded_token=access_token)
        jwtp.new_token(jti=jti, identity="username")
        """
        new_token = self.Token(jti=jti, identity=identity, revoked=False)
        self.db.session.add(new_token)
        self.db.session.commit()

    def revoke_token(self, jti):
        """
        Revoke the token identified by an unique identifier '<jti>' if exists in the database.
        Usage: 

        jti = get_jwt()['jti']
        jwtp.revoke_token(jti)
        """
        self.Token.set_jti_revoked_state(jti, True)
        self.db.session.commit()

    def revoke_all_tokens(self, identity):
        """
        Revoke all tokens generated for a certain '<identity>' in the database.
        Usage: 

        username = get_jwt_identity()
        jwtp.revoke_all_tokens(username)
        """
        tokens = self.Token.query.filter_by(identity=identity).all()
        for token in tokens:
            token.revoked = True
        self.db.session.commit()
