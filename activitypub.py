import os
import sqlite3
import subprocess

import requests
from flask import Flask, jsonify, request
from requests_http_signature import HTTPSignatureAuth, algorithms

if not os.path.exists("keys"):
    os.makedirs("keys")

if not os.path.exists("keys/public.pem"):
    subprocess.run(["openssl", "genrsa", "-out", "keys/private.pem", "2048"])
    subprocess.run(
        [
            "openssl",
            "rsa",
            "-in",
            "keys/private.pem",
            "-outform",
            "PEM",
            "-pubout",
            "-out",
            "keys/public.pem",
        ]
    )

ACTOR = {
    "@context": [
        "https://www.w3.org/ns/activitystreams",
        "https://w3id.org/security/v1",
    ],
    "id": "https://ap.jamesg.blog/actor",
    "type": "Person",
    "preferredUsername": "apjamesg",
    "inbox": "https://ap.jamesg.blog/inbox",
    "publicKey": {
        "id": "https://ap.jamesg.blog/actor#main-key",
        "owner": "https://ap.jamesg.blog/actor",
        "publicKeyPem": open("keys/public.pem", "r").read(),
    },
}

# create DB with one column: items
# items has a single column: activity_streams
# activity_streams is a JSON blob

db = sqlite3.connect("ap.db")

db.execute("CREATE TABLE IF NOT EXISTS items (activity_streams TEXT)")

db.commit()
db.close()

# ref: https://www.w3.org/TR/activitystreams-vocabulary/
SUPPORTED_ACTIONS = ["Create", "Follow"]


def make_http_signature_auth_request():
    return HTTPSignatureAuth(
        key=open("keys/private.pem", "r").read(),
        key_id="https://ap.jamesg.blog/actor#main-key",
        signature_alg=algorithms.RSA_SHA256,
    )


def get_followers():
    db = sqlite3.connect("ap.db")

    items = db.execute(
        "SELECT json_extract(activity_streams, '$.actor') FROM items WHERE json_extract(activity_streams, '$.type') = 'Follow'"
    ).fetchall()

    db.close()

    return [item[0] for item in items]


def create_post(post):
    followers = get_followers()

    # finger to do

    for follower in followers:
        # finger to get inbox
        inbox_url = requests.get(follower + "/.well-known/webfinger").json()["links"][
            0
        ]["href"]

        # send w/ http signature
        response = requests.post(
            inbox_url, json=post, auth=make_http_signature_auth_request()
        )
        print(response)


def follow_actor(post):
    pass


ACTION_REGISTRY = {
    "Create": lambda post: create_post(post),
    "Follow": lambda post: follow_actor(post),
}

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({})


@app.route("/actor")
def actor():
    return jsonify(ACTOR)


@app.route("/.well-known/webfinger")
def webfinger():
    return jsonify(
        {
            "subject": "acct:apjamesg@ap.jamesg.blog",
            "links": [
                {
                    "rel": "self",
                    "type": "application/activity+json",
                    "href": "https://ap.jamesg.blog/actor",
                }
            ],
        }
    )


@app.route("/inbox", methods=["GET", "POST"])
def inbox():
    if request.method == "POST":
        action = request.json["type"]

        if action not in SUPPORTED_ACTIONS:
            return jsonify({"error": "Action not supported."}), 400

        post = request.json

        db = sqlite3.connect("ap.db")

        db.execute("INSERT INTO items (activity_streams) VALUES (?)", (post,))
        db.commit()

        print(f"Record created with data {post}")

        ACTION_REGISTRY[action](post)

        return jsonify({}), 200

    db = sqlite3.connect("ap.db")

    items = db.execute("SELECT activity_streams FROM items").fetchall()

    db.close()

    return jsonify([item[0] for item in items])


@app.route("/following")
def following():
    # get records with Follow type
    # return list of actors

    db = sqlite3.connect("ap.db")

    items = db.execute(
        "SELECT json_extract(activity_streams, '$.actor') FROM items WHERE json_extract(activity_streams, '$.type') = 'Follow'"
    ).fetchall()

    db.close()

    return jsonify([item[0] for item in items])


if __name__ == "__main__":
    app.run(debug=True)
