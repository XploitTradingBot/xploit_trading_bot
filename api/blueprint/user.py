#!/usr/bin/python3

import bcrypt
from model import storage
from model.user import User
from model.usersession import UserSession
from api.blueprint import app_views, auth
from flask import request, jsonify

@app_views.route('/users', methods=['POST'], strict_slashes=False)
def create_user():
    """This creates a user instance"""
    if not request.json:
        return jsonify("Not a valid json"), 400
    data = request.get_json()
    if "password" in data:
        val = data['password']
        val = val.encode()
        val = bcrypt.hashpw(val, bcrypt.gensalt())
        data['password'] = val.decode('utf-8')
    user = User(**data)
    user.save()
    session_dct = {"user_id": user.id}
    session = UserSession(**session_dct)
    session.save()
    ret = {"name": user.name, "id": user.id, "token": session.id}
    return jsonify(ret), 201

@app_views.route('/users/<user_id>', methods=['PUT'], strict_slashes=False)
@auth.login_required
def update_user(user_id):
    if not request.json:
        return jsonify("Not a valid json"), 400
    data = request.get_json()
    user = storage.get(User, user_id)
    if not user:
        return jsonify("User not found", 404)
    
    user.update(**data)
    user.save()
    return jsonify(user.to_dict())

@app_views.route('/user/login', methods=['POST'], strict_slashes=False)
def user_login():
    if not request.json:
        return jsonify("Not a valid json"), 400
    
    data = request.get_json()
    if "email" not in data:
        return jsonify("Must contain an Email"), 400
    if "password" not in data:
        return jsonify("Must contain a password"), 400
    password = data['password']
    for key, user in storage.all("User").items():
        if user.email.lower() == data['email'].lower():
            password = password.encode('utf-8')
            if bcrypt.checkpw(password, user.password.encode()):
                session_dct = {"user_id": user.id}
                session = UserSession(**session_dct)
                session.save()
                ret = {"name": user.name, "id": user.id, "token": session.id}
                return jsonify(ret), 200
            else:
                return jsonify("Incorrect password"), 400
        else:
            continue
    return jsonify("No user with email found"), 400
