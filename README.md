# ActivityPub

A limited implementation of ActivityPub.

> [!NOTE]
> I am building this software to learn about ActivityPub, without aspiration of building a complete implementation of the standard.

## Getting Started

First, clone this repository and install the required dependencies:

```bash
git clone https://github.com/capjamesg/activitypub
cd activitypub
pip install -r requirements.txt
```

Then, run the ActivityPub server:

```bash
python app.py
```

The ActivityPub server will be available at `http://localhost:5000`.

When you first run the server, a database is created and a keypair is saved for use with the server.

## Supported Methods

Supported methods appear below with a checked checkbox. Methods I want to support appear as an empty checkbox.

- [ ] Create
- [ ] Follow

## License

This project is licensed under an [MIT license](LICENSE).
