# Flask JWT Persistency
This extension was developed to add additional features to JWT like revoke a single token or all tokens issued to a specific user. These features are implemented by persisting the tokens in a database, so JWT looses its stateless property.

Installing
----------

Install and update using pip:

```bash
$ pip install flask-jwt-persistency
```

Full working example (also available at examples folder)
----------------

```python
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jti, get_jwt, get_jwt_identity

from flask_jwt_persistency import JWTPersistency

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
app.config["JWTP_DATABASE_URL"] = "sqlite:///jwtptokens.db"  # DB to store the tokens
db = SQLAlchemy(app)
jwt = JWTManager(app)
jwtp = JWTPersistency(app, jwt, db)


@app.route("/auth/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    if username != "test" or password != "test":
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=username)
    jti = get_jti(encoded_token=access_token)

    # Persist the jti in the database
    jwtp.new_token(jti, username)

    return jsonify(access_token=access_token)


# Access a protected route
@app.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    return jsonify({"msg": "You got access to the protected route"})


# Revoke token used in the request
@app.route("/auth/logout", methods=["DELETE"])
@jwt_required()
def logout():
    """Revoke access token"""
    jti = get_jwt()['jti']
    jwtp.revoke_token(jti)


# Revoke all tokens that have been issued to the user that is making the request
@app.route("/auth/logout-from-all-devices", methods=["DELETE"])
@jwt_required()
def logout_from_all_devices():
    """Revoke all tokens"""
    username = get_jwt_identity()
    jwtp.revoke_all_tokens(username)


if __name__ == "__main__":
    app.run(debug=True)

```
