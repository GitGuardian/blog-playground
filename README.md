### Requirements

- pipenv
- docker

### Usage

1. Install virtualenv

```
pipenv install -d
pipenv shell
```

2. Start PG container

```
docker compose up -d
```

3. Apply migrations

```
./manage.py migrate
```

4. Generate data

```
./manage.py generate_data
```

5. Open Django shell

```
./manage.py shell_plus
```

6. Open a notebook

```
./manage.py shell_plus --notebook
```
