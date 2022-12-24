A simple SQL CLI to query on your monday.com boards

# Installation
```
pip install -r requirements.txt
```

# Run
```python
python cli.py <API_TOKEN>
```
*You can generate API Token by following the [Monday API's authentication guide](https://developer.monday.com/api-reference/docs/authentication#admin-tab).*

# Usage
To query all available boards, you can select from the table `boards``
```
sql> SELECT * FROM boards;
+------------+---------------------------------------------------+
|     id     |                        name                       |
+------------+---------------------------------------------------+
|     123    |       Welcome to your monday dev account 😍       |
|     456    | Subitems of Welcome to your monday dev account 😍 |
+------------+---------------------------------------------------+
```
Then to select from specific boards you may select from `b_<board_id>`. For example:
```python
sql> SELECT name FROM b_456;
+----------------------------+
|            name            |
+----------------------------+
|        API session         |
|        Build a view        |
|    Build an integration    |
|       Authentication       |
| Build a Workspace template |
+----------------------------+
```

You're free to use JOINS, GROUP BY, ORDER BY, LIMIT, etc as well.
